from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test,login_required
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger  # Import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test, login_required
from django.views.decorators.cache import never_cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Sum, Count
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
import csv
from datetime import datetime, timedelta
from orders.models import Order, OrderItem
from productsapp.models import Product, ProductVariant
from couponsapp.models import Coupon, CouponUsage
from django.db.models import Sum, Count, F, DecimalField, Case, When, Value
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from openpyxl import Workbook
from datetime import datetime, timedelta
from orders.models import Order, OrderItem
from decimal import Decimal



def is_admin(user):
    return user.is_staff

@never_cache
def admin_login(request):
    form_data = {'username': ''}  # Initialize form data

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        form_data['username'] = username  # Retain username in form data

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid credentials or not an admin user.')

    return render(request, 'admin/admin_login.html', {'form_data': form_data})


@user_passes_test(is_admin)
@login_required(login_url='admin_login')
def admin_dashboard(request):
    # Total Users
    total_users = User.objects.filter(is_superuser=False).count()

    # Total Sales (only from delivered, return_requested, and return_denied orders)
    total_sales = OrderItem.objects.filter(status__in=['delivered', 'return_requested', 'return_denied']).aggregate(
        total_sales=Sum(
            Case(
                When(order__coupon__isnull=False, then=F('price') * F('quantity') * (1 - F('order__coupon__discount_percentage') / Decimal('100.00'))),
                default=F('price') * F('quantity'),
                output_field=DecimalField()
            )
        )
    )['total_sales'] or Decimal('0.00')

    # Total Orders
    total_orders = Order.objects.count()

    # Total Discount (only from delivered, return_requested, and return_denied orders)
    total_discount = OrderItem.objects.filter(status__in=['delivered', 'return_requested', 'return_denied']).aggregate(
        total_discount=Sum(
            Case(
                When(order__coupon__isnull=False, then=F('price') * F('quantity') * F('order__coupon__discount_percentage') / Decimal('100.00')),
                default=Value(Decimal('0.00')),
                output_field=DecimalField()
            )
        )
    )['total_discount'] or Decimal('0.00')

    # Top Selling Products (only from delivered, return_requested, and return_denied orders)
    top_selling_products = Product.objects.annotate(
        total_sold=Sum(
            Case(
                When(variants__orderitem__status__in=['delivered', 'return_requested', 'return_denied'], then=F('variants__orderitem__quantity')),
                default=Value(0),
                output_field=DecimalField()
            )
        )
    ).order_by('-total_sold')[:5]

    # Low Stock Products
    low_stock_products = ProductVariant.objects.filter(stock__lt=10)

    context = {
        'total_users': total_users,
        'total_sales': total_sales,
        'total_orders': total_orders,
        'total_discount': total_discount,
        'top_selling_products': top_selling_products,
        'low_stock_products': low_stock_products,
    }

    return render(request, 'admin/dashboard.html', context)



