from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test,login_required
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Sum, Count, F, DecimalField, Case, When, Value
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
import csv
from datetime import datetime, timedelta
from productsapp.models import Product, ProductVariant
from couponsapp.models import Coupon, CouponUsage
from openpyxl import Workbook
from orders.models import Order, OrderItem
from decimal import Decimal
from weasyprint import HTML 
from openpyxl.styles import Font, Border, Side, PatternFill, Alignment
from openpyxl.utils import get_column_letter



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

        # Fetch orders within the date range
        orders = Order.objects.filter(
            created_at__range=[start_date, end_date],
            items__status__in=['delivered', 'return_requested', 'return_denied']
        ).distinct()

        # Pre-calculate totals and discounts
        order_data = []
        total_discount_amount = Decimal('0.00')
        total_sales = Decimal('0.00')

        for order in orders:
            order_items = OrderItem.objects.filter(
                order=order,
                status__in=['delivered', 'return_requested', 'return_denied']
            )

            original_total = sum(
                item.product.offer * item.quantity if item.product.offer else item.product.price * item.quantity
                for item in order_items
            )

            discounted_amount = Decimal('0.00')
            if order.coupon:
                discounted_amount = original_total * (order.coupon.discount_percentage / Decimal('100.00'))

            adjusted_total_price = sum(
                item.product.offer * item.quantity if item.product.offer else item.product.price * item.quantity
                for item in order_items.exclude(status='returned')
            )

            if order.coupon:
                adjusted_total_price -= discounted_amount

            total_discount_amount += discounted_amount
            total_sales += adjusted_total_price

            order_data.append({
                'id': order.id,
                'user': order.user,
                'total_before_coupon': original_total,
                'total_price': adjusted_total_price,
                'discounted_amount': discounted_amount,
                'created_at': order.created_at
            })

        total_orders = len(order_data)

        # Add the current timestamp for the report generation time
        report_generated_at = datetime.now()

        context = {
            'order_data': order_data,
            'total_sales': total_sales,
            'total_discount_amount': total_discount_amount,
            'total_orders': total_orders,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'report_generated_at': report_generated_at.strftime('%Y-%m-%d %H:%M:%S'),  # Add timestamp
        }

        report_format = request.POST.get('report_format')
        if report_format == 'pdf':
            # Generate PDF using WeasyPrint
            template = get_template('admin/sales_report_pdf.html')
            html = template.render(context)
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="sales_report_{start_date}_{end_date}.pdf"'
            HTML(string=html).write_pdf(response)
            return response

        elif report_format == 'excel':
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename="sales_report_{start_date}_{end_date}.xlsx"'

            workbook = Workbook()
            worksheet = workbook.active
            worksheet.title = 'Sales Report'

            # Define styles
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
            border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
            alignment = Alignment(horizontal='center')
            summary_left_fill = PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")  # Light gray for left column

            # Main heading styling
            worksheet.merge_cells('A1:F1')
            heading_cell = worksheet.cell(row=1, column=1, value="URBAN EDGE Sales Report")
            heading_cell.font = Font(bold=True, size=16, name='Arial', underline='single')  # Increased size, font family, and underline
            heading_cell.alignment = Alignment(horizontal='center')

            # Period section styling
            worksheet.merge_cells('A2:F2')
            period_cell = worksheet.cell(row=2, column=1, value=f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            period_cell.font = Font(bold=True, size=12, name='Arial')  # Bold and larger font
            period_cell.alignment = Alignment(horizontal='center')

            # Side heading for Summary section
            worksheet.cell(row=3, column=1, value="Summary").font = Font(bold=True, size=14, name='Arial')  # Bold and larger font
            worksheet.merge_cells('A3:B3')  # Merge cells for the side heading

            # Add summary section
            summary_data = [
                # ['Date Range', f'{start_date.strftime("%Y-%m-%d")} to {end_date.strftime("%Y-%m-%d")}'],
                ['Total Orders', total_orders],
                ['Total Sales', total_sales],
                ['Total Discount', total_discount_amount],
            ]

            # Write summary data starting from row 4
            for row_index, row in enumerate(summary_data, start=4):
                worksheet.append(row)

            # Apply styling to summary section
            for row in worksheet.iter_rows(min_row=4, max_row=7, max_col=2):
                for cell in row:
                    cell.border = border
                    cell.alignment = alignment
                    if cell.column == 1:  # Left column (labels)
                        cell.fill = summary_left_fill
                        cell.font = Font(bold=True)

            # Adjust column widths for the summary section
            worksheet.column_dimensions['A'].width = 25  # Left column width
            worksheet.column_dimensions['B'].width = 25  # Right column width

            # Add an empty row for spacing
            worksheet.append([])

            # Side heading for Order Details section
            worksheet.cell(row=9, column=1, value="Order Details").font = Font(bold=True, size=14, name='Arial')  # Bold and larger font
            worksheet.merge_cells('A9:F9')  # Merge cells for the side heading

            # Add headers for the order data
            headers = ['Order ID', 'User', 'Price', 'Discounted Amount', 'Total Price', 'Date']
            worksheet.append(headers)

            # Apply header styles
            for col in range(1, len(headers) + 1):
                cell = worksheet.cell(row=10, column=col)
                cell.font = header_font
                cell.fill = header_fill
                cell.border = border
                cell.alignment = alignment

            # Add order data
            for order in order_data:
                row = [
                    order['id'],
                    order['user'].username,
                    order['total_before_coupon'],
                    order['discounted_amount'],
                    order['total_price'],
                    order['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
                ]
                worksheet.append(row)

            # Apply border and alignment to data rows
            for row in worksheet.iter_rows(min_row=11, max_row=worksheet.max_row, max_col=worksheet.max_column):
                for cell in row:
                    cell.border = border
                    cell.alignment = alignment

            # Set column widths for the order data section
            column_widths = [25, 20, 15, 20, 15, 22]  # Adjust as needed
            for i, column_width in enumerate(column_widths, 1):
                worksheet.column_dimensions[get_column_letter(i)].width = column_width

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