from django.shortcuts import render
from category.models import Category
from products.models import Product
from django.utils import timezone
from datetime import timedelta

# Create your views here.
def index(request):
    categories = Category.objects.filter(is_listed=True)

    context = {
        'categories' : categories,
    }
    return render(request,'index.html',context)