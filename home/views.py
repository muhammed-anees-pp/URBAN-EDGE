from django.shortcuts import render
# from products.models import Category
from django.contrib.auth.models import User
# Create your views here.
def home(request):
    # if request.user.is_authenticated and request.user.user_details.is_active:
        # category=Category.objects.all()
        # return render(request,'landingpage.html',{'category':category})
        return render(request,'landing.html')
    # return render (request,'login.html')