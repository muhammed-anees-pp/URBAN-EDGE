from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Category
from django.utils import timezone
from admin_side.views import is_admin
from django.contrib.auth.decorators import user_passes_test

@user_passes_test(is_admin)
def category_management(request):
    if request.method == 'POST':
        category_name = request.POST.get('category_name')
        category_image = request.FILES.get('image')

        if not category_name:
            error_message = "Category name is required!"
        elif Category.objects.filter(category_name__iexact=category_name).exists():
            error_message = "Category already exists!"
        else:
            Category.objects.create(
                category_name=category_name,
                created_at=timezone.now(),
                image=category_image
            )
            messages.success(request, "Category created successfully!")
            return redirect('category_management')

        # Return the modal with the error message
        categories = Category.objects.all()
        return render(request, 'admin/category.html', {
            'categories': categories,
            'form_data': {'category_name': category_name},
            'error_message': error_message
        })

    categories = Category.objects.all()
    return render(request, 'admin/category.html', {'categories': categories})

@user_passes_test(is_admin)
def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    if request.method == 'POST':
        category_name = request.POST.get('category_name')
        category_image = request.FILES.get('image')

        if not category_name:
            messages.error(request, "Category name is required!")
        elif Category.objects.filter(category_name__iexact=category_name).exclude(id=category.id).exists():
            messages.error(request, "Category with this name already exists!")
        else:
            category.category_name = category_name
            if category_image:
                category.image = category_image
            category.save()
            messages.success(request, "Category updated successfully!")
            return redirect('category_management')

    return render(request, 'admin/edit_category.html', {'category': category})


@user_passes_test(is_admin)
def toggle_listing(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    category.is_listed = not category.is_listed
    category.save()
    messages.success(request, f"Category {'unlisted' if not category.is_listed else 'relisted'} successfully!")
    return redirect('category_management')
