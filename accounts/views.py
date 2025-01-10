from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
from .models import User
from .forms import SignupForm, LoginForm
import random
from django.contrib.auth.hashers import make_password
from django.contrib import messages  # Import the messages module

otp_storage = {}  # Temporary OTP storage for demonstration purposes.
user_storage = {}  # Temporary user storage before OTP verification.

def signup(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            username = form.cleaned_data['username']

            # Check if the email is already registered
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email is already registered.')
                return render(request, 'signup.html', {'form': form})

            # Check if the username is already taken
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username is already taken.')
                return render(request, 'signup.html', {'form': form})

            # Temporarily store user data before OTP verification
            user_data = {
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
                'username': username,
                'email': email,
                'password': form.cleaned_data['password'],
            }
            # Store user data temporarily in user_storage
            otp_storage[email] = None
            user_storage[email] = user_data

            # Generate and send OTP
            otp = random.randint(1000, 9999)
            otp_storage[email] = otp
            send_mail(
                'Your OTP for Verification',
                f'Your OTP is: {otp}',
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
            messages.success(request, 'OTP sent successfully! Please verify your email.')
            return redirect('verify_email', email=email)
        else:
            # Add form validation errors to messages (corrected line)
            for field in form.errors.values():
                for error in field:
                    messages.error(request, error)

    else:
        form = SignupForm()

    return render(request, 'signup.html', {'form': form})


def verify_email(request, email):
    if request.method == "POST":
        # Combine OTP inputs from the form
        otp = ''.join([request.POST.get(f'otp{i}') for i in range(1, 5)])
        correct_otp = otp_storage.get(email)  # Retrieve OTP from storage

        if otp and otp == str(correct_otp):  # Validate OTP
            # Process verified user creation
            user_data = user_storage.pop(email, None)
            if user_data:
                user = User(
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    username=user_data['username'],
                    email=user_data['email'],
                    is_verified=True,
                )
                user.set_password(user_data['password'])  # Hash the password
                user.save()
                otp_storage.pop(email, None)
                messages.success(request, 'Account created successfully! You can now log in.')
                return redirect('login')
        else:
            messages.error(request, 'Invalid or expired OTP.')

    # Render the template with the email address
    return render(request, 'verify_email.html', {'email': email})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            try:
                user = User.objects.get(username=username)
                if user.is_verified and user.check_password(password):  # Use check_password to verify the password
                    # For simplicity, store user ID in session
                    request.session['user_id'] = user.id
                    messages.success(request, 'Logged in successfully!')
                    return redirect('home')
                else:
                    messages.error(request, 'Invalid credentials or account not verified.')
                    return render(request, 'login.html', {'form': form})
            except User.DoesNotExist:
                messages.error(request, 'Invalid credentials.')
                return render(request, 'login.html', {'form': form})
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def home(request):
    if 'user_id' in request.session:
        user = User.objects.get(id=request.session['user_id'])
        return render(request, 'home.html', {'user': user})
    else:
        messages.info(request, 'Please log in to access your account.')
        return redirect('login')
