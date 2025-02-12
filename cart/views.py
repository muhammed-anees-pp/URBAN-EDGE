from decimal import Decimal
from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Cart, CartItem
from productsapp.models import Product, ProductVariant # Import ProductVariant
from django.contrib.auth.decorators import login_required
import logging
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger



logger = logging.getLogger(__name__)

@login_required
def cart_view(request):
    if not request.user.is_authenticated:
        return render(request, 'cart.html', {'cart_empty': True, 'message': 'Your cart is empty. Please log in to add items.'})

    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.all()

    # Check stock availability for each item in the cart
    out_of_stock_items = []
    for item in cart_items:
        if item.product_variant.stock < item.quantity:
            out_of_stock_items.append({
                'product_name': item.product_variant.product.name,
                'variant': f"{item.product_variant.color} / {item.product_variant.size}",
                'available_stock': item.product_variant.stock,
            })

    # Calculate total price for each cart item
    # for item in cart_items:
    #     item.total_price_value = item.total_price()  # Call the total_price method

    # grand_total = sum(item.total_price_value for item in cart_items)
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

    if not cart_items.exists():
        return render(request, 'cart.html', {'cart_empty': True, 'message': 'Your cart is empty. Start shopping now!'})
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(cart_items, 10)  # Show 10 items per page

    try:
        cart_items = paginator.page(page)
    except PageNotAnInteger:
        cart_items = paginator.page(1)
    except EmptyPage:
        cart_items = paginator.page(paginator.num_pages)


    context = {
        'cart_items': cart_items,
        # 'grand_total': grand_total,
        'cart_empty': False,
        'out_of_stock_items': out_of_stock_items,  # Pass out-of-stock items to the template
        'cart_count': cart_items.paginator.count,  # Total count of items
        'total_listed_price': total_listed_price,
        'total_offer_price': total_offer_price,
        'discounted_amount': discounted_amount,
        'delivery_charge': delivery_charge,
        'grand_total': grand_total,
    }

    return render(request, 'cart.html', context)

@login_required(login_url='/login/')
def add_to_cart(request):
    product_id = request.POST.get('product_id')
    color = request.POST.get('color')
    size = request.POST.get('size')
    quantity = int(request.POST.get('quantity', 1))  # Default to 1 if not provided

    logger.info(f"Adding to cart: product_id={product_id}, color={color}, size={size}, quantity={quantity}")

    try:
        # Fetch the product
        product = Product.objects.get(id=product_id)

        # Check if the product has any variants
        variants = ProductVariant.objects.filter(product=product)

        if not variants.exists():
            logger.error(f"No variants available for product_id={product_id}")
            return JsonResponse({'success': False, 'error': 'No stock available for this product.'})

        # Find the variant based on selected color and size
        if color and size:
            product_variant = variants.filter(color=color, size=size).first()
        if not product_variant:
            # Attempt to find a default variant if the exact match is not found
            product_variant = variants.first()

        if not product_variant:
            logger.error(f"No valid variant found for product_id={product_id}, color={color}, size={size}")
            return JsonResponse({'success': False, 'error': 'No valid variant found for this product.'})

        # Check stock availability
        if product_variant.stock <= 0:
            logger.error(f"Product variant out of stock: variant_id={product_variant.id}")
            return JsonResponse({'success': False, 'error': 'This product is out of stock.'})

        # Add to cart or update existing cart item
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product_variant=product_variant)
        if not created:
            return JsonResponse({'success': False, 'error': 'This product is already in the cart.'})

        cart_item.quantity += quantity
        cart_item.save()

        logger.info(f"Item added to cart: product_id={product_id}, variant_id={product_variant.id}, quantity={quantity}")
        return JsonResponse({'success': True, 'message': 'Item added to cart.'})

    except Product.DoesNotExist:
        logger.error(f"Product not found: product_id={product_id}")
        return JsonResponse({'success': False, 'error': 'Product not found.'})
    except Exception as e:
        logger.error(f"Error adding to cart: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required(login_url='/login/')
@require_POST
def update_cart(request, item_id, action):
    logger.debug(f"Update Cart URL: /update_cart/{item_id}/{action}/")
    try:
        cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
        product_variant = cart_item.product_variant

        if action == "increase":
            if cart_item.quantity + 1 > product_variant.stock:
                return JsonResponse({'message': 'Stock Will Be Unavailable', 'status': 'error'}, status=400)
            cart_item.quantity += 1
        elif action == "decrease" and cart_item.quantity > 1:
            cart_item.quantity -= 1
        cart_item.save()
        return JsonResponse({'message': 'Cart updated successfully.', 'status': 'success'})
    except CartItem.DoesNotExist:
        return JsonResponse({'message': 'Item not found in the cart.', 'status': 'error'}, status=404)
    except Exception as e:
        return JsonResponse({'message': str(e), 'status': 'error'}, status=500)


@login_required(login_url='/login/')
@require_POST
def remove_from_cart(request, item_id):
    logger.debug(f"Remove From Cart URL: /remove_from_cart/{item_id}/")
    try:
        cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
        cart_item.delete()
        return JsonResponse({'message': 'Item removed from cart successfully.'})
    except CartItem.DoesNotExist:
        return JsonResponse({'message': 'Item not found in the cart.'}, status=404)
    except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)
