from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from decimal import Decimal
from cart.models import Cart, CartItem
from orders.models import Order, OrderItem
from user_profile.models import Address, ShippingAddress
from productsapp.models import ProductVariant
from couponsapp.models import Coupon, CouponUsage
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from wallet.models import Wallet, WalletTransaction
from django.template.loader import render_to_string
from weasyprint import HTML
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from payments.views import initiate_retry_payment




def is_admin(user):
    return user.is_authenticated and user.is_superuser


@login_required
def place_order(request):
    user = request.user
    addresses = Address.objects.filter(user=user, is_deleted=False)
    default_address = addresses.filter(is_default=True).first()

    try:
        cart = Cart.objects.get(user=user)
        cart_items = CartItem.objects.filter(cart=cart)

        if not cart_items.exists():
            return JsonResponse({"error": "Your cart is empty. Please add items to checkout."}, status=400)

        for item in cart_items:
            if item.quantity > item.product_variant.stock:
                messages.error(request, 'Please remove the out of stock products')
                return redirect('cart_view')

        total_listed_price = Decimal('0.00')
        total_offer_price = Decimal('0.00')
        for item in cart_items:
            price = Decimal(str(item.product_variant.product.offer if item.product_variant.product.offer else item.product_variant.product.price))
            quantity = Decimal(str(item.quantity))
            item.subtotal = price * quantity
            listed_price = Decimal(str(item.product_variant.product.price))
            offer_price = Decimal(str(item.product_variant.product.offer)) if item.product_variant.product.offer else listed_price
            item.subtotal_listed_price = listed_price * quantity
            item.subtotal_offer_price = offer_price * quantity
            total_listed_price += item.subtotal_listed_price
            total_offer_price += item.subtotal_offer_price

        discounted_amount = total_listed_price - total_offer_price
        delivery_charge = Decimal('40.00') if total_offer_price < Decimal('500.00') else Decimal('0.00')
        grand_total = total_offer_price + delivery_charge

        # Store cart total in session for coupon validation
        request.session['cart_total'] = str(total_offer_price)

        # Apply coupon discount if any
        coupon_discount = Decimal('0.00')
        coupon_code = request.session.get('coupon_code', None)
        if coupon_code:
            try:
                coupon = Coupon.objects.get(coupon_code=coupon_code, is_active=True)
                if coupon.is_valid() and total_offer_price >= coupon.minimum_purchase_amount:
                    if not CouponUsage.objects.filter(user=user, coupon=coupon).exists():
                        coupon_discount = (coupon.discount_percentage / Decimal('100.00')) * total_offer_price
                        grand_total -= coupon_discount
                        # Add coupon discount to the total discount amount
                        discounted_amount += coupon_discount
            except Coupon.DoesNotExist:
                pass

    except Cart.DoesNotExist:
        cart_items = []
        total_listed_price = Decimal('0.00')
        total_offer_price = Decimal('0.00')
        discounted_amount = Decimal('0.00')
        delivery_charge = Decimal('0.00')
        grand_total = Decimal('0.00')

    if request.method == "POST":
        try:
            address_id = request.POST.get("address_id")
            payment_method = request.POST.get("payment_method")

            if not address_id or not payment_method:
                return JsonResponse({"error": "Address or payment method not provided."}, status=400)

            # Handle address selection
            if address_id == "new":
                # If the user adds a new address, it should already be in the Address table
                # So we fetch the latest address added by the user
                address = Address.objects.filter(user=user).order_by('-id').first()
            elif address_id:
                # Fetch the selected address
                address = Address.objects.get(id=address_id, user=user)
            else:
                # Use default address
                address = default_address

            if not address:
                return JsonResponse({"error": "No valid address found."}, status=400)

            # Copy the address to the ShippingAddress table
            shipping_address = ShippingAddress.objects.create(
                user=user,
                name=address.name,
                address=address.address,
                city=address.city,
                state=address.state,
                country=address.country,
                postcode=address.postcode,
                phone=address.phone,
            )

            # Check if payment method is wallet and if the user has sufficient balance
            if payment_method == "wallet":
                wallet = Wallet.objects.get(user=user)
                if wallet.balance < grand_total:
                    return JsonResponse({"error": "Insufficient funds in wallet."}, status=400)

            # Determine payment and order status based on payment method
            if payment_method == "COD":
                payment_status = 'Pending'
                order_status = 'pending'
                order_item_status = 'order_placed'
            elif payment_method == "wallet":
                payment_status = 'Paid'
                order_status = 'pending'
                order_item_status = 'order_placed'
            elif payment_method == "razorpay":
                payment_status = 'Pending'
                order_status = 'processing'
                order_item_status = 'processing'

            order = Order.objects.create(
                user=user,
                shipping_address=shipping_address,
                payment_method=payment_method,
                payment_status=payment_status,
                status=order_status,
                total_price=grand_total,
                coupon=coupon if coupon_code else None,
            )

            for item in cart_items:
                if item.product_variant.stock < item.quantity:
                    return JsonResponse({"error": f"Not enough stock for {item.product_variant.product.name}."}, status=400)

                item.product_variant.stock -= item.quantity
                item.product_variant.save()

                price = item.product_variant.product.offer if item.product_variant.product.offer else item.product_variant.product.price
                for _ in range(item.quantity):
                    OrderItem.objects.create(
                        order=order,
                        product=item.product_variant.product,
                        product_variant=item.product_variant,
                        quantity=1,
                        status=order_item_status,
                        price=price,
                    )

            # Deduct amount from wallet if payment method is wallet
            if payment_method == "wallet":
                wallet.balance -= grand_total
                wallet.save()
                WalletTransaction.objects.create(
                    wallet=wallet,
                    order=order,
                    amount=grand_total,
                    transaction_type='debit'
                )

            # Record coupon usage only after the order is successfully created
            if coupon_code:
                CouponUsage.objects.create(user=user, coupon=coupon)
                del request.session['coupon_code']

            cart_items.delete()

            # Clear the entered coupon code from the session after placing the order
            if 'entered_coupon_code' in request.session:
                del request.session['entered_coupon_code']

            return redirect(reverse('order_success'))

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    # Retrieve the entered coupon code from the session
    entered_coupon_code = request.session.get('entered_coupon_code', '')
    context = {
        'addresses': addresses,
        'default_address': default_address,
        'cart_items': cart_items,
        'total_listed_price': total_listed_price,
        'total_offer_price': total_offer_price,
        'discounted_amount': discounted_amount,
        'delivery_charge': delivery_charge,
        'grand_total': grand_total,
        'coupon_discount': coupon_discount,
        'entered_coupon_code': entered_coupon_code,  # Pass the entered coupon code to the template
    }
    return render(request, 'user/checkout.html', context)




