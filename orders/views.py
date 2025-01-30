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
#     default_address = addresses.filter(is_default=True).first()  # Get the default address

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
#         total += delivery_charge
        
#     except Cart.DoesNotExist:
#         cart_items = []
#         total = Decimal('0.00')
#         delivery_charge = Decimal('0.00')
    
#     if request.method == "POST":
#         try:
#             address_id = request.POST.get("address_id")
#             payment_method = request.POST.get("payment_method")

#             if not address_id or not payment_method:
#                 return JsonResponse({"error": "Address or payment method not provided."}, status=400)

#             address = Address.objects.get(id=address_id, user=request.user)
            
#             # if payment_method == 'COD' and total > Decimal('1000.00'):
#             #     return JsonResponse({"error": "Cash on Delivery is not available for orders above ₹1000."}, status=400)

#             order = Order.objects.create(
#                 user=user,
#                 address=address,
#                 payment_method=payment_method,
#                 total_price=total,
#             )

#             for item in cart_items:
#                 if item.product_variant.stock < item.quantity:
#                     return JsonResponse({"error": f"Not enough stock for {item.product_variant.product.name}."}, status=400)

#                 item.product_variant.stock -= item.quantity
#                 item.product_variant.save()

#                 price = item.product_variant.product.offer if item.product_variant.product.offer else item.product_variant.product.price
#                 OrderItem.objects.create(
#                     order=order,
#                     product=item.product_variant.product,
#                     quantity=item.quantity,
#                     price=price,
#                 )

#             cart_items.delete()

#             # Redirect to the order success page
#             return redirect(reverse('order_success'))

#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=400)
    
#     context = {
#         'addresses': addresses,
#         'default_address': default_address,  # Pass the default address to the template
#         'cart_items': cart_items,
#         'total': total,
#         'delivery_charge': delivery_charge
#     }
#     return render(request, 'user/checkout.html', context)


# def order_success(request):
#     return render(request, 'user/order_confirm.html')



# ## New additions
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

# @login_required
# def user_orders(request):
#     orders = Order.objects.filter(user=request.user).order_by('-created_at')
#     return render(request, 'user/orders_list.html', {'orders': orders})

# @login_required
# def user_order_details(request, order_id):
#     order = get_object_or_404(Order, id=order_id, user=request.user)
#     order_items = order.items.all()

#     for item in order_items:
#         item.subtotal = item.quantity * item.price

#     return render(request, 'user/order_details.html', {'order': order, 'order_items': order_items})

# @login_required
# def cancel_order(request, order_id):
#     order = get_object_or_404(Order, id=order_id, user=request.user)

#     if order.status == 'pending':
#         order.status = 'canceled'
#         order.save()
#         return JsonResponse({"message": "Order canceled successfully."})
    
#     return JsonResponse({"error": "Order cannot be canceled."}, status=400)




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
#         total += delivery_charge
        
#     except Cart.DoesNotExist:
#         cart_items = []
#         total = Decimal('0.00')
#         delivery_charge = Decimal('0.00')
    
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
#                 total_price=total,
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
#         'delivery_charge': delivery_charge
#     }
#     return render(request, 'user/checkout.html', context)


# def order_success(request):
#     return render(request, 'user/order_confirm.html')

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

# @login_required
# def user_orders(request):
#     orders = Order.objects.filter(user=request.user).order_by('-created_at')
#     return render(request, 'user/orders_list.html', {'orders': orders})

# @login_required
# def user_order_details(request, order_id):
#     order = get_object_or_404(Order, id=order_id, user=request.user)
#     order_items = order.items.all()

#     for item in order_items:
#         item.subtotal = item.quantity * item.price

#     return render(request, 'user/order_details.html', {'order': order, 'order_items': order_items})

# @login_required
# def cancel_order_item(request, item_id):
#     order_item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)

#     if order_item.order.status == 'pending':
#         order_item.order.status = 'canceled'
#         order_item.order.save()
#         return JsonResponse({"message": "Order item canceled successfully."})
    
#     return JsonResponse({"error": "Order item cannot be canceled."}, status=400)


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


# def order_success(request):
#     return render(request, 'user/order_confirm.html')

# from django.shortcuts import render
# from orders.models import Order, OrderItem

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


def is_admin(user):
    return user.is_authenticated and user.is_superuser

@user_passes_test(is_admin)
def order_management(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'admin/order_admin.html', {'orders': orders})

@user_passes_test(is_admin)
def admin_order_details(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = order.items.all()
    
    for item in order_items:
        item.subtotal = item.quantity * item.price

    return render(request, 'admin/order_details_admin.html', {'order': order, 'order_items': order_items})

@user_passes_test(is_admin)
def update_order_status(request, order_id):
    if request.method == "POST":
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')

        if new_status in dict(Order.ORDER_STATUS_CHOICES):
            order.status = new_status
            order.save()
            return JsonResponse({"message": "Order status updated successfully."})

    return JsonResponse({"error": "Invalid request."}, status=400)

@login_required
def user_orders(request):
    # Fetch all order items for the user, grouped by order
    order_items = OrderItem.objects.filter(order__user=request.user).order_by('-order__created_at')
    return render(request, 'user/orders_list.html', {'order_items': order_items})

# @login_required
# def user_order_details(request, order_id):
#     order = get_object_or_404(Order, id=order_id, user=request.user)
#     order_items = order.items.all()

#     for item in order_items:
#         item.subtotal = item.quantity * item.price

#     return render(request, 'user/order_details.html', {'order': order, 'order_items': order_items})

@login_required
def user_order_details(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.items.all()

    for item in order_items:
        item.subtotal = item.quantity * item.price

    return render(request, 'user/order_details.html', {
        'order': order, 
        'order_items': order_items
    })



@login_required
def cancel_order_item(request, item_id):
    order_item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)

    if order_item.order.status == 'pending':
        order_item.delete()  # Remove the canceled item
        return JsonResponse({"message": "Order item canceled successfully."})
    
    return JsonResponse({"error": "Order item cannot be canceled."}, status=400)