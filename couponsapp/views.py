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