@login_required
def order_success(request):
    latest_order = Order.objects.filter(user=request.user).order_by('-created_at').first()
    
    if not latest_order:
        return render(request, 'user/order_confirm.html', {
            'error': 'No order found.'
        })
    
    order_items = OrderItem.objects.filter(order=latest_order)
    
    total_listed_price = Decimal('0.00')
    total_offer_price = Decimal('0.00')
    for item in order_items:
        listed_price = Decimal(str(item.product.price))
        offer_price = Decimal(str(item.product.offer)) if item.product.offer else listed_price
        quantity = Decimal(str(item.quantity))
        total_listed_price += listed_price * quantity
        total_offer_price += offer_price * quantity
    
    discounted_amount = total_listed_price - total_offer_price
    delivery_charge = Decimal('40.00') if total_offer_price < Decimal('500.00') else Decimal('0.00')

    # Use the total_price from the Order model (already includes coupon discount)
    grand_total = latest_order.total_price

    # Calculate coupon discount only if a coupon was applied to this order
    coupon_discount = Decimal('0.00')
    if latest_order.coupon:
        # Calculate the discount percentage applied
        coupon_discount = (latest_order.coupon.discount_percentage / Decimal('100.00')) * total_offer_price
    
    # Clear the entered coupon code from the session after the order is successfully placed
    if 'entered_coupon_code' in request.session:
        del request.session['entered_coupon_code']
    
    context = {
        'order_number': latest_order.id,
        'order_items': order_items,
        'total_listed_price': total_listed_price,
        'total_offer_price': total_offer_price,
        'discounted_amount': discounted_amount,
        'delivery_charge': delivery_charge,
        'grand_total': grand_total,
        'coupon_discount': coupon_discount if latest_order.coupon else Decimal('0.00'),  # Only show discount if coupon was applied
        'payment_status': latest_order.payment_status,
        'show_retry_button': latest_order.payment_status == 'Pending' and latest_order.payment_method == 'razorpay',
    }
    
    return render(request, 'user/order_confirm.html', context)


