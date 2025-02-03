from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from decimal import Decimal
from cart.models import Cart, CartItem
from orders.models import Order, OrderItem
from user_profile.models import Address
from productsapp.models import ProductVariant
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger  # Import Paginator


@login_required
def place_order(request):
    user = request.user
    addresses = Address.objects.filter(user=user)
    default_address = addresses.filter(is_default=True).first()

    try:
        cart = Cart.objects.get(user=user)
        cart_items = CartItem.objects.filter(cart=cart)
        
        if not cart_items.exists():
            return JsonResponse({"error": "Your cart is empty. Please add items to checkout."}, status=400)

        for item in cart_items:
            if item.quantity < 1:
                return JsonResponse({"error": f"Invalid quantity for {item.product_variant.product.name}. Please update your cart."}, status=400)
            
            if item.quantity > item.product_variant.stock:
                return JsonResponse({
                    "error": f"Requested quantity for {item.product_variant.product.name} exceeds available stock."
                }, status=400)
        
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
        grand_total = total_offer_price + delivery_charge  # Grand total including delivery charge
        
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

            address = Address.objects.get(id=address_id, user=request.user)
            
            order = Order.objects.create(
                user=user,
                address=address,
                payment_method=payment_method,
                total_price=grand_total,
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
                        product_variant=item.product_variant,  # Add this line to include product_variant
                        quantity=1,
                        price=price,
                    )

            cart_items.delete()

            return redirect(reverse('order_success'))

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    
    context = {
        'addresses': addresses,
        'default_address': default_address,
        'cart_items': cart_items,
        'total_listed_price': total_listed_price,
        'total_offer_price': total_offer_price,
        'discounted_amount': discounted_amount,
        'delivery_charge': delivery_charge,
        'grand_total': grand_total,
    }
    return render(request, 'user/checkout.html', context)


def order_success(request):
    # Fetch the latest order for the logged-in user
    latest_order = Order.objects.filter(user=request.user).order_by('-created_at').first()
    
    if not latest_order:
        # Handle case where no order exists (e.g., redirect to home or show an error)
        return render(request, 'user/order_confirm.html', {
            'error': 'No order found.'
        })
    
    # Fetch order items for the latest order
    order_items = OrderItem.objects.filter(order=latest_order)
    
    # Calculate total listed price, total offer price, and discounted amount
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
    grand_total = total_offer_price + delivery_charge
    
    # Prepare data for the template
    context = {
        'order_number': latest_order.id,  # Use the custom order ID
        'order_items': order_items,
        'total_listed_price': total_listed_price,
        'total_offer_price': total_offer_price,
        'discounted_amount': discounted_amount,
        'delivery_charge': delivery_charge,
        'grand_total': grand_total,
    }
    
    return render(request, 'user/order_confirm.html', context)


@login_required
def user_orders(request):
    # Fetch all order items for the user, grouped by order
    order_items = OrderItem.objects.filter(order__user=request.user).order_by('-order__created_at')
    return render(request, 'user/orders_list.html', {'order_items': order_items})


@login_required
def user_order_details(request, item_id):
    # Get the clicked order item
    particular_product = get_object_or_404(OrderItem, id=item_id, order__user=request.user)
    order = particular_product.order  # Get the order from the item

    # Get all items in the same order
    order_items = order.items.all()

    # Calculate subtotal for each item
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

    # Exclude the particular product to get other products
    other_products_in_order = order_items.exclude(id=particular_product.id)

    # Pass the current time to the template
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
        'days_since_delivery': days_since_delivery,  # Add this line
    })


@login_required
def cancel_order_item(request, item_id):
    order_item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)

    # Check if the order item can be canceled (before "Out for Delivery")
    if order_item.status in ['out_for_delivery', 'delivered', 'canceled']:
        return JsonResponse({
            "error": "This item cannot be canceled as it is already out for delivery, delivered, or canceled."
        }, status=400)

    if request.method == "POST":
        # Handle the cancellation reason form submission
        cancel_reason = request.POST.get("cancel_reason")
        if cancel_reason:
            # Refill the product stock
            product_variant = order_item.product_variant
            product_variant.stock += order_item.quantity
            product_variant.save()

            # Update the order item status
            order_item.status = 'canceled'
            order_item.cancel_reason = cancel_reason
            order_item.save()

            # Return a JSON response with success message and redirect URL
            return JsonResponse({
                "success": True,
                "message": "Order item canceled successfully.",
                "redirect_url": reverse('user_order_details', args=[order_item.id])
            })
        else:
            return JsonResponse({"error": "Please provide a reason for cancellation."}, status=400)

    # Render the cancellation reason form template
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


def is_admin(user):
    return user.is_authenticated and user.is_superuser


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

    # Pagination
    page = request.GET.get('page', 1)  # Get the page number from the URL parameters
    paginator = Paginator(order_items, 10)  # Show 10 products per page

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

    # Define the allowed status transitions
    allowed_transitions = {
        'order_placed': ['shipped', 'canceled'],
        'shipped': ['out_for_delivery', 'canceled'],
        'out_for_delivery': ['delivered', 'canceled'],
        'delivered': ['return_requested'],  # Only users can request returns
        'canceled': [],  # No further transitions after canceled
        'return_requested': ['returned', 'return_denied'],  # Admin can approve or deny return
        'returned': [],  # No further transitions after returned
        'return_denied': [],  # No further transitions after return denied
    }

    current_status = order_item.status

    # Check if the new status is allowed
    if new_status not in allowed_transitions.get(current_status, []):
        return JsonResponse({"error": f"Cannot update status from {current_status} to {new_status}."}, status=400)

    # Prevent admins from directly changing status to 'return_requested'
    if new_status == 'return_requested':
        return JsonResponse({"error": "Admins cannot directly request returns. Only users can request returns."}, status=400)

    # Update the item status
    order_item.status = new_status

    # Refill stock if the status is updated to 'returned'
    if new_status == 'returned':
        product_variant = order_item.product_variant
        product_variant.stock += order_item.quantity
        product_variant.save()
        order_item.returned_at = timezone.now()  # Set the returned_at timestamp

    order_item.save()

    # Debug: Print the updated item status
    print(f"Updated OrderItem {order_item.id} status to {order_item.status}")

    # Return a success response
    return JsonResponse({
        "success": True,
        "message": "Order item status updated successfully.",
        "redirect_url": reverse('admin_order_details', args=[order.id])
    })