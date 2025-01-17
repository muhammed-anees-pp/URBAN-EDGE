from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages
from .models import Product, SizeVariant
from category.models import Category
from decimal import Decimal
from decimal import Decimal, InvalidOperation
from admin_side.views import is_admin 
from django.contrib.auth.decorators import user_passes_test
from django.db.models import F
import re

@user_passes_test(is_admin)
def product_list(request):
    products = Product.objects.all()
    categories = Category.objects.all()
    return render(request, 'admin/product.html', {
        'products': products,
        'categories': categories
    })

@user_passes_test(is_admin)
def create_product(request):
    if request.method == "POST":
        try:
            # Get form data
            name = request.POST.get('product_name')
            description = request.POST.get('description')
            category_id = request.POST.get('category')
            color = request.POST.get('color')
            price_str = request.POST.get('price')
            offer_str = request.POST.get('offer')

            # Validate name and description
            if not name:
                messages.error(request, "Product name is required")
                return redirect('create_product')
            if Product.objects.filter(name__iexact=name).exists():
                 messages.error(request, "product already exists!")
                 return redirect('create_product')
            if not description or len(description) < 10:
                messages.error(request, "Description must be at least 10 characters long.")
                return redirect('create_product')

            # Ensure valid price
            try:
                price = Decimal(price_str) if price_str else None
                if price is None or price <= 0:
                    messages.error(request, "Please provide a valid price greater than 0.")
                    return redirect('create_product')
            except InvalidOperation:
                messages.error(request, "Price must be a valid decimal number.")
                return redirect('create_product')

            # Ensure valid offer, if provided
            offer = None
            if offer_str:
                try:
                    offer = Decimal(offer_str)
                    if offer < 0 or offer >= price:
                        messages.error(request, "Offer must be a positive decimal and less than the price.")
                        return redirect('create_product')
                except InvalidOperation:
                    messages.error(request, "Offer must be a valid decimal number.")
                    return redirect('create_product')

            # Validate category selection
            if not category_id:
                messages.error(request, "Please select a category.")
                return redirect('create_product')

            # Check if the selected category exists
            try:
                category = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                messages.error(request, "Selected category does not exist.")
                return redirect('create_product')

            # Handle image uploads and validate file types
            image1 = request.FILES.get('image1')
            image2 = request.FILES.get('image2')
            image3 = request.FILES.get('image3')

            # Check if at least one image is uploaded
            if not image1:
                messages.error(request, "Please upload at least the first image.")
                return redirect('create_product')

            # Image format validation
            for image in [image1, image2, image3]:
                if image and not image.name.lower().endswith(('.png', '.jpg', '.jpeg','.webp')):
                    messages.error(request, "Only PNG, JPG, and JPEG image files are allowed.")
                    return redirect('create_product')

            # Create the product instance if all validations pass
            product = Product(
                name=name,
                description=description,
                category=category,
                color=color,
                price=price,
                offer=offer,
                image1=image1,
                image2=image2,
                image3=image3,
            )
            product.save()

            messages.success(request, "Product created successfully.")
            return redirect('product_management')

        except Exception as e:
            messages.error(request, f"Error creating product: {str(e)}")
            return redirect('create_product')

    # GET request - show the form
    categories = Category.objects.filter(is_listed=True)
    return render(request, 'admin/product.html', {'categories': categories})

    