@login_required
def user_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(orders, 10)  # Show 10 orders per page

    try:
        orders = paginator.page(page)
    except PageNotAnInteger:
        orders = paginator.page(1)
    except EmptyPage:
        orders = paginator.page(paginator.num_pages)

    return render(request, 'user/orders_list.html', {'orders': orders})


@login_required
def order_items(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.items.all()
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(order_items, 10)  # Show 10 items per page

    try:
        order_items = paginator.page(page)
    except PageNotAnInteger:
        order_items = paginator.page(1)
    except EmptyPage:
        order_items = paginator.page(paginator.num_pages)

    return render(request, 'user/order_items.html', {'order': order, 'order_items': order_items})


@login_required
def user_order_details(request, item_id):
    particular_product = get_object_or_404(OrderItem, id=item_id, order__user=request.user)
    order = particular_product.order

    order_items = order.items.all()

    total_listed_price = Decimal('0.00')
    total_offer_price = Decimal('0.00')
    for item in order_items:
        listed_price = Decimal(str(item.product.price))
        offer_price = Decimal(str(item.product.offer)) if item.product.offer else listed_price
        quantity = Decimal(str(item.quantity))
        item.subtotal_listed_price = listed_price * quantity
        item.subtotal_offer_price = offer_price * quantity
        total_listed_price += item.subtotal_listed_price
        total_offer_price += item.subtotal_offer_price

    discounted_amount = total_listed_price - total_offer_price
    delivery_charge = Decimal('40.00') if total_offer_price < Decimal('500.00') else Decimal('0.00')
    grand_total = total_offer_price + delivery_charge

    # Calculate coupon discount
    coupon_discount = Decimal('0.00')
    if order.coupon:
        coupon_discount = (order.coupon.discount_percentage / Decimal('100.00')) * total_offer_price
        grand_total -= coupon_discount

    other_products_in_order = order_items.exclude(id=particular_product.id)

    current_time = timezone.now()
    days_since_delivery = (current_time - particular_product.updated_at).days

    return render(request, 'user/order_details.html', {
        'order': order,
        'particular_product': particular_product,
        'other_products_in_order': other_products_in_order,
        'total_listed_price': total_listed_price,
        'total_offer_price': total_offer_price,
        'discounted_amount': discounted_amount,
        'delivery_charge': delivery_charge,
        'grand_total': grand_total,
        'coupon_discount': coupon_discount,
        'days_since_delivery': days_since_delivery,
    })



@login_required
def cancel_order_item(request, item_id):
    order_item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)

    if order_item.status in ['out_for_delivery', 'delivered', 'canceled']:
        return JsonResponse({
            "error": "This item cannot be canceled as it is already out for delivery, delivered, or canceled."
        }, status=400)

    if request.method == "POST":
        cancel_reason = request.POST.get("cancel_reason")
        if cancel_reason:
            product_variant = order_item.product_variant
            product_variant.stock += order_item.quantity
            product_variant.save()

            # Filter desired statuses
            desired_statuses = [
                'order_placed',
                'shipped',
                'out_for_delivery',
                'delivered',
                'return_requested',
                'return_denied'
            ]

            # Filter full_order_items and remaining_order_items
            full_order_items = OrderItem.objects.filter(
                order=order_item.order,
                status__in=desired_statuses
            )
            full_total_price = sum(item.price * item.quantity for item in full_order_items)

            remaining_order_items = OrderItem.objects.filter(
                order=order_item.order,
                status__in=desired_statuses
            ).exclude(id=order_item.id)
            remaining_total_price = sum(item.price * item.quantity for item in remaining_order_items)

            coupon = order_item.order.coupon
            refund_amount = Decimal('0.00')

            if coupon:
                total_discount = (coupon.discount_percentage / Decimal('100.00')) * full_total_price

                if remaining_total_price < coupon.minimum_purchase_amount:
                    if not order_item.order.discount_applied:
                        refund_amount = (order_item.price * order_item.quantity) - total_discount
                        order_item.order.discount_applied = True
                    else:
                        refund_amount = order_item.price * order_item.quantity
                else:
                    refund_amount = (order_item.price * order_item.quantity) - (
                        (coupon.discount_percentage / Decimal('100.00')) *
                        order_item.price *
                        order_item.quantity
                    )
                order_item.order.save()
            else:
                refund_amount = order_item.price * order_item.quantity

            order_item.status = 'canceled'
            order_item.cancel_reason = cancel_reason
            order_item.save()

            # Update the order status
            order_item.order.update_order()

            refund_amount = max(refund_amount, Decimal('0.00'))

            # Credit wallet for non-COD payments
            if order_item.order.payment_method != 'COD':
                wallet, created = Wallet.objects.get_or_create(user=request.user)
                wallet.balance += refund_amount
                wallet.save()

                WalletTransaction.objects.create(
                    wallet=wallet,
                    order=order_item.order,
                    amount=refund_amount,
                    transaction_type='credit'
                )

            return JsonResponse({
                "success": True,
                "message": "Order item canceled successfully.",
                "redirect_url": reverse('user_order_details', args=[order_item.id])
            })
        else:
            return JsonResponse({"error": "Please provide a reason for cancellation."}, status=400)

    return render(request, 'user/cancel_reason.html', {'order_item': order_item})



