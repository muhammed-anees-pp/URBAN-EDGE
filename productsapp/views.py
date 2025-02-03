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
from django.db.models import Q
import json
import random
from reviews.models import Review
from django.http import JsonResponse
from .models import ProductVariant


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


@user_passes_test(is_admin)
def create_product(request):
    if request.method == "POST":
        form_data = {
            'product_name': request.POST.get('product_name', ''),
            'description': request.POST.get('description', ''),
            'category': request.POST.get('category', ''),
            'price': request.POST.get('price', ''),
            'offer': request.POST.get('offer', ''),
            'product_images': request.POST.getlist('product_images[]')  # Preserve image data
        }

        errors = []
        try:
            # Validation
            name = form_data['product_name']
            description = form_data['description']
            category_id = form_data['category']
            try:
                price = Decimal(form_data['price'])
                if price <= 0:
                    errors.append("Price must be greater than zero.")
            except (InvalidOperation, ValueError):
                errors.append("Price must be a valid decimal number.")

            offer = None
            if form_data['offer']:
                try:
                    offer = Decimal(form_data['offer'])
                    if offer < 0 or offer >= price:
                        errors.append("Offer must be a positive number and less than the price.")
                except (InvalidOperation, ValueError):
                    errors.append("Offer must be a valid decimal number.")

            if not name:
                errors.append("Product name is required.")
            if not description:
                errors.append("Description is required.")
            if not category_id:
                errors.append("Category is required.")
            else:
                try:
                    category = Category.objects.get(id=category_id)
                except Category.DoesNotExist:
                    errors.append("Selected category does not exist.")

            product_images = form_data['product_images']
            if not product_images:
                errors.append("Please upload at least one image.")

            if errors:
                raise ValueError("Validation Error")

            # Create the product
            product = Product.objects.create(
                name=name,
                description=description,
                category=category,
                price=price,
                offer=offer
            )

            # Process images
            for base64_image in product_images:
                if ',' in base64_image:
                    format, imgstr = base64_image.split(';base64,')
                else:
                    imgstr = base64_image

                decoded_image = base64.b64decode(imgstr)
                image_file = ContentFile(decoded_image, name=f'product_{product.id}_{uuid.uuid4()}.jpg')
                ProductImage.objects.create(product=product, image=image_file)

            messages.success(request, "Product created successfully!")
            return redirect('product_management')

        except Exception as e:
            messages.error(request, "Error creating product. Please check the form and try again.")
            categories = Category.objects.filter(is_listed=True)
            return render(request, 'admin/add_product.html', {
                'categories': categories,
                'form_data': form_data,
                'errors': errors,
            })

    categories = Category.objects.filter(is_listed=True)
    return render(request, 'admin/add_product.html', {'categories': categories})

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
            # Validation
            name = form_data['product_name']
            if not name:
                errors.append("Product name is required.")

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
            if form_data['offer']:
                try:
                    offer = Decimal(form_data['offer'])
                    if offer < 0 or offer >= price:
                        errors.append("Offer must be a positive number and less than the price.")
                except (InvalidOperation, ValueError):
                    errors.append("Offer must be a valid decimal number.")

            category_id = form_data['category']
            if not category_id:
                errors.append("Category is required.")
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

            # Update the product
            product.name = name
            product.description = description
            product.price = price
            product.offer = offer
            product.category = category
            product.save()

            messages.success(request, "Product updated successfully!")
            return redirect('product_management')

        except Exception as e:
            errors.append("Error updating product. Please check the form and try again.")
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
    variant.delete()
    return redirect('variant', product_id=variant.product.id)



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



def product_details(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # Get all variants that are in stock
    variants = product.variants.filter(stock__gt=0)
    
    # Get unique colors and sizes
    unique_colors = variants.values_list('color', flat=True).distinct()
    
    # Create a dictionary with colors as keys and their available sizes as values
    color_size_dict = {}
    for color in unique_colors:
        color_size_dict[color] = list(variants.filter(color=color).values_list('size', flat=True).distinct())

    product_images = product.images.all()  # Fetch all images related to the product
    related_products = Product.objects.filter(category=product.category).exclude(id=product_id)
    
    # Randomly select 4 related products (if there are more than 4)
    related_products = random.sample(list(related_products), min(len(related_products), 5))
    can_review = False

    if request.user.is_authenticated:
        can_review = Review.can_review(request.user, product)

    context = {
        'product': product,
        'unique_colors': unique_colors,
        'color_size_dict': json.dumps(color_size_dict),  # Convert to JSON string
        'product_images': product_images,
        'related_products': related_products,
        'can_review': can_review,
    }
    return render(request, 'product_details.html', context)


def category_products(request, category_id):
    category = get_object_or_404(Category, id=category_id, is_listed=True)
    products = Product.objects.filter(category=category, is_listed=True).prefetch_related('images')

    # Handle search
    search_query = request.GET.get('search', '')  # Get search input
    if search_query:
        products = products.filter(name__icontains=search_query)  # Search by name (case-insensitive)

    # Handle sorting
    sort_option = request.GET.get('sort', '')  # Get sort option
    if sort_option == 'name-asc':
        products = products.order_by('name')  # Sort A to Z
    elif sort_option == 'name-desc':
        products = products.order_by('-name')  # Sort Z to A
    elif sort_option == 'price-asc':  # Sort by MRP Low to High
        products = products.order_by('price')
    elif sort_option == 'price-desc':  # Sort by MRP High to Low
        products = products.order_by('-price')
    elif sort_option == 'offer-asc':  # Sort by Offer Price Low to High
        products = products.order_by('offer')
    elif sort_option == 'offer-desc':  # Sort by Offer Price High to Low
        products = products.order_by('-offer')

    # Prepare context data
    context = {
        'category': category,
        'products': [{
            'product': product,
            'first_image': product.images.first()  # Fetch the first image
        } for product in products],
        'search_query': search_query,
        'sort_option': sort_option,
    }
    return render(request, 'category_products.html', context)




def check_stock(request):
    if request.method == "POST":
        color = request.POST.get('color')
        size = request.POST.get('size')
        variants = ProductVariant.objects.filter(product__is_listed=True)
        variant_data = [{'color': variant.color, 'size': variant.size, 'stock': variant.stock} for variant in variants]
        return JsonResponse({'variants': variant_data})
    return JsonResponse({'error': 'Invalid request'}, status=400)
