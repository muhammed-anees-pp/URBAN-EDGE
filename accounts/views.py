from datetime import datetime
from django.utils.timezone import make_aware
from django.core.mail import send_mail
from random import randint
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.utils.timezone import now, timedelta
from .models import User_Details
from django.conf import settings


def user_signup(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        # Validate password match
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("user_signup")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("user_signup")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect("user_signup")

        # Store user data temporarily in session for later creation
        request.session['user_data'] = {
            'first_name': first_name,
            'last_name': last_name,
            'username': username,
            'email': email,
            'password': make_password(password),
        }

        # Generate and send OTP
        return send_otp(request, email)

    return render(request, "signup.html")


def send_otp(request, email):
    otp = randint(1000, 9999)
    request.session['otp'] = otp  # Store OTP in session
    request.session['otp_expiry'] = (now() + timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S")  # Expiry time
    request.session['otp_email'] = email  # Store email for display

    # Send OTP to email
    send_mail(
        'Your OTP Code',
        f'Your OTP code is {otp}',
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )

    messages.info(request, f"Please verify your email within 1 minute to proceed with the process.")
    return redirect("otp_verification")




def otp_verification(request):
    if request.method == "POST":
        otp = request.POST.get("otp")
        session_otp = request.session.get("otp")
        otp_expiry = request.session.get("otp_expiry")

        # Check if OTP has expired
        otp_expiry_time = datetime.strptime(otp_expiry, "%Y-%m-%d %H:%M:%S")
        
        # Make the expiry time aware by attaching the current timezone
        otp_expiry_time = make_aware(otp_expiry_time)

        # Compare with the current time (aware datetime)
        if now() > otp_expiry_time:
            messages.error(request, "The OTP has expired. Please request a new OTP.")
            return redirect("otp_verification")

        # Check if OTP matches
        if otp == str(session_otp):
            # Retrieve user data from session
            user_data = request.session.get("user_data")

            if not user_data:
                messages.error(request, "Session expired. Please sign up again.")
                return redirect("user_signup")

            # Create User instance
            user = User.objects.create(
                username=user_data['username'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                email=user_data['email'],
                password=user_data['password'],  # Already hashed during signup
                is_active=True,
            )

            # Create User_Details instance
            User_Details.objects.create(
                first_name=user.first_name,
                last_name=user.last_name,
                username=user.username,
                email=user.email,
                password=user.password,
                user=user,
            )

            # Clear session data
            request.session.flush()

            messages.success(request, "Account activated! You can now log in.")
            return redirect("user_login")
        else:
            messages.error(request, "Invalid OTP. Please try again.")

    email = request.session.get("otp_email", "")
    return render(request, "otp_verification.html", {"email": email})



def resend_otp(request):
    email = request.session.get("otp_email")
    if not email:
        messages.error(request, "Session expired. Please sign up again.")
        return redirect("user_signup")

    return send_otp(request, email)


def user_login(request):
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
            return redirect('user_login')

    return render(request, 'login.html')


def user_logout(request):
    auth_logout(request)
    messages.success(request, "You have logged out successfully.")
    return redirect('user_login')  # Redirect to login after logout