@login_required
def request_return(request, item_id):
    order_item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)

    # Check if the item is eligible for return (delivered within 7 days)
    if order_item.status != 'delivered' or (timezone.now() - order_item.updated_at).days > 7:
        messages.error(request, "This item is not eligible for return.")
        return redirect('user_order_details', item_id=item_id)

    if request.method == "POST":
        return_reason = request.POST.get("return_reason")
        if return_reason:
            # Update the order item status
            order_item.status = 'return_requested'
            order_item.return_reason = return_reason
            order_item.return_requested_at = timezone.now()
            order_item.save()

            messages.success(request, "Return request submitted successfully.")
            return redirect('user_order_details', item_id=item_id)
        else:
            messages.error(request, "Please provide a reason for return.")
            return redirect('request_return', item_id=item_id)

    # Render the return reason form template
    return render(request, 'user/return_reason.html', {'order_item': order_item})


def download_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = order.items.all()
    
    # Check if invoice is allowed for this order
    allowed_statuses = ['delivered', 'return_requested', 'return_denied', 'returned']
    if not order_items.filter(status__in=allowed_statuses).exists():
        return redirect('user_order_details')

    # Calculate values for the invoice
    total_listed_price = sum(item.product.price * item.quantity for item in order_items)
    total_offer_price = sum(item.price * item.quantity for item in order_items)
    delivery_charge = Decimal('40.00') if total_offer_price < Decimal('500.00') else Decimal('0.00')
    coupon_discount = Decimal('0.00')
    
    if order.coupon:
        coupon_discount = total_offer_price * (order.coupon.discount_percentage / Decimal('100.00'))
    
    grand_total = (total_offer_price - coupon_discount) + delivery_charge

    # Prepare order items with calculated values
    processed_items = []
    for item in order_items:
        item_listed_price = item.product.price
        item_offer_price = item.price
        quantity = item.quantity
        item_offer_total = item_offer_price * quantity
        
        # Calculate coupon discount for this item proportionally
        item_coupon_discount = Decimal('0.00')
        if total_offer_price > 0 and coupon_discount > 0:
            item_coupon_discount = (item_offer_total / total_offer_price) * coupon_discount
        
        discounted_price = item_offer_price - (item_coupon_discount / quantity)
        
        processed_items.append({
            'name': item.product.name,
            'quantity': quantity,
            'listed_price': item_listed_price,
            'offer_price': item_offer_price,
            'coupon_discount': item_coupon_discount.quantize(Decimal('0.00')),
            'discount':discounted_price,
            'subtotal': (item_offer_price * quantity) - item_coupon_discount,
        })

    context = {
        'order': order,
        'order_items': processed_items,
        'delivery_charge': delivery_charge,
        'coupon_discount': coupon_discount.quantize(Decimal('0.00')),
        'grand_total': grand_total.quantize(Decimal('0.00')),
        'total_offer_price': total_offer_price.quantize(Decimal('0.00')),
        'total_listed_price': total_listed_price.quantize(Decimal('0.00')),
    }

    # Generate PDF
    html_string = render_to_string('user/invoice_template.html', context)
    html = HTML(string=html_string)
    pdf = html.write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.id}.pdf"'
    return response



