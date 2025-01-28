from django.shortcuts import render, HttpResponse
from productsapp.models import Product, ProductImage
from category.models import Category

def all_products(request):
    # Get all listed products and categories
    products = Product.objects.filter(is_listed=True).prefetch_related('images')
    categories = Category.objects.filter(is_listed=True)

    # Handle search query
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(name__icontains=search_query)

    # Handle category filtering
    selected_categories = request.GET.getlist('categories')  # Retrieve list of selected category IDs
    if selected_categories:
        products = products.filter(category__id__in=selected_categories)

    # Handle sorting
    sort_option = request.GET.get('sort', '')
    if sort_option == 'name-asc':
        products = products.order_by('name')
    elif sort_option == 'name-desc':
        products = products.order_by('-name')
    elif sort_option == 'offer-asc':
        products = products.order_by('offer')
    elif sort_option == 'offer-desc':
        products = products.order_by('-offer')

    # Prepare context data
    context = {
        'products': [{
            'product': product,
            'first_image': product.images.first()  # Fetch the first image
        } for product in products],
        'categories': categories,
        'selected_categories': [int(cat) for cat in selected_categories],
        'search_query': search_query,
        'sort_option': sort_option,
    }

    return render(request, 'user/all_products.html', context)
