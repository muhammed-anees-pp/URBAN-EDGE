# from django.http import JsonResponse
# from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib.auth.decorators import login_required, user_passes_test
# import json
# from decimal import Decimal
# from cart.models import Cart, CartItem
# from orders.models import Order, OrderItem
# from user_profile.models import Address
# from productsapp.models import ProductVariant
# from django.urls import reverse

# @login_required
# def place_order(request):
#     user = request.user
#     addresses = Address.objects.filter(user=user)
#     default_address = addresses.filter(is_default=True).first()

#     try:
#         cart = Cart.objects.get(user=user)
#         cart_items = CartItem.objects.filter(cart=cart)
        
#         if not cart_items.exists():
#             return JsonResponse({"error": "Your cart is empty. Please add items to checkout."}, status=400)

#         for item in cart_items:
#             if item.quantity < 1:
#                 return JsonResponse({"error": f"Invalid quantity for {item.product_variant.product.name}. Please update your cart."}, status=400)
            
#             if item.quantity > item.product_variant.stock:
#                 return JsonResponse({
#                     "error": f"Requested quantity for {item.product_variant.product.name} exceeds available stock."
#                 }, status=400)
        
#         total = Decimal('0.00')
#         for item in cart_items:
#             price = Decimal(str(item.product_variant.product.offer if item.product_variant.product.offer else item.product_variant.product.price))
#             quantity = Decimal(str(item.quantity))
#             item.subtotal = price * quantity
#             total += item.subtotal

#         delivery_charge = Decimal('40.00') if total < Decimal('500.00') else Decimal('0.00')
#         total_amount = total + delivery_charge  # Total amount including delivery charge
        
#     except Cart.DoesNotExist:
#         cart_items = []
#         total = Decimal('0.00')
#         delivery_charge = Decimal('0.00')
#         total_amount = total  # Total amount including delivery charge
    
#     if request.method == "POST":
#         try:
#             address_id = request.POST.get("address_id")
#             payment_method = request.POST.get("payment_method")

#             if not address_id or not payment_method:
#                 return JsonResponse({"error": "Address or payment method not provided."}, status=400)

#             address = Address.objects.get(id=address_id, user=request.user)
            
#             order = Order.objects.create(
#                 user=user,
#                 address=address,
#                 payment_method=payment_method,
#                 total_price=total_amount,
#             )

#             for item in cart_items:
#                 if item.product_variant.stock < item.quantity:
#                     return JsonResponse({"error": f"Not enough stock for {item.product_variant.product.name}."}, status=400)

#                 item.product_variant.stock -= item.quantity
#                 item.product_variant.save()

#                 price = item.product_variant.product.offer if item.product_variant.product.offer else item.product_variant.product.price
#                 for _ in range(item.quantity):
#                     OrderItem.objects.create(
#                         order=order,
#                         product=item.product_variant.product,
#                         product_variant=item.product_variant,  # Add this line to include product_variant
#                         quantity=1,
#                         price=price,
#                     )

#             cart_items.delete()

#             return redirect(reverse('order_success'))

#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=400)
    
#     context = {
#         'addresses': addresses,
#         'default_address': default_address,
#         'cart_items': cart_items,
#         'total': total,
#         'delivery_charge': delivery_charge,
#         'total_amount': total_amount,
#     }
#     return render(request, 'user/checkout.html', context)


# def order_success(request):
#     # Fetch the latest order for the logged-in user
#     latest_order = Order.objects.filter(user=request.user).order_by('-created_at').first()
    
#     if not latest_order:
#         # Handle case where no order exists (e.g., redirect to home or show an error)
#         return render(request, 'user/order_confirm.html', {
#             'error': 'No order found.'
#         })
    
#     # Fetch order items for the latest order
#     order_items = OrderItem.objects.filter(order=latest_order)
    
#     # Prepare data for the template
#     context = {
#         'order_number': latest_order.id,  # Use the custom order ID
#         'order_items': order_items,
#         'order_total': latest_order.total_price,
#     }
    
#     return render(request, 'user/order_confirm.html', context)


# @login_required
# def user_orders(request):
#     # Fetch all order items for the user, grouped by order
#     order_items = OrderItem.objects.filter(order__user=request.user).order_by('-order__created_at')
#     return render(request, 'user/orders_list.html', {'order_items': order_items})


# ##################################################################################################################

# # @login_required
# # def user_order_details(request, order_id):
# #     order = get_object_or_404(Order, id=order_id, user=request.user)
# #     order_items = order.items.all()

# #     # Calculate subtotal for each item
# #     for item in order_items:
# #         item.subtotal = item.quantity * item.price

# #     # Get the particular product (first product in the order)
# #     particular_product = order_items.first()

# #     # Get other products in the same order (excluding the particular product)
# #     other_products_in_order = order_items.exclude(id=particular_product.id) if order_items.count() > 1 else []

# #     return render(request, 'user/order_details.html', {
# #         'order': order, 
# #         'particular_product': particular_product,
# #         'other_products_in_order': other_products_in_order,
# #     })


# # @login_required
# # def user_order_details(request, item_id):
# #     # Get the clicked order item
# #     particular_product = get_object_or_404(OrderItem, id=item_id, order__user=request.user)
# #     order = particular_product.order  # Get the order from the item

