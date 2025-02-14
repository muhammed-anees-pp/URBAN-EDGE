from decimal import Decimal
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from .models import Coupon, CouponUsage
from django.contrib.auth.decorators import login_required

@login_required
def apply_coupon(request):
    if request.method == "POST":
        coupon_code = request.POST.get('coupon_code')
        request.session['entered_coupon_code'] = coupon_code  # Store the entered coupon code in the session
        try:
            coupon = Coupon.objects.get(coupon_code=coupon_code, is_active=True)
            if coupon.is_valid():
                # Check if the user has already used this coupon
                if CouponUsage.objects.filter(user=request.user, coupon=coupon).exists():
                    messages.error(request, 'You have already used this coupon.')
                else:
                    # Check if the cart total meets the minimum purchase amount
                    cart_total = Decimal(request.session.get('cart_total', '0.00'))
                    if cart_total >= coupon.minimum_purchase_amount:
                        request.session['coupon_code'] = coupon_code
                        messages.success(request, 'Coupon applied successfully.')
                    else:
                        messages.error(request, f'Minimum purchase amount of ₹{coupon.minimum_purchase_amount} required to apply this coupon.')
            else:
                messages.error(request, 'This coupon is not valid.')
        except Coupon.DoesNotExist:
            messages.error(request, 'Invalid coupon code.')
    return redirect('place_order')


@login_required
def remove_coupon(request):
    if 'coupon_code' in request.session:
        del request.session['coupon_code']
        messages.success(request, 'Coupon removed successfully.')
    return redirect('place_order')




from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Coupon
from .forms import CouponForm  # We'll create this form later

# List Coupons with Pagination
def coupon_list(request):
    query = request.GET.get('q', '')
    coupons = Coupon.objects.all()

    if query:
        coupons = coupons.filter(coupon_code__icontains=query)

    paginator = Paginator(coupons, 10)  # Show 10 coupons per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'coupons': page_obj,
        'query': query,
    }
    return render(request, 'admin/coupon_list.html', context)

# Add Coupon
def add_coupon(request):
    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Coupon added successfully.')
            return redirect('coupon_list')
    else:
        form = CouponForm()
    return render(request, 'admin/add_coupon.html', {'form': form})

# Edit Coupon
def edit_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, coupon_id=coupon_id)
    if request.method == 'POST':
        form = CouponForm(request.POST, instance=coupon)  # Pass the instance here
        if form.is_valid():
            form.save()
            messages.success(request, 'Coupon updated successfully.')
            return redirect('coupon_list')
    else:
        form = CouponForm(instance=coupon)  # Pass the instance here
    return render(request, 'admin/edit_coupon.html', {'form': form, 'coupon': coupon})



# Activate/Deactivate Coupon
def toggle_coupon_status(request, coupon_id):
    coupon = get_object_or_404(Coupon, coupon_id=coupon_id)
    coupon.is_active = not coupon.is_active
    coupon.save()
    action = "activated" if coupon.is_active else "deactivated"
    messages.success(request, f'Coupon {action} successfully.')
    return redirect('coupon_list')

# Delete Coupon
def delete_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, coupon_id=coupon_id)
    coupon.delete()
    messages.success(request, 'Coupon deleted successfully.')
    return redirect('coupon_list')



