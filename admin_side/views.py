from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test, login_required

# Check if the user is an admin (staff)
def is_admin(user):
    return user.is_staff

# Admin login view
def admin_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate user
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:  # Allow only staff users
            login(request, user)
            return redirect('dashboard')  # Redirect to the dashboard
        else:
            messages.error(request, "Invalid credentials or you don't have admin access.")

    return render(request, 'admin_login.html')

# Dashboard view (only accessible to logged-in admins)
@login_required(login_url='/admin-login/')
@user_passes_test(is_admin, login_url='/admin-login/')
def dashboard(request):
    return render(request, 'dashboard.html')

# Logout view
@login_required(login_url='/admin-login/')
def admin_logout(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('admin_login')
