from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Product, ProductVariant, ProductImage
from category.models import Category
from decimal import Decimal, InvalidOperation
from admin_side.views import is_admin
from django.contrib.auth.decorators import user_passes_test
import base64
import uuid
from django.core.files.base import ContentFile


# Product List View
@user_passes_test(is_admin)
def product_list(request):
    query = request.GET.get('q', '')  # Get the search query from the URL parameters
    products = Product.objects.all()

    if query:  # If there is a search query
        products = products.filter(name__icontains=query)  # Search for product names that contain the query (case-insensitive)

    categories = Category.objects.all()
    return render(request, 'admin/product_list.html', {
        'products': products,
        'categories': categories,
        'query': query,  # Pass the query back to the template to preserve it in the search bar
    })


# Create Product View
@user_passes_test(is_admin)
def create_product(request):
    if request.method == "POST":
        form_data = {
            'product_name': request.POST.get('product_name', ''),
            'description': request.POST.get('description', ''),
            'category': request.POST.get('category', ''),
            'price': request.POST.get('price', ''),
            'offer': request.POST.get('offer', ''),
        }

        try:
            name = form_data['product_name']
            description = form_data['description']
            category_id = form_data['category']
            price = Decimal(form_data['price'])

            if not name or not description or not category_id:
                messages.error(request, "All fields are required.")
                raise ValueError("Validation Error")

            category = Category.objects.get(id=category_id)

            product = Product.objects.create(
                name=name,
                description=description,
                category=category,
                price=price,
                offer=Decimal(form_data['offer']) if form_data['offer'] else None
            )

            # Handle base64 images
            product_images = request.POST.getlist('product_images[]')
            if not product_images:
                messages.error(request, "Please upload at least one image.")
                raise ValueError("Validation Error")

            for base64_image in product_images:
                if ',' in base64_image:
                    format, imgstr = base64_image.split(';base64,')
                else:
                    imgstr = base64_image

                try:
                    decoded_image = base64.b64decode(imgstr)
                    image_file = ContentFile(decoded_image, name=f'product_{product.id}_{uuid.uuid4()}.jpg')
                    ProductImage.objects.create(product=product, image=image_file)
                except Exception as e:
                    product.delete()  # Rollback if image processing fails
                    messages.error(request, f"Error processing images: {str(e)}")
                    raise ValueError("Image processing error")

            messages.success(request, "Product created successfully!")
            return redirect('product_management')

        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {str(e)}")

    categories = Category.objects.filter(is_listed=True)
    return render(request, 'admin/add_product.html', {'categories': categories})


# Edit Product View (with no color field)
@user_passes_test(is_admin)
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        form_data = {
            'product_name': request.POST.get('product_name', product.name),
            'description': request.POST.get('description', product.description),
            'category': request.POST.get('category', product.category.id if product.category else ''),
            'price': request.POST.get('price', product.price),
            'offer': request.POST.get('offer', product.offer),
        }

        errors = []

        try:
            name = form_data['product_name']
            if not name or Product.objects.filter(name__iexact=name).exclude(id=product.id).exists():
                errors.append("Product name is required and must be unique.")

            description = form_data['description']
            if not description:
                errors.append("Description is required.")

            try:
                price = Decimal(form_data['price'])
                if price <= 0:
                    errors.append("Price must be greater than zero.")
            except (InvalidOperation, ValueError):
                errors.append("Price must be a valid decimal number.")

            offer = None
            offer_str = form_data['offer']
            if offer_str:
                try:
                    offer = Decimal(offer_str)
                    if offer < 0 or offer >= price:
                        errors.append("Offer must be a positive decimal and less than the price.")
                except (InvalidOperation, ValueError):
                    errors.append("Offer must be a valid decimal number.")

            category_id = form_data['category']
            if not category_id:
                errors.append("Please select a category.")
            else:
                try:
                    category = Category.objects.get(id=category_id)
                except Category.DoesNotExist:
                    errors.append("Selected category does not exist.")

            if errors:
                categories = Category.objects.filter(is_listed=True)
                return render(request, 'admin/edit_product.html', {
                    'product': product,
                    'categories': categories,
                    'form_data': form_data,
                    'errors': errors,
                })

            # Update product details
            product.name = name
            product.description = description
            product.price = price
            product.offer = offer
            product.category = category
            product.save()

            messages.success(request, "Product updated successfully.")
            return redirect('product_management')

        except Exception as e:
            errors.append(f"Error updating product: {str(e)}")
            categories = Category.objects.filter(is_listed=True)
            return render(request, 'admin/edit_product.html', {
                'product': product,
                'categories': categories,
                'form_data': form_data,
                'errors': errors,
            })

    categories = Category.objects.filter(is_listed=True)
    return render(request, 'admin/edit_product.html', {
        'product': product,
        'categories': categories,
    })

