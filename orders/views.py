from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import json
from decimal import Decimal
from cart.models import Cart, CartItem
from orders.models import Order, OrderItem
from user_profile.models import Address
from productsapp.models import ProductVariant

@login_required
def place_order(request):
    user = request.user
    addresses = Address.objects.filter(user=user)

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
        total += delivery_charge
        
    except Cart.DoesNotExist:
        cart_items = []
        total = Decimal('0.00')
        delivery_charge = Decimal('0.00')
    
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            address_id = data.get("address_id")
            payment_method = data.get("payment_method")

            if not address_id or not payment_method:
                return JsonResponse({"error": "Address or payment method not provided."}, status=400)

            address = Address.objects.get(id=address_id, user=request.user)
            
            if payment_method == 'COD' and total > Decimal('1000.00'):
                return JsonResponse({"error": "Cash on Delivery is not available for orders above ₹1000."}, status=400)

            order = Order.objects.create(
                user=user,
                address=address,
                payment_method=payment_method,
                total_price=total,
            )

            for item in cart_items:
                if item.product_variant.stock < item.quantity:
                    return JsonResponse({"error": f"Not enough stock for {item.product_variant.product.name}."}, status=400)

                item.product_variant.stock -= item.quantity
                item.product_variant.save()

                price = item.product_variant.product.offer if item.product_variant.product.offer else item.product_variant.product.price
                OrderItem.objects.create(
                    order=order,
                    product=item.product_variant.product,
                    quantity=item.quantity,
                    price=price,
                )

            cart_items.delete()

            return JsonResponse({"success": "Order placed successfully!"}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid request format."}, status=400)
    
    context = {
        'addresses': addresses,
        'cart_items': cart_items,
        'total': total,
        'delivery_charge': delivery_charge
    }
    return render(request, 'user/checkout.html', context)


def order_success(request):
    return render(request, 'user/order_confirm.html')
