# from django.shortcuts import render, redirect, get_object_or_404
# from . models import Category

# # List Categories
# def category_list(request):
#     # Fetch only active categories
#     categories = Category.objects.filter(is_active=True)
#     return render(request, 'category_list.html', {'categories': categories})

# # Add Category
# def add_category(request):
#     if request.method == 'POST':
#         # Retrieve form data
#         category_name = request.POST.get('category')
#         description = request.POST.get('description')
#         category_image = request.FILES.get('image')  # Get the uploaded image

#         # Save the new category
#         if category_name:
#             # Create a new category with image
#             Category.objects.create(
#                 name=category_name,
#                 description=description,
#                 image=category_image,
#                 is_active=True
#             )
#             print(f"Category '{category_name}' added with description: {description}")
#             return redirect('category_list')  # Adjust the redirect URL as needed
#         else:
#             return render(request, 'add_category.html', {
#                 'error_message': 'Category name is required.'
#             })

#     return render(request, 'add_category.html')

# # Edit Category
# def edit_category(request, pk):
#     category = get_object_or_404(Category, pk=pk)  # Retrieve the category object by primary key

#     if request.method == 'POST':
#         # Retrieve form data
#         category_name = request.POST.get('name')
#         category_description = request.POST.get('description')

#         if not category_name:
#             return render(request, 'edit_category.html', {
#                 'category': category,
#                 'error_message': 'Category name is required.'
#             })

#         # Update category fields and save
#         category.name = category_name
#         category.description = category_description
#         category.save()

#         return redirect('category_list')  # Adjust redirect URL as per your app's structure

#     return render(request, 'edit_category.html', {'category': category})
# # Soft Delete Category
# def delete_category(request, pk):
#     category = get_object_or_404(Category, pk=pk)
#     category.is_active = False  # Soft delete
#     category.save()
#     return redirect('category_list')

from django.shortcuts import render,redirect,get_object_or_404
from django.contrib import messages
from .models import Category
from django.utils import timezone
from admin_side.views import is_admin 
from django.contrib.auth.decorators import user_passes_test

# Create your views here.
@user_passes_test(is_admin)
def category_management(request):
    if request.method == 'POST':
        category_name = request.POST.get('category_name')
        category_image = request.FILES.get('image')  

        if not category_name:
            messages.error(request, "Category name is required!")
        else:
            if Category.objects.filter(category_name__iexact=category_name).exists():
                messages.error(request, "Category already exists!")
            else:
                Category.objects.create(
                    category_name=category_name,
                    created_at=timezone.now(),
                    image=category_image  
                )
                messages.success(request, "Category created successfully!")
                return redirect(category_management)

    categories = Category.objects.all()
    return render(request, 'admin/category.html', {'categories': categories})


@user_passes_test(is_admin)
def edit_category(request,category_id):
    category = get_object_or_404(Category,id=category_id)

    if request.method == 'POST':
        category_name = request.POST.get('category_name')
        if category_name:
            category.category_name = category_name
            category.save()
            messages.success(request, "Category updated successfully!")
        else:
            messages.error(request, "Category name cannot be empty!")
        return redirect('category_management')
    
    return render(request,'admin/edit_category.html',{'category' : category})

@user_passes_test(is_admin)
def toggle_listing(request,category_id):
    category = get_object_or_404(Category,id=category_id)
    category.is_listed = not category.is_listed
    category.save()
    messages.success(request, f"Category {'unlisted' if not category.is_listed else 'relisted'} successfully!")
    return redirect('category_management')