@user_passes_test(is_admin)
@login_required(login_url='admin_login')
def generate_sales_report(request):
    if request.method == 'POST':
        date_range = request.POST.get('date_range')
        custom_start = request.POST.get('custom_start')
        custom_end = request.POST.get('custom_end')

        # Determine the date range
        if date_range == 'custom':
            start_date = datetime.strptime(custom_start, '%Y-%m-%d')
            end_date = datetime.strptime(custom_end, '%Y-%m-%d')
        else:
            end_date = datetime.now()
            if date_range == '1_day':
                start_date = end_date - timedelta(days=1)
            elif date_range == '1_week':
                start_date = end_date - timedelta(weeks=1)
            elif date_range == '1_month':
                start_date = end_date - timedelta(days=30)

        # Fetch orders within the date range that have at least one delivered item or at least one return_request or at least one return denied
        orders = Order.objects.filter(
            created_at__range=[start_date, end_date],
            items__status__in=['delivered', 'return_requested', 'return_denied']
        ).distinct()

        # Pre-calculate totals and discounts
        order_data = []
        total_discount_amount = Decimal('0.00')
        total_sales = Decimal('0.00')

        for order in orders:
            # Get OrderItems with specific statuses (like the admin dashboard)
            order_items = OrderItem.objects.filter(
                order=order,
                status__in=['delivered', 'return_requested', 'return_denied']
            )

            # Calculate original total from OrderItems (before discount)
            original_total = sum(
                item.product.offer * item.quantity if item.product.offer else item.product.price * item.quantity
                for item in order_items
            )

            # Calculate discount based on original_total (not order.total_price)
            discounted_amount = Decimal('0.00')
            if order.coupon:
                discounted_amount = original_total * (order.coupon.discount_percentage / Decimal('100.00'))

            # Adjust the total price based on returned items
            # Exclude returned items from the total price
            adjusted_total_price = sum(
                item.product.offer * item.quantity if item.product.offer else item.product.price * item.quantity
                for item in order_items.exclude(status='returned')
            )

            # Apply coupon discount to the adjusted total price
            if order.coupon:
                adjusted_total_price -= discounted_amount

            # Accumulate totals
            total_discount_amount += discounted_amount
            total_sales += adjusted_total_price  # Use adjusted total price

            order_data.append({
                'id': order.id,
                'user': order.user,
                'total_before_coupon': original_total,  # Total before applying coupon
                'total_price': adjusted_total_price,  # Final total after applying coupon
                'discounted_amount': discounted_amount,
                'created_at': order.created_at
            })

        # Calculate total number of orders
        total_orders = len(order_data)

        context = {
            'order_data': order_data,
            'total_sales': total_sales,
            'total_discount_amount': total_discount_amount,
            'total_orders': total_orders,  # Add total number of orders
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
        }

        report_format = request.POST.get('report_format')
        if report_format == 'pdf':
            # Generate PDF
            template = get_template('admin/sales_report_pdf.html')
            html = template.render(context)
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="sales_report_{start_date}_{end_date}.pdf"'
            pisa_status = pisa.CreatePDF(html, dest=response)
            if pisa_status.err:
                return HttpResponse('Error generating PDF: <pre>' + html + '</pre>')
            return response

        elif report_format == 'excel':
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename="sales_report_{start_date}_{end_date}.xlsx"'

            workbook = Workbook()
            worksheet = workbook.active
            worksheet.title = 'Sales Report'

            # Add summary section
            worksheet.append(['Date Range', f'{start_date.strftime("%Y-%m-%d")} to {end_date.strftime("%Y-%m-%d")}'])
            worksheet.append(['Total Orders', total_orders])
            worksheet.append(['Total Sales', total_sales])
            worksheet.append(['Total Discount', total_discount_amount])
            worksheet.append([])  # Add an empty row for spacing

            headers = ['Order ID', 'User', 'Total Before Coupon', 'Total Price', 'Discounted Amount', 'Date']
            worksheet.append(headers)

            for order in order_data:
                row = [
                    order['id'],
                    order['user'].username,
                    order['total_before_coupon'],
                    order['total_price'],
                    order['discounted_amount'],
                    order['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
                ]
                worksheet.append(row)

            workbook.save(response)
            return response

    return render(request, 'admin/generate_sales_report.html')


@user_passes_test(is_admin)
def user_manage(request):
    users = User.objects.filter(is_superuser=False).order_by('-date_joined')

    # Pagination
    page = request.GET.get('page', 1)  # Get the page number from the URL parameters
    paginator = Paginator(users, 10)  # Show 10 products per page

    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)


    return render(request,'admin/users.html',{'users':users})

@user_passes_test(is_admin)
def block_user(request,user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = False
    user.save()
    messages.success(request, f'{user.username} has been blocked.')
    return redirect('users')

@user_passes_test(is_admin)
def unblock_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = True
    user.save()
    messages.success(request, f'{user.username} has been unblocked.')
    return redirect('users')

@login_required(login_url='admin_login')
def admin_logout(request):
    logout(request)
    return redirect('admin_login')