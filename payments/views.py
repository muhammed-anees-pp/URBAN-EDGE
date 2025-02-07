from decimal import Decimal
from django.shortcuts import render, redirect
from django.urls import reverse
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest, JsonResponse
from orders.models import Order, OrderItem
from cart.models import Cart, CartItem
from productsapp.models import ProductVariant
from couponsapp.models import Coupon, CouponUsage
from user_profile.models import Address
import logging

logger = logging.getLogger(__name__)

razorpay_client = razorpay.Client(auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))

# def initiate_payment(request):
#     if request.method == "POST":
#         user = request.user
#         address_id = request.POST.get("address_id")
#         payment_method = request.POST.get("payment_method")

#         if not address_id or not payment_method:
#             return JsonResponse({"error": "Address or payment method not provided."}, status=400)

#         try:
#             address = Address.objects.get(id=address_id, user=user)
#             cart = Cart.objects.get(user=user)
#             cart_items = CartItem.objects.filter(cart=cart)

#             total_offer_price = Decimal('0.00')
#             for item in cart_items:
#                 price = Decimal(str(item.product_variant.product.offer if item.product_variant.product.offer else item.product_variant.product.price))
#                 quantity = Decimal(str(item.quantity))
#                 total_offer_price += price * quantity

#             delivery_charge = Decimal('40.00') if total_offer_price < Decimal('500.00') else Decimal('0.00')
#             grand_total = total_offer_price + delivery_charge

#             # Store cart details in session
#             request.session['cart_details'] = {
#                 'address_id': address_id,
#                 'payment_method': payment_method,
#                 'total_price': str(grand_total),
#                 'cart_items': [{'product_variant_id': item.product_variant.id, 'quantity': item.quantity} for item in cart_items]
#             }

#             if payment_method == "COD":
#                 # For COD, create the order immediately
#                 return create_order(request)
#             elif payment_method == "razorpay":
#                 amount = int(grand_total * 100)  # Convert to paise
#                 currency = "INR"
#                 receipt = f"order_{user.id}_{address_id}"
#                 notes = {
#                     "address_id": address_id,
#                     "user_id": user.id,
#                 }

#                 razorpay_order = razorpay_client.order.create({
#                     "amount": amount,
#                     "currency": currency,
#                     "receipt": receipt,
#                     "notes": notes,
#                 })

#                 return JsonResponse({
#                     "razorpay_order_id": razorpay_order["id"],
#                     "razorpay_merchant_key": settings.RAZOR_KEY_ID,
#                     "razorpay_amount": amount,
#                     "currency": currency,
#                     "callback_url": request.build_absolute_uri(reverse('order_success')),
#                 })
#             else:
#                 return JsonResponse({"error": "Invalid payment method."}, status=400)

#         except Exception as e:
#             logger.error(f"Error in initiate_payment: {str(e)}")
#             return JsonResponse({"error": str(e)}, status=500)


