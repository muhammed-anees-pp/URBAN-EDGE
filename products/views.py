from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Product, SizeVariant, ProductImage
from category.models import Category
from decimal import Decimal, InvalidOperation
from admin_side.views import is_admin
from django.contrib.auth.decorators import user_passes_test
from django.db.models import F
import base64
import uuid
from django.core.files.base import ContentFile
from decimal import Decimal, InvalidOperation

@user_passes_test(is_admin)
def product_list(request):
    products = Product.objects.all()
    categories = Category.objects.all()
    return render(request, 'admin/product_list.html', {
        'products': products,
        'categories': categories
    })


@user_passes_test(is_admin)
def create_product(request):
    if request.method == "POST":
        # Collect form data to preserve user input
        form_data = {
            'product_name': request.POST.get('product_name', ''),
            'description': request.POST.get('description', ''),
            'category': request.POST.get('category', ''),
            'color': request.POST.get('color', ''),
            'price': request.POST.get('price', ''),
            'offer': request.POST.get('offer', ''),
        }
        try:
            # Validate form inputs
            name = form_data['product_name']
            description = form_data['description']
            category_id = form_data['category']
            price_str = form_data['price']
            offer_str = form_data['offer']
            color = form_data['color']

            if not name:
                messages.error(request, "Product name is required.")
                raise ValueError("Validation error")

            # Check if product name already exists
            if Product.objects.filter(name=name).exists():
                messages.error(request, "A product with this name already exists.")
                raise ValueError("Validation error")

            if not description:
                messages.error(request, "Description is required.")
                raise ValueError("Validation error")

            # Check for minimum 10 characters in description
            if len(description) < 10:
                messages.error(request, "Description must be at least 10 characters long.")
                raise ValueError("Validation error")

            try:
                price = Decimal(price_str)
                if price <= 0:
                    messages.error(request, "Price must be a positive number.")
                    raise ValueError("Validation error")
            except (InvalidOperation, ValueError):
                messages.error(request, "Invalid price format.")
                raise ValueError("Validation error")

            offer = None
            if offer_str:
                try:
                    offer = Decimal(offer_str)
                    if offer < 0 or offer >= price:
                        messages.error(request, "Offer must be a positive number less than the price.")
                        raise ValueError("Validation error")
                except InvalidOperation:
                    messages.error(request, "Invalid offer format.")
                    raise ValueError("Validation error")

            # Validate category
            try:
                category = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                messages.error(request, "Selected category does not exist.")
                raise ValueError("Validation error")

            # Get the base64 images from the form
            product_images = request.POST.getlist('product_images[]')
            if not product_images:
                messages.error(request, "Please upload at least one image.")
                raise ValueError("Validation error")

            # Create the product instance
            product = Product.objects.create(
                name=name,
                description=description,
                category=category,
                color=color,
                price=price,
                offer=offer,
            )

            # Save base64 images
            for base64_image in product_images:
                # Convert base64 to file
                if ',' in base64_image:
                    # Split the base64 string if it contains the data URI prefix
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

        except ValueError:
            # Catch validation errors and re-render the form with existing data
            categories = Category.objects.filter(is_listed=True)
            return render(request, 'admin/add_product.html', {
                'categories': categories,
                'form_data': form_data
            })
        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {str(e)}")
            categories = Category.objects.filter(is_listed=True)
            return render(request, 'admin/add_product.html', {
                'categories': categories,
                'form_data': form_data
            })

    # GET request: Render the form
    categories = Category.objects.filter(is_listed=True)
    return render(request, 'admin/add_product.html', {'categories': categories})


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
        # Collect form data to retain values
        form_data = {
            'product_name': request.POST.get('product_name', product.name),
            'description': request.POST.get('description', product.description),
            'color': request.POST.get('color', product.color),
            'category': request.POST.get('category', product.category.id if product.category else ''),
            'price': request.POST.get('price', product.price),
            'offer': request.POST.get('offer', product.offer),
        }
        errors = []

        try:
            # Validate name
            name = form_data['product_name']
            if not name:
                errors.append("Product name is required.")
            elif Product.objects.filter(name__iexact=name).exclude(id=product.id).exists():
                errors.append("Product with this name already exists.")

            # Validate description
            description = form_data['description']
            if not description:
                errors.append("Description is required.")

            # Validate price
            try:
                price = Decimal(form_data['price'])
                if price <= 0:
                    errors.append("Price must be greater than zero.")
            except (InvalidOperation, ValueError):
                errors.append("Price must be a valid decimal number.")

            # Validate offer
            offer = None
            offer_str = form_data['offer']
            if offer_str:
                try:
                    offer = Decimal(offer_str)
                    if offer < 0 or offer >= price:
                        errors.append("Offer must be a positive decimal and less than the price.")
                except (InvalidOperation, ValueError):
                    errors.append("Offer must be a valid decimal number.")

            # Validate category
            category_id = form_data['category']
            category = None
            if not category_id:
                errors.append("Please select a category.")
            else:
                try:
                    category = Category.objects.get(id=category_id)
                except Category.DoesNotExist:
                    errors.append("Selected category does not exist.")

            # If errors exist, re-render the form with the existing data and errors
            if errors:
                categories = Category.objects.filter(is_listed=True)
                return render(request, 'admin/edit_product.html', {
                    'product': product,
                    'categories': categories,
                    'form_data': form_data,
                    'errors': errors,
                })

            # Update the product instance
            product.name = name
            product.description = description
            product.color = form_data['color']
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


