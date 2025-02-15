from datetime import datetime, timedelta, timezone
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone as django_timezone
import random
import re
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from user_profile.models import Referral
from wallet.models import Wallet, WalletTransaction


def generate_otp():
    """Generate a random 4-digit OTP."""
    return random.randint(1000, 9999)

def send_otp_email(email, otp):
    """Send OTP email to the user."""
    subject = "Your OTP Code"
    message = f"Your OTP code is: {otp}"
    try:
        send_mail(subject, message, "your_email@gmail.com", [email])
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

    form_data = {}  # To retain user input on error
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        form_data['username'] = username

        if not username or not password:
            messages.error(request, 'Please enter both username and password.')
            return render(request, 'login.html', {'form_data': form_data})

        user = authenticate(request, username=username, password=password)
        if user:
            # Specify the backend explicitly (optional, as authenticate already handles this)
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            # messages.success(request, 'Successfully logged in.')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
            return render(request, 'login.html', {'form_data': form_data})

    return render(request, 'login.html', {'form_data': form_data})



def user_logout(request):
    """Logout user."""
    logout(request)
    # messages.success(request, 'Successfully logged out.')
    return redirect('home')


def register(request):
    """User registration with OTP and referral code."""
    if request.user.is_authenticated:
        return redirect('home')

    form_data = {}  # To retain user input on error
    if request.method == 'POST':
        username = request.POST.get('username').strip()
        first_name = request.POST.get('first_name').strip()
        last_name = request.POST.get('last_name').strip()
        email = request.POST.get('email').strip()
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        referral_code = request.POST.get('referral_code', '').strip()  # Get referral code

        form_data = {
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'referral_code': referral_code,
        }

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
                messages.error(request, error)
            return render(request, 'register.html', {'form_data': form_data})

        # Validate referral code
        referred_by = None
        if referral_code:
            try:
                referral = Referral.objects.get(referral_code=referral_code)
                referred_by = referral.user
            except Referral.DoesNotExist:
                messages.error(request, "Invalid referral code.")
                return render(request, 'register.html', {'form_data': form_data})

        otp = generate_otp()
        expires_at = django_timezone.now() + timedelta(minutes=1)

        # Store OTP and user information in session
        request.session['otp'] = otp
        request.session['otp_expires_at'] = int(expires_at.timestamp())
        request.session['username'] = username
        request.session['email'] = email
        request.session['password'] = password
        request.session['first_name'] = first_name
        request.session['last_name'] = last_name
        request.session['referral_code'] = referral_code  # Store referral code in session

        if not send_otp_email(email, otp):
            messages.error(request, "Failed to send OTP email. Please try again.")
            return render(request, 'register.html', {'form_data': form_data})

        return redirect('verify_otp')

    return render(request, 'register.html', {'form_data': form_data})


def verify_otp(request):
    """Verify OTP and complete registration."""
    email = request.session.get('email')

    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        otp = request.session.get('otp')
        otp_expires_at = request.session.get('otp_expires_at')

        if not otp:
            return render(request, 'verify_otp.html', {'error': 'OTP not found.', 'email': email})

        try:
            otp_expires_at = datetime.fromtimestamp(otp_expires_at, tz=timezone.utc)
        except ValueError:
            return render(request, 'verify_otp.html', {'error': 'Invalid OTP expiration format.', 'email': email})

        if django_timezone.now() > otp_expires_at:
            return render(request, 'verify_otp.html', {'error': 'OTP has expired.', 'email': email})

        if str(otp) == entered_otp:
            # Proceed with registration
            username = request.session['username']
            password = request.session['password']
            first_name = request.session['first_name']
            last_name = request.session['last_name']
            referral_code = request.session.get('referral_code')  # Get referral code from session

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            # Create a referral entry for the new user
            Referral.objects.create(user=user)

            # Handle referral code
            if referral_code:
                try:
                    referral = Referral.objects.get(referral_code=referral_code)
                    referred_by = referral.user
                    Referral.objects.filter(user=user).update(referred_by=referred_by)

                    # Credit ₹50 to the new user's wallet
                    wallet, _ = Wallet.objects.get_or_create(user=user)
                    wallet.balance += 50
                    wallet.save()
                    WalletTransaction.objects.create(
                        wallet=wallet,
                        amount=50,
                        transaction_type='credit',
                        description='Referral bonus for new user'  # Add description
                    )

                    # Credit ₹100 to the referred user's wallet
                    referred_wallet, _ = Wallet.objects.get_or_create(user=referred_by)
                    referred_wallet.balance += 100
                    referred_wallet.save()
                    WalletTransaction.objects.create(
                        wallet=referred_wallet,
                        amount=100,
                        transaction_type='credit',
                        description='Referral bonus for referring user'  # Add description
                    )
                except Referral.DoesNotExist:
                    pass  # Invalid referral code, ignore

            # Clear session data
            for key in ['otp', 'otp_expires_at', 'username', 'email', 'password', 'first_name', 'last_name', 'referral_code']:
                request.session.pop(key, None)

            # Log in the user
            user.backend = 'django.contrib.auth.backends.ModelBackend'  # Use the appropriate backend
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