@user_passes_test(is_admin)
def add_variant(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        color = request.POST.get('color', '').strip()
        size = request.POST.get('size', '').strip()
        stock = request.POST.get('stock', '').strip()

        errors = []

        # Validation checks
        if not color:
            errors.append("Color is required.")
        if not size:
            errors.append("Size is required.")
        try:
            stock = int(stock)
            if stock < 0:
                errors.append("Stock cannot be negative.")
        except ValueError:
            errors.append("Stock must be a valid number.")

        # Check for duplicates (same color and size for the product) - case insensitive
        if ProductVariant.objects.filter(product=product).filter(
            color__iexact=color, size__iexact=size).exists():
            errors.append("This variant already exists.")

        if errors:
            # If there are errors, render the form with error messages
            for error in errors:
                messages.error(request, error)
            return render(request, 'admin/add_variant.html', {'product': product, 'errors': errors, 'color': color, 'size': size, 'stock': stock})

        try:
            # Create the variant
            ProductVariant.objects.create(product=product, color=color, size=size, stock=stock)
            messages.success(request, "Variant added successfully!")
            return redirect('variant', product_id=product_id)
        except Exception as e:
            messages.error(request, f"Error adding variant: {str(e)}")
            return render(request, 'admin/add_variant.html', {'product': product})

    return render(request, 'admin/add_variant.html', {'product': product})



# Variant List View
@user_passes_test(is_admin)
def variant_list(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    variants = product.variants.all()  # Get related variants
    return render(request, 'admin/variant.html', {'product': product, 'variants': variants})


@user_passes_test(is_admin)
def update_variant(request, variant_id):
    variant = get_object_or_404(ProductVariant, id=variant_id)

    if request.method == "POST":
        color = request.POST.get('color', '').strip()
        size = request.POST.get('size', '').strip()
        stock = request.POST.get('stock', '').strip()

        # List to store error messages
        errors = []

        # Validation checks
        if not color or not size:
            errors.append("Color and Size are required.")
        
        if stock.isdigit() and int(stock) < 0:
            errors.append("Stock cannot be negative.")

        # Check for duplicate combination (if another variant with same color & size exists) - case insensitive
        if ProductVariant.objects.filter(product=variant.product).filter(
            color__iexact=color, size__iexact=size).exclude(id=variant.id).exists():
            errors.append("This variant already exists.")

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'admin/edit_variant.html', {'variant': variant, 'errors': errors})

        try:
            # Update the variant if no errors
            variant.color = color
            variant.size = size
            variant.stock = int(stock)
            variant.save()

            messages.success(request, "Variant updated successfully!")
            return redirect('variant', product_id=variant.product.id)

        except Exception as e:
            messages.error(request, f"Error updating variant: {str(e)}")
            return render(request, 'admin/edit_variant.html', {'variant': variant})

    return render(request, 'admin/edit_variant.html', {'variant': variant})

@user_passes_test(is_admin)
def delete_variant(request, variant_id):
    # Get the variant object or 404 if not found
    variant = get_object_or_404(ProductVariant, id=variant_id)

    # Delete the variant
    variant.delete()

    # Redirect back to the variants list page for the product
    return redirect('variant', product_id=variant.product.id)


# Product Details View
def product_details(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    variants = product.variants.filter(stock__gt=0)  # Get variants with stock greater than 0
    related_products = Product.objects.filter(category=product.category).exclude(id=product_id)

    context = {
        'product': product,
        'variants': variants,  # Pass the variants (color, size, stock) to the template
        'related_products': related_products,
    }
    return render(request, 'product_details.html', context)

# Toggle Product Listing
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


# Category Products View
# def category_products(request, category_id):
#     category = get_object_or_404(Category, id=category_id, is_listed=True)
#     products = Product.objects.filter(category=category, is_listed=True)

#     context = {
#         'category': category,
#         'products': products
#     }
#     return render(request, 'category_products.html', context)

def category_products(request, category_id):
    category = get_object_or_404(Category, id=category_id, is_listed=True)
    products = Product.objects.filter(category=category, is_listed=True).prefetch_related('images')

    # Prepare context data with only the first image
    context = {
        'category': category,
        'products': [{
            'product': product,
            'first_image': product.images.first()  # Fetch the first image
        } for product in products]
    }
    return render(request, 'category_products.html', context)