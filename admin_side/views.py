from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test,login_required
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger  # Import Paginator



def is_admin(user):
    return user.is_staff

@never_cache
def admin_login(request):
    form_data = {'username': ''}  # Initialize form data

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        form_data['username'] = username  # Retain username in form data

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid credentials or not an admin user.')

    return render(request, 'admin/admin_login.html', {'form_data': form_data})



@user_passes_test(is_admin)
@login_required(login_url='admin_login')
def admin_dashboard(request):
    return render(request, 'admin/dashboard.html')

@user_passes_test(is_admin)
def user_manage(request):
    users = User.objects.filter(is_superuser=False).order_by('-date_joined')

    # Pagination
    page = request.GET.get('page', 1)  # Get the page number from the URL parameters
    paginator = Paginator(users, 10)  # Show 10 products per page

    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)


    return render(request,'admin/users.html',{'users':users})

@user_passes_test(is_admin)
def block_user(request,user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = False
    user.save()
    messages.success(request, f'{user.username} has been blocked.')
    return redirect('users')

@user_passes_test(is_admin)
def unblock_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = True
    user.save()
    messages.success(request, f'{user.username} has been unblocked.')
    return redirect('users')

@login_required(login_url='admin_login')
def admin_logout(request):
    logout(request)
    return redirect('admin_login')