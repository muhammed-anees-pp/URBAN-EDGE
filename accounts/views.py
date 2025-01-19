from datetime import datetime, timedelta, timezone  # Use timezone from the datetime module for UTC
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone as django_timezone  # Use Django's timezone utility for time zone aware datetimes
import random
import re
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.utils.timezone import make_aware

def generate_otp():
    """Generate a random 4-digit OTP."""
    return random.randint(1000, 9999)

def send_otp_email(email, otp):
    """Send OTP to the user's email."""
    subject = 'Your OTP Code'
    message = f'Your OTP code is: {otp}'
    try:
        send_mail(subject, message, 'your_email@gmail.com', [email])
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def validate_password(password):
    """Validate password strength."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."
    return True, ""

def user_login(request):
    """Login user."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            messages.error(request, 'Please enter both username and password.')
            return render(request, 'login.html', {'username': username})

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, 'Successfully logged in.')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
            return render(request, 'login.html', {'username': username})

    return render(request, 'login.html')


def user_logout(request):
    """Logout user."""
    logout(request)
    messages.success(request, 'Successfully logged out.')
    return redirect('home')


def register(request):
    """User registration with OTP"""
    if request.user.is_authenticated:
        return redirect('userlogin')

    if request.method == 'POST':
        username = request.POST.get('username').strip()
        first_name = request.POST.get('first_name').strip()
        last_name = request.POST.get('last_name').strip()
        email = request.POST.get('email').strip()
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        errors = {}

        # Check if the username or email already exists
        if User.objects.filter(username=username).exists():
            errors['username'] = "Username already exists. Please choose a different one."
        
        if User.objects.filter(email=email).exists():
            errors['email'] = "Email is already registered. Please use a different email."

        if password != confirm_password:
            errors['password'] = "Passwords do not match."

        if errors:
            for error in errors.values():
                messages.error(request, error)  # Add error message to messages framework
            return render(request, 'register.html')

        otp = generate_otp()
        expires_at = django_timezone.now() + timedelta(minutes=1)

        # Store OTP and user information in session
        request.session['otp'] = otp
        request.session['otp_expires_at'] = int(expires_at.timestamp())  # Convert datetime to timestamp
        request.session['username'] = username  # Store username in session
        request.session['email'] = email  # Store email in session
        request.session['password'] = password  # Store password in session

        if not send_otp_email(email, otp):
            messages.error(request, "Failed to send OTP email. Please try again.")  # Add error message
            return render(request, 'register.html')

        messages.success(request, "OTP sent successfully! Please verify your email.")  # Success message
        return redirect('verify_otp')

    return render(request, 'register.html')


def verify_otp(request):
    """Verify OTP"""
    email = request.session.get('email')  # Retrieve the email from the session

    if request.method == 'POST':
        entered_otp = request.POST.get('otp')

        otp = request.session.get('otp')
        otp_expires_at = request.session.get('otp_expires_at')

        if not otp:
            return render(request, 'verify_otp.html', {'error': 'OTP not found.', 'email': email})

        try:
            # Convert expiry timestamp back to a timezone-aware datetime
            otp_expires_at = datetime.fromtimestamp(otp_expires_at, tz=timezone.utc)
        except ValueError:
            return render(request, 'verify_otp.html', {'error': 'Invalid OTP expiration format.', 'email': email})

        # Check OTP expiry
        if django_timezone.now() > otp_expires_at:
            return render(request, 'verify_otp.html', {'error': 'OTP has expired.', 'email': email})

        if str(otp) == entered_otp:
            # Proceed with registration (create user, etc.)
            username = request.session['username']
            password = request.session['password']

            user = User.objects.create_user(username=username, email=email, password=password)
            del request.session['otp']  # Clear OTP from session
            del request.session['otp_expires_at']  # Clear expiration
            del request.session['username']  # Clear username from session
            del request.session['email']  # Clear email from session
            del request.session['password']  # Clear password from session

            login(request, user)
            return redirect('home')
        else:
            return render(request, 'verify_otp.html', {'error': 'Invalid OTP. Please try again.', 'email': email})

    return render(request, 'verify_otp.html', {'email': email})


