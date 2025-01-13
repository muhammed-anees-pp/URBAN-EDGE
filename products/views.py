from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Product, SIZE_CHOICES
from category.models import Category
from random import sample

# View all products (Admin view)
def product_list(request):
    products = Product.objects.all()
    return render(request, 'product_list.html', {'products': products})

# Add a product
def add_product(request):
    if request.method == 'POST':
        name = request.POST['name']
        category_id = request.POST['category']
        size = request.POST.get('size')  # Fetch predefined size
        custom_size = request.POST.get('custom_size')  # Fetch custom size
        price = request.POST['price']
        stock = request.POST['stock']
        description = request.POST['description']

        # Validate category
        category = get_object_or_404(Category, id=category_id)

        # Ensure either size or custom_size is provided
        if not size and not custom_size:
            return JsonResponse({'error': 'You must provide either a predefined size or a custom size.'}, status=400)

        # Create the product
        product = Product.objects.create(
            name=name,
            category=category,
            size=size,
            custom_size=custom_size,
            price=price,
            stock=stock,
            description=description
        )

        # Handle images
        for i in range(1, 4):
            image = request.FILES.get(f'image{i}')
            if image:
                setattr(product, f'image{i}', image)

        product.save()
        return redirect('products:product_list')

    # Render the form
    categories = Category.objects.filter(is_active=True)
    return render(request, 'add_product.html', {'categories': categories, 'size_choices': SIZE_CHOICES})

# Edit a product
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product.name = request.POST['name']
        category_id = request.POST['category']
        product.category = get_object_or_404(Category, id=category_id)
        product.size = request.POST.get('size')
        product.custom_size = request.POST.get('custom_size')
        product.price = request.POST['price']
        product.stock = request.POST['stock']
        product.description = request.POST['description']

        # Handle images
        for i in range(1, 4):
            image = request.FILES.get(f'image{i}')
            if image:
                setattr(product, f'image{i}', image)

        product.save()
        return redirect('products:product_list')

    categories = Category.objects.filter(is_active=True)
    return render(request, 'edit_product.html', {
        'product': product,
        'categories': categories,
        'size_choices': SIZE_CHOICES
    })

# Delete a product (soft delete)
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.is_active = False
    product.save()
    return redirect('products:product_list')

# User-side product and category list
# def category_with_products(request, category_id=None):
#     categories = Category.objects.filter(is_active=True)
#     selected_category = None
#     products = []

#     if category_id:
#         selected_category = get_object_or_404(Category, id=category_id, is_active=True)
#         products = selected_category.products.filter(is_active=True)
#     else:
#         all_products = Product.objects.filter(is_active=True)
#         products = sample(list(all_products), min(len(all_products), 6))

#     return render(request, 'home_product.html', {
#         'categories': categories,
#         'selected_category': selected_category,
#         'products': products
#     })
# User-side product and category list
def category_with_products(request, category_id=None):
    categories = Category.objects.filter(is_active=True)
    selected_category = None
    products = []

    if category_id:
        selected_category = get_object_or_404(Category, id=category_id, is_active=True)
        products = selected_category.products.filter(is_active=True)
    else:
        all_products = Product.objects.filter(is_active=True)
        products = sample(list(all_products), min(len(all_products), 6))

    # Add display_size attribute to each product
    for product in products:
        product.display_size = product.size if product.size else f"Custom: {product.custom_size}"

    return render(request, 'home_product.html', {
        'categories': categories,
        'selected_category': selected_category,
        'products': products,
    })