# @user_passes_test(is_admin)
# def edit_product(request, product_id):
#     product = get_object_or_404(Product, id=product_id)

#     if request.method == "POST":
#         # Collect form data
#         form_data = {
#             'product_name': request.POST.get('product_name', product.name),
#             'description': request.POST.get('description', product.description),
#             'color': request.POST.get('color', product.color),
#             'category': request.POST.get('category', product.category.id if product.category else ''),
#             'price': request.POST.get('price', product.price),
#             'offer': request.POST.get('offer', product.offer),
#         }
#         errors = []

#         try:
#             # Validate name
#             name = form_data['product_name']
#             if not name:
#                 errors.append("Product name is required.")
#             elif Product.objects.filter(name__iexact=name).exclude(id=product.id).exists():
#                 errors.append("Product with this name already exists.")

#             # Validate description
#             description = form_data['description']
#             if not description or len(description) < 10:
#                 errors.append("Description is required and must be at least 10 characters long.")

#             # Validate price
#             try:
#                 price = Decimal(form_data['price'])
#                 if price <= 0:
#                     errors.append("Price must be greater than zero.")
#             except (InvalidOperation, ValueError):
#                 errors.append("Price must be a valid decimal number.")

#             # Validate offer
#             offer = None
#             offer_str = form_data['offer']
#             if offer_str:
#                 try:
#                     offer = Decimal(offer_str)
#                     if offer < 0 or offer >= price:
#                         errors.append("Offer must be a positive decimal and less than the price.")
#                 except (InvalidOperation, ValueError):
#                     errors.append("Offer must be a valid decimal number.")

#             # Validate category
#             category_id = form_data['category']
#             category = None
#             if not category_id:
#                 errors.append("Please select a category.")
#             else:
#                 try:
#                     category = Category.objects.get(id=category_id)
#                 except Category.DoesNotExist:
#                     errors.append("Selected category does not exist.")

#             # If errors exist, re-render the form with the existing data and errors
#             if errors:
#                 categories = Category.objects.filter(is_listed=True)
#                 product_images = ProductImage.objects.filter(product=product)
#                 return render(request, 'admin/edit_product.html', {
#                     'product': product,
#                     'categories': categories,
#                     'form_data': form_data,
#                     'product_images': product_images,
#                     'errors': errors,
#                 })

#             # Update product details
#             product.name = name
#             product.description = description
#             product.color = form_data['color']
#             product.price = price
#             product.offer = offer
#             product.category = category
#             product.save()

#             # Handle image updates
#             product_images = ProductImage.objects.filter(product=product)
#             new_images = request.POST.getlist('new_product_images[]')
#             for image in product_images:
#                 if f"remove_image_{image.id}" in request.POST:
#                     image.delete()

#             # Save new images
#             for base64_image in new_images:
#                 if ',' in base64_image:
#                     _, imgstr = base64_image.split(';base64,')
#                 else:
#                     imgstr = base64_image
#                 try:
#                     decoded_image = base64.b64decode(imgstr)
#                     image_file = ContentFile(decoded_image, name=f'product_{product.id}_{uuid.uuid4()}.jpg')
#                     ProductImage.objects.create(product=product, image=image_file)
#                 except Exception as e:
#                     errors.append(f"Error processing images: {str(e)}")
#                     break

#             if errors:
#                 categories = Category.objects.filter(is_listed=True)
#                 product_images = ProductImage.objects.filter(product=product)
#                 return render(request, 'admin/edit_product.html', {
#                     'product': product,
#                     'categories': categories,
#                     'form_data': form_data,
#                     'product_images': product_images,
#                     'errors': errors,
#                 })

#             messages.success(request, "Product updated successfully.")
#             return redirect('product_management')

#         except Exception as e:
#             errors.append(f"Error updating product: {str(e)}")
#             categories = Category.objects.filter(is_listed=True)
#             product_images = ProductImage.objects.filter(product=product)
#             return render(request, 'admin/edit_product.html', {
#                 'product': product,
#                 'categories': categories,
#                 'form_data': form_data,
#                 'product_images': product_images,
#                 'errors': errors,
#             })

#     # GET request: Render the edit product form
#     categories = Category.objects.filter(is_listed=True)
#     product_images = ProductImage.objects.filter(product=product)
#     return render(request, 'admin/edit_product.html', {
#         'product': product,
#         'categories': categories,
#         'product_images': product_images,
#     })

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