@user_passes_test(is_admin)
def toggle_product_listing(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
        product.is_listed = not product.is_listed
        product.save()
        status = "listed" if product.is_listed else "unlisted"
        messages.success(request, f"Product successfully {status}")
    except Product.DoesNotExist:
        messages.error(request, "Product not found")
    return redirect('product_management')


@user_passes_test(is_admin)
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        try:
            # Validate and update name
            name = request.POST.get('product_name', product.name)
            if not name:
                messages.error(request, "Product name is required")
                return redirect('edit_product', product_id=product.id)
            if Product.objects.filter(name__iexact=name).exists():
                messages.error(request, "product already exists!")
                return redirect('create_product')
            product.name = name

            # Validate and update description
            description = request.POST.get('description', product.description)
            if not description:
                messages.error(request, "Description is required")
                return redirect('edit_product', product_id=product.id)
            product.description = description

            # Update category if provided
            color = request.POST.get('color', product.color)
            category_id = request.POST.get('category')
            if category_id:
                try:
                    category = Category.objects.get(id=category_id)
                    product.category = category
                except Category.DoesNotExist:
                    messages.error(request, "Selected category does not exist.")
                    return redirect('edit_product', product_id=product.id)

            # Validate and update price
            try:
                price = Decimal(request.POST.get('price') or "0.00")
                if price <= 0:
                    messages.error(request, "Price must be greater than zero.")
                    return redirect('edit_product', product_id=product.id)
                product.price = price
            except InvalidOperation:
                messages.error(request, "Price must be a valid decimal number.")
                return redirect('edit_product', product_id=product.id)

            # Validate and update offer
            offer_str = request.POST.get('offer')
            if offer_str:
                try:
                    offer = Decimal(offer_str)
                    if offer < 0 or offer >= product.price:
                        messages.error(request, "Offer must be a positive decimal and less than the price.")
                        return redirect('edit_product', product_id=product.id)
                    product.offer = offer
                except InvalidOperation:
                    messages.error(request, "Offer must be a valid decimal number.")
                    return redirect('edit_product', product_id=product.id)
                
            product.save()

            messages.success(request, "Product updated successfully.")
            return redirect('product_management')

        except Exception as e:
            messages.error(request, f"Error updating product: {str(e)}")
            return redirect('edit_product', product_id=product.id)

    categories = Category.objects.filter(is_listed=True)
    return render(request, 'admin/edit_product.html', {
        'product': product,
        'categories': categories
    })

@user_passes_test(is_admin)
def variant_list(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    variants = product.size_variants.all()  # Get related size variants
    return render(request, 'admin/variant.html', {'product': product, 'variants': variants})

@user_passes_test(is_admin)
def add_size_variants(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == "POST":
        try:
            size = request.POST.get("size", "").strip()
            stock = request.POST.get("stock", "").strip()

            # Validate inputs
            if not size:
                messages.error(request, "Size cannot be empty")
                return redirect('variant', product_id=product_id)

            # Convert stock to integer and validate
            try:
                stock = int(stock)
                if stock < 0:
                    messages.error(request, "Stock cannot be negative")
                    return redirect('variant', product_id=product_id)
            except ValueError:
                messages.error(request, "Stock must be a valid number")
                return redirect('variant', product_id=product_id)

            # Check if size variant already exists
            if SizeVariant.objects.filter(product=product, size=size).exists():
                messages.error(request, f"Size {size} already exists for this product")
                return redirect('variant', product_id=product_id)

            # Create the size variant
            SizeVariant.objects.create(
                product=product,
                size=size,
                stock=stock
            )

            messages.success(request, "Size variant added successfully")
            return redirect('variant', product_id=product_id)

        except Exception as e:
            messages.error(request, f"Error adding size variant: {str(e)}")
            return redirect('variant', product_id=product_id)

    return render(request, 'admin/edit_variant.html', {'product': product})

@user_passes_test(is_admin)
def update_variant(request,variant_id):
        variant = SizeVariant.objects.get(id=variant_id)
        if request.method == 'POST':
            size = request.POST.get('size')
            stock = request.POST.get('stock')

            variant.size = size
            variant.stock = F('stock') + stock
            variant.save()
            messages.success(request, 'Variant updated successfully!')
            return redirect('variant', product_id=variant.product.id)

        context = {'variant': variant}
        return render(request,'admin/edit_variant.html',context)


# def product_details(request,product_id):
#     product = Product.objects.get(id = product_id)
#     sizes = product.size_variants.filter(stock__gt = 0)
#     stock = product.stock_variants.filter(stock__gt=0)
#     related_products = Product.objects.filter(category = product.category).exclude(id = product_id)

#     context = {
#         'product' : product,
#          'sizes' : sizes,
#          'related_products' : related_products 
#     }
#     return render(request,'product_details.html',context)

def product_details(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    sizes = product.size_variants.filter(stock__gt=0)  # Correct attribute: size_variants
    related_products = Product.objects.filter(category=product.category).exclude(id=product_id)

    context = {
        'product': product,
        'sizes': sizes,  # Pass the size variants (with stock) to the template
        'related_products': related_products,
    }
    return render(request, 'product_details.html', context)

def category_products(request, category_id):
    category = get_object_or_404(Category, id=category_id, is_listed=True)
    products = Product.objects.filter(category=category, is_listed=True)

    context = {
        'category': category,
        'products': products
    }
    return render(request, 'category_products.html', context)