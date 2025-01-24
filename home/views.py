# from django.shortcuts import render
# from category.models import Category
# from products.models import Product
# from django.utils import timezone
# from datetime import timedelta

# # Create your views here.
# def index(request):
#     categories = Category.objects.filter(is_listed=True)

#     context = {
#         'categories' : categories,
#     }
#     return render(request,'home.html',context)

from django.shortcuts import render
from category.models import Category
from products.models import Product
import random

# Home View
def index(request):
    # Get the listed categories
    categories = Category.objects.filter(is_listed=True)

    # Fetch the latest 4 products (based on created date or any other criteria)
    latest_products = Product.objects.filter(is_listed=True).order_by('-created_at')[:4]  # Adjust 'created_at' based on your model fields

    # Randomly shuffle the products to show them in random order
    random_products = random.sample(list(latest_products), len(latest_products))

    context = {
        'categories': categories,
        'random_products': random_products,  # Add the random products to the context
    }
    return render(request, 'home.html', context)

