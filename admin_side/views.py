# from django.contrib.auth import authenticate, login, logout
# from django.shortcuts import render, redirect
# from django.contrib import messages
# from django.contrib.auth.decorators import user_passes_test, login_required

# # Check if the user is an admin (staff)
# def is_admin(user):
#     return user.is_staff

# # Admin login view
# def admin_login(request):
#     if request.method == "POST":
#         username = request.POST.get('username')
#         password = request.POST.get('password')

#         # Authenticate user
#         user = authenticate(request, username=username, password=password)

#         if user is not None and user.is_staff:  # Allow only staff users
#             login(request, user)
#             return redirect('dashboard')  # Redirect to the dashboard
#         else:
#             messages.error(request, "Invalid credentials or you don't have admin access.")

#     return render(request, 'admin_login.html')

# # Dashboard view (only accessible to logged-in admins)
# @login_required(login_url='/admin-login/')
# @user_passes_test(is_admin, login_url='/admin-login/')
# def dashboard(request):
#     return render(request, 'dashboard.html')

# # Logout view
# @login_required(login_url='/admin-login/')
# def admin_logout(request):
#     logout(request)
#     messages.success(request, "You have been logged out successfully.")
#     return redirect('admin_login')

from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test,login_required
from django.contrib import messages



def is_admin(user):
    return user.is_staff


def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid credentials or not an admin user.')

    return render(request, 'admin/admin_login.html')


@user_passes_test(is_admin)
@login_required(login_url='admin_login')
def admin_dashboard(request):
    return render(request, 'admin/dashboard.html')

@user_passes_test(is_admin)
def user_manage(request):
    users = User.objects.filter(is_superuser=False).order_by('-date_joined')

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