@user_passes_test(is_admin)
def order_management(request):
    orders = Order.objects.all().order_by('-created_at')

    # Pagination
    page = request.GET.get('page', 1)  # Get the page number from the URL parameters
    paginator = Paginator(orders, 10)  # Show 10 products per page

    try:
        orders = paginator.page(page)
    except PageNotAnInteger:
        orders = paginator.page(1)
    except EmptyPage:
        orders = paginator.page(paginator.num_pages)

    return render(request, 'admin/order_admin.html', {'orders': orders})


@user_passes_test(is_admin)
def admin_order_details(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = order.items.all()
    
    for item in order_items:
        item.subtotal = item.quantity * item.price

    status_choices = OrderItem.ORDER_ITEM_STATUS_CHOICES

    # Calculate coupon discount
    coupon_discount = Decimal('0.00')
    if order.coupon:
        coupon_discount = (order.coupon.discount_percentage / Decimal('100.00')) * order.total_price

    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(order_items, 10)

    try:
        order_items = paginator.page(page)
    except PageNotAnInteger:
        order_items = paginator.page(1)
    except EmptyPage:
        order_items = paginator.page(paginator.num_pages)

    return render(request, 'admin/order_details_admin.html', {
        'order': order,
        'order_items': order_items,
        'status_choices': status_choices,
        'coupon_discount': coupon_discount,
    })


@user_passes_test(is_admin)
@require_POST
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    item_id = request.POST.get('item_id')
    new_status = request.POST.get('status')

    if not item_id or not new_status:
        return JsonResponse({"error": "Invalid request."}, status=400)

    order_item = get_object_or_404(OrderItem, id=item_id, order=order)

    # Debug: Log the current and new status
    print(f"Current status of OrderItem {order_item.id}: {order_item.status}")
    print(f"Requested new status: {new_status}")

    # Check if the new status is allowed using the can_update_status method
    if not order_item.can_update_status(new_status):
        return JsonResponse({"error": f"Cannot update status from {order_item.status} to {new_status}."}, status=400)

    if new_status == 'return_requested':
        return JsonResponse({"error": "Admins cannot directly request returns. Only users can request returns."}, status=400)

    # Update the item status
    order_item.status = new_status
    order_item.save()

    # Debug: Log the status update
    print(f"Updated status of OrderItem {order_item.id} to {order_item.status}")

    # If the order is delivered and payment method is COD, update payment status to 'Paid'
    if new_status == 'delivered' and order.payment_method == 'COD':
        order.payment_status = 'Paid'
        order.save()

    # If the status is updated to 'return', process the refund logic
    if new_status == 'return':
        # Refill stock and credit amount to wallet if the status is updated to 'return'
        product_variant = order_item.product_variant
        product_variant.stock += order_item.quantity
        product_variant.save()
        order_item.returned_at = timezone.now()

        # Filter desired statuses
        desired_statuses = [
            'order_placed',
            'shipped',
            'out_for_delivery',
            'delivered',
            'return_requested',
            'return',
            'return_denied'
        ]

        # Filter full_order_items and remaining_order_items
        full_order_items = OrderItem.objects.filter(
            order=order_item.order,
            status__in=desired_statuses
        )
        full_total_price = sum(item.price * item.quantity for item in full_order_items)

        remaining_order_items = OrderItem.objects.filter(
            order=order_item.order,
            status__in=desired_statuses
        ).exclude(id=order_item.id)
        remaining_total_price = sum(item.price * item.quantity for item in remaining_order_items)

        coupon = order_item.order.coupon
        refund_amount = Decimal('0.00')

        if coupon:
            total_discount = (coupon.discount_percentage / Decimal('100.00')) * full_total_price

            if remaining_total_price < coupon.minimum_purchase_amount:
                if not order_item.order.discount_applied:
                    refund_amount = (order_item.price * order_item.quantity) - total_discount
                    order_item.order.discount_applied = True
                    print(f"Before saving: discount_applied={order_item.order.discount_applied}")
                    order_item.order.save(update_fields=['discount_applied'])  # Ensure only this field updates
                    order_item.order.refresh_from_db()  # Force refresh from DB
                    print(f"Final discount_applied value in DB: {order.discount_applied}")
                    print(f"After saving: discount_applied={order_item.order.discount_applied}")
                else:
                    refund_amount = order_item.price * order_item.quantity
            else:
                refund_amount = (order_item.price * order_item.quantity) - (
                    (coupon.discount_percentage / Decimal('100.00')) *
                    order_item.price *
                    order_item.quantity
                )
            order_item.order.save()
        else:
            refund_amount = order_item.price * order_item.quantity

        order_item.status = 'returned'
        order_item.save()
        refund_amount = max(refund_amount, Decimal('0.00'))

        # Credit wallet for non-COD payments
        if order_item.order.payment_method != 'COD':
            wallet, created = Wallet.objects.get_or_create(user=order.user)
            wallet.balance += refund_amount
            wallet.save()

            WalletTransaction.objects.create(
                wallet=wallet,
                order=order_item.order,
                amount=refund_amount,
                transaction_type='credit'
            )
    else:
        pass

    # Update the order status
    print(f"Before update_order: discount_applied={order.discount_applied}")
    order.update_order()
    order.refresh_from_db()
    print(f"After update_order: discount_applied={order.discount_applied}")


    return JsonResponse({
        "success": True,
        "message": "Order item status updated successfully.",
        "redirect_url": reverse('admin_order_details', args=[order.id])
    })


"""
RETRY PAYMENT FOR RAZORPAY FAILED PAYMENTS
"""
@csrf_exempt
def retry_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if request.method == "POST":
        # Store cart details in session for retry payment
        request.session['retry_payment_details'] = {
            'order_id': order.id,
            'shipping_address_id': order.shipping_address.id,
            'payment_method': order.payment_method,
            'total_price': str(order.total_price),
            'cart_items': [{'product_variant_id': item.product_variant.id, 'quantity': item.quantity} for item in order.items.all()],
            'coupon_code': order.coupon.coupon_code if order.coupon else None,
            'coupon_discount': '0.00',
        }
        return initiate_retry_payment(request)
    
    # If it's a GET request, render a confirmation page
    context = {
        'order': order,
    }
    return render(request, 'user/retry_payment_confirmation.html', context)


"""
RETRY ORDER SUCCESS PAGE
"""
@login_required
def retry_order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.items.all()
    
    total_listed_price = Decimal('0.00')
    total_offer_price = Decimal('0.00')
    for item in order_items:
        listed_price = Decimal(str(item.product.price))
        offer_price = Decimal(str(item.product.offer)) if item.product.offer else listed_price
        quantity = Decimal(str(item.quantity))
        total_listed_price += listed_price * quantity
        total_offer_price += offer_price * quantity
    
    discounted_amount = total_listed_price - total_offer_price
    delivery_charge = Decimal('40.00') if total_offer_price < Decimal('500.00') else Decimal('0.00')
    grand_total = order.total_price

    coupon_discount = Decimal('0.00')
    if order.coupon:
        coupon_discount = (order.coupon.discount_percentage / Decimal('100.00')) * total_offer_price
    
    context = {
        'order_number': order.id,
        'order_items': order_items,
        'total_listed_price': total_listed_price,
        'total_offer_price': total_offer_price,
        'discounted_amount': discounted_amount,
        'delivery_charge': delivery_charge,
        'grand_total': grand_total,
        'coupon_discount': coupon_discount,
        'payment_status': order.payment_status,
        'show_retry_button': False  # Disable retry button on this page
    }
    
    return render(request, 'user/retry_order_confirm.html', context)