def resend_otp(request):
    """Resend OTP functionality"""
    if request.method == 'POST':
        otp = request.session.get('otp')
        otp_expires_at = request.session.get('otp_expires_at')

        # Check if the OTP is still valid
        if otp and django_timezone.now() < django_timezone.make_aware(datetime.fromtimestamp(otp_expires_at)):
            # Calculate time remaining for the OTP to expire
            time_remaining = (django_timezone.make_aware(datetime.fromtimestamp(otp_expires_at)) - django_timezone.now()).seconds
            return JsonResponse({'success': False, 'message': f"Please wait {time_remaining} seconds before requesting a new OTP."})

        # Send new OTP if expired or not present
        new_otp = generate_otp()
        expires_at = django_timezone.now() + timedelta(minutes=1)
        request.session['otp'] = new_otp
        request.session['otp_expires_at'] = int(expires_at.timestamp())  # Store as timestamp

        if send_otp_email(request.session['email'], new_otp):
            return JsonResponse({'success': True, 'message': 'New OTP sent successfully!'})
        else:
            return JsonResponse({'success': False, 'message': 'Failed to send OTP. Please try again.'})



def forgot_password(request):
    """Handle forgot password logic."""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            otp = generate_otp()
            expires_at = django_timezone.now() + timedelta(minutes=1)

            # Store OTP and expiry as timestamps in session
            request.session['password_reset_otp'] = otp
            request.session['password_reset_expires_at'] = int(expires_at.timestamp())  # Store as timestamp
            request.session['reset_email'] = email  # Store email in session

            if send_otp_email(email, otp):
                messages.success(request, 'OTP sent successfully to your email.')
                return redirect('verify_forgot_password_otp')
            else:
                messages.error(request, 'Failed to send OTP. Please try again.')
        except User.DoesNotExist:
            messages.error(request, 'Email not found.')
            return redirect('forgot_password')

    return render(request, 'forgot_password.html')


def verify_forgot_password_otp(request):
    """Verify OTP for password reset."""
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')

        otp = request.session.get('password_reset_otp')
        otp_expires_at = request.session.get('password_reset_expires_at')

        if not otp or not otp_expires_at:
            messages.error(request, 'OTP not found or expired.')
            return redirect('forgot_password')

        try:
            # Convert expiry timestamp back to a timezone-aware datetime
            otp_expires_at = datetime.fromtimestamp(otp_expires_at, tz=timezone.utc)  # Correct timezone usage
        except ValueError:
            messages.error(request, 'Invalid OTP expiration format.')
            return redirect('forgot_password')

        if django_timezone.now() > otp_expires_at:
            messages.error(request, 'OTP has expired.')
            return redirect('forgot_password')

        if str(otp) == entered_otp:
            messages.success(request, 'OTP verified successfully.')
            return redirect('reset_password')
        else:
            messages.error(request, 'Invalid OTP.')
            return redirect('verify_forgot_password_otp')

    return render(request, 'verify_forgot_password_otp.html')


# def resend_forgot_password_otp(request):
#     """Resend OTP for forgot password."""
#     if request.method == 'POST':
#         otp_expires_at = request.session.get('password_reset_expires_at')

#         # Check if the OTP is still valid
#         if otp_expires_at:
#             otp_expires_at = datetime.fromtimestamp(otp_expires_at, tz=timezone.utc)
#             if django_timezone.now() < otp_expires_at:
#                 # OTP is still valid, show the time remaining to the user
#                 time_remaining = (otp_expires_at - django_timezone.now()).seconds
#                 messages.error(request, f'Please wait {time_remaining} seconds before requesting a new OTP.')
#                 return redirect('verify_forgot_password_otp')

#         # Generate a new OTP if expired or not present
#         otp = generate_otp()
#         expires_at = django_timezone.now() + timedelta(minutes=1)
#         request.session['password_reset_otp'] = otp
#         request.session['password_reset_expires_at'] = int(expires_at.timestamp())  # Store as timestamp

#         email = request.session.get('reset_email')
#         if email:
#             # Send the OTP to the email
#             if send_otp_email(email, otp):
#                 messages.success(request, 'A new OTP has been sent to your email.')
#             else:
#                 messages.error(request, 'Failed to send OTP. Please try again.')
#         else:
#             messages.error(request, 'Email not found in session.')

#         return redirect('verify_forgot_password_otp')

#     # For GET requests, simply redirect to the OTP verification page
#     return redirect('verify_forgot_password_otp')



def reset_password(request):
    """Reset password after OTP verification."""
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('reset_password')

        email = request.session.get('reset_email')
        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            messages.success(request, 'Password reset successfully. Please log in.')
            return redirect('userlogin')
        except User.DoesNotExist:
            messages.error(request, 'User not found. Please try again.')
            return redirect('forgot_password')

    return render(request, 'reset_password.html')