# #     # Get all items in the same order
# #     order_items = order.items.all()

# #     # Calculate subtotal for each item
# #     for item in order_items:
# #         item.subtotal = item.quantity * item.price

# #     # Exclude the particular product to get other products
# #     other_products_in_order = order_items.exclude(id=particular_product.id)

# #     return render(request, 'user/order_details.html', {
# #         'order': order,
# #         'particular_product': particular_product,
# #         'other_products_in_order': other_products_in_order,
# #     })


# @login_required
# def user_order_details(request, order_id):
#     # Get the order using the custom order ID
#     order = get_object_or_404(Order, id=order_id, user=request.user)
#     order_items = order.items.all()

#     # Calculate subtotal for each item
#     for item in order_items:
#         item.subtotal = item.quantity * item.price

#     # Get the particular product (first product in the order)
#     particular_product = order_items.first()

#     # Get other products in the same order (excluding the particular product)
#     other_products_in_order = order_items.exclude(id=particular_product.id) if order_items.count() > 1 else []

#     return render(request, 'user/order_details.html', {
#         'order': order,
#         'particular_product': particular_product,
#         'other_products_in_order': other_products_in_order,
#     })






# from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib.auth.decorators import login_required
# from django.http import JsonResponse
# from .models import OrderItem

# @login_required
# def cancel_order_item(request, item_id):
#     order_item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)

#     if request.method == "POST":
#         # Handle the cancellation reason form submission
#         cancel_reason = request.POST.get("cancel_reason")
#         if cancel_reason:
#             order_item.status = 'canceled'
#             order_item.cancel_reason = cancel_reason
#             order_item.save()
#             return JsonResponse({"message": "Order item canceled successfully."})
#         else:
#             return JsonResponse({"error": "Please provide a reason for cancellation."}, status=400)

#     # Render the cancellation reason form template
#     return render(request, 'user/cancel_reason.html', {'order_item': order_item})
#################################################33


from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
import json
from decimal import Decimal
from cart.models import Cart, CartItem
from orders.models import Order, OrderItem
from user_profile.models import Address
from productsapp.models import ProductVariant
from django.urls import reverse

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
        
        total = Decimal('0.00')
        for item in cart_items:
            price = Decimal(str(item.product_variant.product.offer if item.product_variant.product.offer else item.product_variant.product.price))
            quantity = Decimal(str(item.quantity))
            item.subtotal = price * quantity
            total += item.subtotal

        delivery_charge = Decimal('40.00') if total < Decimal('500.00') else Decimal('0.00')
        total_amount = total + delivery_charge  # Total amount including delivery charge
        
    except Cart.DoesNotExist:
        cart_items = []
        total = Decimal('0.00')
        delivery_charge = Decimal('0.00')
        total_amount = total  # Total amount including delivery charge
    
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
                total_price=total_amount,
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
        'total': total,
        'delivery_charge': delivery_charge,
        'total_amount': total_amount,
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
    
    # Prepare data for the template
    context = {
        'order_number': latest_order.id,  # Use the custom order ID
        'order_items': order_items,
        'order_total': latest_order.total_price,
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
    for item in order_items:
        item.subtotal = item.quantity * item.price

    # Exclude the particular product to get other products
    other_products_in_order = order_items.exclude(id=particular_product.id)

    return render(request, 'user/order_details.html', {
        'order': order,
        'particular_product': particular_product,
        'other_products_in_order': other_products_in_order,
    })


@login_required
def cancel_order_item(request, item_id):
    order_item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)

    if request.method == "POST":
        # Handle the cancellation reason form submission
        cancel_reason = request.POST.get("cancel_reason")
        if cancel_reason:
            order_item.status = 'canceled'
            order_item.cancel_reason = cancel_reason
            order_item.save()
            return JsonResponse({"message": "Order item canceled successfully."})
        else:
            return JsonResponse({"error": "Please provide a reason for cancellation."}, status=400)

    # Render the cancellation reason form template
    return render(request, 'user/cancel_reason.html', {'order_item': order_item})




############################################


# def is_admin(user):
#     return user.is_authenticated and user.is_superuser

# @user_passes_test(is_admin)
# def order_management(request):
#     orders = Order.objects.all().order_by('-created_at')
#     return render(request, 'admin/order_admin.html', {'orders': orders})

# @user_passes_test(is_admin)
# def admin_order_details(request, order_id):
#     order = get_object_or_404(Order, id=order_id)
#     order_items = order.items.all()
    
#     for item in order_items:
#         item.subtotal = item.quantity * item.price

#     return render(request, 'admin/order_details_admin.html', {'order': order, 'order_items': order_items})

# @user_passes_test(is_admin)
# def update_order_status(request, order_id):
#     if request.method == "POST":
#         order = get_object_or_404(Order, id=order_id)
#         new_status = request.POST.get('status')

#         if new_status in dict(Order.ORDER_STATUS_CHOICES):
#             order.status = new_status
#             order.save()
#             return JsonResponse({"message": "Order status updated successfully."})

#     return JsonResponse({"error": "Invalid request."}, status=400)





