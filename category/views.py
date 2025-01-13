from django.shortcuts import render, redirect, get_object_or_404
from . models import Category

# List Categories
def category_list(request):
    # Fetch only active categories
    categories = Category.objects.filter(is_active=True)
    return render(request, 'category_list.html', {'categories': categories})

# Add Category
def add_category(request):
    if request.method == 'POST':
        # Retrieve form data
        category_name = request.POST.get('category')
        description = request.POST.get('description')
        category_image = request.FILES.get('image')  # Get the uploaded image

        # Save the new category
        if category_name:
            # Create a new category with image
            Category.objects.create(
                name=category_name,
                description=description,
                image=category_image,
                is_active=True
            )
            print(f"Category '{category_name}' added with description: {description}")
            return redirect('category_list')  # Adjust the redirect URL as needed
        else:
            return render(request, 'add_category.html', {
                'error_message': 'Category name is required.'
            })

    return render(request, 'add_category.html')

# Edit Category
def edit_category(request, pk):
    category = get_object_or_404(Category, pk=pk)  # Retrieve the category object by primary key

    if request.method == 'POST':
        # Retrieve form data
        category_name = request.POST.get('name')
        category_description = request.POST.get('description')

        if not category_name:
            return render(request, 'edit_category.html', {
                'category': category,
                'error_message': 'Category name is required.'
            })

        # Update category fields and save
        category.name = category_name
        category.description = category_description
        category.save()

        return redirect('category_list')  # Adjust redirect URL as per your app's structure

    return render(request, 'edit_category.html', {'category': category})
# Soft Delete Category
def delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    category.is_active = False  # Soft delete
    category.save()
    return redirect('category_list')