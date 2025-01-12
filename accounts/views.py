from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.hashers import make_password  # Add this import
from django.contrib import messages
from django.contrib.auth.models import User
from .models import User_Details
from home.views import home

def signup(request):
    if request.method == "POST":
        # Get form data
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        # Validation
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("signup")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("signup")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect("signup")

        # Create User instance
        user = User.objects.create(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=make_password(password),  # Use make_password to hash the password
        )

        # Create User_Details instance
        User_Details.objects.create(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            password=make_password(password),  # Hash the password for User_Details as well
            user=user,
        )

        messages.success(request, "Account created successfully! Please log in.")
        return redirect("login")
    return render(request, "signup.html")


def login(request):
    if request.method == 'POST':
        email_or_username = request.POST.get('email')  # Capture either username or email
        password = request.POST.get('password')

        # Try to find the user by email or username
        if '@' in email_or_username:  # If it's an email
            try:
                user = User.objects.get(email=email_or_username)  # Get user by email
            except User.DoesNotExist:
                user = None
        else:  # Otherwise, treat it as a username
            try:
                user = User.objects.get(username=email_or_username)  # Get user by username
            except User.DoesNotExist:
                user = None

        # Authenticate the user with password if the user exists
        if user and user.check_password(password):
            auth_login(request, user)  # Log the user in
            messages.success(request, "Login successful!")
            return redirect('home')  # Redirect to home or any other page
        else:
            messages.error(request, "Invalid username/email or password.")
            return redirect('login')

    return render(request, 'login.html')