def initiate_payment(request):
    if request.method == "POST":
        user = request.user
        address_id = request.POST.get("address_id")
        payment_method = request.POST.get("payment_method")

        if not address_id or not payment_method:
            return JsonResponse({"error": "Address or payment method not provided."}, status=400)

        try:
            address = Address.objects.get(id=address_id, user=user)
            cart = Cart.objects.get(user=user)
            cart_items = CartItem.objects.filter(cart=cart)

            total_offer_price = Decimal('0.00')
            for item in cart_items:
                price = Decimal(str(item.product_variant.product.offer if item.product_variant.product.offer else item.product_variant.product.price))
                quantity = Decimal(str(item.quantity))
                total_offer_price += price * quantity

            delivery_charge = Decimal('40.00') if total_offer_price < Decimal('500.00') else Decimal('0.00')
            grand_total = total_offer_price + delivery_charge

            # Apply coupon discount if any
            coupon_code = request.session.get('coupon_code', None)
            coupon_discount = Decimal('0.00')
            if coupon_code:
                try:
                    coupon = Coupon.objects.get(coupon_code=coupon_code, is_active=True)
                    if coupon.is_valid() and total_offer_price >= coupon.minimum_purchase_amount:
                        if not CouponUsage.objects.filter(user=user, coupon=coupon).exists():
                            coupon_discount = (coupon.discount_percentage / Decimal('100.00')) * total_offer_price
                            grand_total -= coupon_discount
                except Coupon.DoesNotExist:
                    pass

            # Store cart details in session
            request.session['cart_details'] = {
                'address_id': address_id,
                'payment_method': payment_method,
                'total_price': str(grand_total),
                'cart_items': [{'product_variant_id': item.product_variant.id, 'quantity': item.quantity} for item in cart_items],
                'coupon_code': coupon_code,
                'coupon_discount': str(coupon_discount),
            }

            if payment_method == "COD":
                # For COD, create the order immediately
                return create_order(request)
            elif payment_method == "razorpay":
                amount = int(grand_total * 100)  # Convert to paise
                currency = "INR"
                receipt = f"order_{user.id}_{address_id}"
                notes = {
                    "address_id": address_id,
                    "user_id": user.id,
                }

                razorpay_order = razorpay_client.order.create({
                    "amount": amount,
                    "currency": currency,
                    "receipt": receipt,
                    "notes": notes,
                })

                return JsonResponse({
                    "razorpay_order_id": razorpay_order["id"],
                    "razorpay_merchant_key": settings.RAZOR_KEY_ID,
                    "razorpay_amount": amount,
                    "currency": currency,
                    "callback_url": request.build_absolute_uri(reverse('order_success')),
                })
            else:
                return JsonResponse({"error": "Invalid payment method."}, status=400)

        except Exception as e:
            logger.error(f"Error in initiate_payment: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)

def create_order(request):
    try:
        cart_details = request.session.get('cart_details')
        if not cart_details:
            return JsonResponse({"error": "Cart details not found in session."}, status=400)

        user = request.user
        address_id = cart_details['address_id']
        payment_method = cart_details['payment_method']
        total_price = Decimal(cart_details['total_price'])
        cart_items = cart_details['cart_items']
        coupon_code = cart_details.get('coupon_code', None)
        coupon_discount = Decimal(cart_details.get('coupon_discount', '0.00'))

        address = Address.objects.get(id=address_id, user=user)

        # Create the order
        order = Order.objects.create(
            user=user,
            address=address,
            payment_method=payment_method,
            total_price=total_price,
            payment_status='Paid' if payment_method != 'COD' else 'Pending',
            coupon=Coupon.objects.get(coupon_code=coupon_code) if coupon_code else None,
        )

        # Store order items
        for item in cart_items:
            product_variant = ProductVariant.objects.get(id=item['product_variant_id'])
            price = product_variant.product.offer if product_variant.product.offer else product_variant.product.price
            OrderItem.objects.create(
                order=order,
                product=product_variant.product,
                product_variant=product_variant,
                quantity=item['quantity'],
                price=price,
            )

            # Adjust stock
            product_variant.stock -= item['quantity']
            product_variant.save()

        # Clear the cart
        cart = Cart.objects.get(user=user)
        CartItem.objects.filter(cart=cart).delete()

        # Clear the session
        del request.session['cart_details']

        return JsonResponse({"success": "Order created successfully."}, status=200)

    except Exception as e:
        logger.error(f"Error in create_order: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


# def create_order(request):
#     try:
#         cart_details = request.session.get('cart_details')
#         if not cart_details:
#             return JsonResponse({"error": "Cart details not found in session."}, status=400)

#         user = request.user
#         address_id = cart_details['address_id']
#         payment_method = cart_details['payment_method']
#         total_price = Decimal(cart_details['total_price'])
#         cart_items = cart_details['cart_items']

#         address = Address.objects.get(id=address_id, user=user)

#         # Create the order
#         order = Order.objects.create(
#             user=user,
#             address=address,
#             payment_method=payment_method,
#             total_price=total_price,
#             payment_status='Paid' if payment_method != 'COD' else 'Pending',
#         )

#         # Store order items
#         for item in cart_items:
#             product_variant = ProductVariant.objects.get(id=item['product_variant_id'])
#             price = product_variant.product.offer if product_variant.product.offer else product_variant.product.price
#             OrderItem.objects.create(
#                 order=order,
#                 product=product_variant.product,
#                 product_variant=product_variant,
#                 quantity=item['quantity'],
#                 price=price,
#             )

#             # Adjust stock
#             product_variant.stock -= item['quantity']
#             product_variant.save()

#         # Clear the cart
#         cart = Cart.objects.get(user=user)
#         CartItem.objects.filter(cart=cart).delete()

#         # Clear the session
#         del request.session['cart_details']

#         return JsonResponse({"success": "Order created successfully."}, status=200)

#     except Exception as e:
#         logger.error(f"Error in create_order: {str(e)}")
#         return JsonResponse({"error": str(e)}, status=500)
    


@csrf_exempt
def paymenthandler(request):
    if request.method != "POST":
        logger.error("Invalid request method in paymenthandler.")
        return HttpResponseBadRequest("Invalid request method.")

    try:
        payment_id = request.POST.get('razorpay_payment_id', '')
        razorpay_order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')

        logger.info(f"Received payment data - Payment ID: {payment_id}, Order ID: {razorpay_order_id}, Signature: {signature}")

        if not payment_id or not razorpay_order_id or not signature:
            logger.error("Missing payment data in paymenthandler.")
            return HttpResponseBadRequest("Missing payment data.")

        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }

        try:
            # Verify the payment signature
            razorpay_client.utility.verify_payment_signature(params_dict)

            # Fetch the payment details
            payment = razorpay_client.payment.fetch(payment_id)
            logger.info(f"Payment status: {payment['status']}")

            if payment['status'] == 'captured':
                # Create the order after payment is successful
                response = create_order(request)
                if response.status_code == 200:
                    return redirect(reverse('order_success'))
                else:
                    logger.error("Failed to create order after payment.")
                    return HttpResponseBadRequest("Failed to create order.")

            # Capture the payment if not already captured
            razorpay_client.payment.capture(payment_id, int(request.session.get('amount', 0)))

            # Create the order after payment is successful
            response = create_order(request)
            if response.status_code == 200:
                return redirect(reverse('order_success'))
            else:
                logger.error("Failed to create order after payment.")
                return HttpResponseBadRequest("Failed to create order.")

        except razorpay.errors.SignatureVerificationError as e:
            logger.error(f"Signature verification failed: {str(e)}")
            return render(request, 'paymentfail.html')
        except Exception as e:
            logger.error(f"Error in paymenthandler: {str(e)}")
            return render(request, 'paymentfail.html')

    except Exception as e:
        logger.error(f"Unexpected error in paymenthandler: {str(e)}")
        return HttpResponseBadRequest()
