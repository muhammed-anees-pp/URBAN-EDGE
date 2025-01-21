from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Product, SizeVariant
from category.models import Category
from decimal import Decimal, InvalidOperation
from admin_side.views import is_admin
from django.contrib.auth.decorators import user_passes_test
from django.db.models import F

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
        try:
            # Get form data
            name = request.POST.get('product_name', '')
            description = request.POST.get('description', '')
            category_id = request.POST.get('category', '')
            color = request.POST.get('color', '')
            price_str = request.POST.get('price', '')
            offer_str = request.POST.get('offer', '')

            # Preserve form data to re-populate fields
            form_data = {
                'product_name': name,
                'description': description,
                'category': category_id,
                'color': color,
                'price': price_str,
                'offer': offer_str,
            }

            # Validate name and description
            if not name:
                messages.error(request, "Product name is required")
                return render(request, 'admin/add_product.html', {'categories': Category.objects.all(), 'form_data': form_data})
            if Product.objects.filter(name__iexact=name).exists():
                messages.error(request, "Product already exists!")
                return render(request, 'admin/add_product.html', {'categories': Category.objects.all(), 'form_data': form_data})
            if not description or len(description) < 10:
                messages.error(request, "Description must be at least 10 characters long.")
                return render(request, 'admin/add_product.html', {'categories': Category.objects.all(), 'form_data': form_data})

            # Ensure valid price
            try:
                price = Decimal(price_str) if price_str else None
                if price is None or price <= 0:
                    messages.error(request, "Please provide a valid price greater than 0.")
                    return render(request, 'admin/add_product.html', {'categories': Category.objects.all(), 'form_data': form_data})
            except InvalidOperation:
                messages.error(request, "Price must be a valid decimal number.")
                return render(request, 'admin/add_product.html', {'categories': Category.objects.all(), 'form_data': form_data})

            # Ensure valid offer, if provided
            offer = None
            if offer_str:
                try:
                    offer = Decimal(offer_str)
                    if offer < 0 or offer >= price:
                        messages.error(request, "Offer must be a positive decimal and less than the price.")
                        return render(request, 'admin/add_product.html', {'categories': Category.objects.all(), 'form_data': form_data})
                except InvalidOperation:
                    messages.error(request, "Offer must be a valid decimal number.")
                    return render(request, 'admin/add_product.html', {'categories': Category.objects.all(), 'form_data': form_data})

            # Validate category selection
            if not category_id:
                messages.error(request, "Please select a category.")
                return render(request, 'admin/add_product.html', {'categories': Category.objects.all(), 'form_data': form_data})

            # Check if the selected category exists
            try:
                category = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                messages.error(request, "Selected category does not exist.")
                return render(request, 'admin/add_product.html', {'categories': Category.objects.all(), 'form_data': form_data})

            # Handle image uploads and validate file types
            image1 = request.FILES.get('image1')
            image2 = request.FILES.get('image2')
            image3 = request.FILES.get('image3')

            # Check if at least one image is uploaded
            if not image1:
                messages.error(request, "Please upload at least the first image.")
                return render(request, 'admin/add_product.html', {'categories': Category.objects.all(), 'form_data': form_data})

            # Image format validation
            for image in [image1, image2, image3]:
                if image and not image.name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    messages.error(request, "Only PNG, JPG, JPEG, and WEBP image files are allowed.")
                    return render(request, 'admin/add_product.html', {'categories': Category.objects.all(), 'form_data': form_data})

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
            return render(request, 'admin/add_product.html', {'categories': Category.objects.all(), 'form_data': form_data})

    # GET request - show the form
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