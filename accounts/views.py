# # from django.shortcuts import render, redirect
# # from django.core.mail import send_mail
# # from django.conf import settings
# # from .models import User
# # from .forms import SignupForm, LoginForm
# # import random
# # from django.contrib.auth.hashers import make_password

# # otp_storage = {}  # Temporary OTP storage for demonstration purposes.
# # user_storage = {}  # Temporary user storage before OTP verification.

# # def signup(request):
# #     if request.method == "POST":
# #         form = SignupForm(request.POST)
# #         if form.is_valid():
# #             # Temporarily store user data before OTP verification
# #             user_data = {
# #                 'first_name': form.cleaned_data['first_name'],
# #                 'last_name': form.cleaned_data['last_name'],
# #                 'username': form.cleaned_data['username'],
# #                 'email': form.cleaned_data['email'],
# #                 'password': form.cleaned_data['password'],
# #             }
# #             # Store user data temporarily in user_storage
# #             otp_storage[user_data['email']] = None
# #             user_storage[user_data['email']] = user_data

# #             # Generate and send OTP
# #             otp = random.randint(1000, 9999)
# #             otp_storage[user_data['email']] = otp
# #             send_mail(
# #                 'Your OTP for Verification',
# #                 f'Your OTP is: {otp}',
# #                 settings.EMAIL_HOST_USER,
# #                 [user_data['email']],
# #                 fail_silently=False,
# #             )
# #             return redirect('verify_email', email=user_data['email'])
# #     else:
# #         form = SignupForm()
# #     return render(request, 'signup.html', {'form': form})

# # def verify_email(request, email):
# #     if request.method == "POST":
# #         otp = request.POST.get('otp')
# #         if otp_storage.get(email) == int(otp):
# #             # OTP verified, now create the user
# #             user_data = user_storage.get(email)
# #             if user_data:
# #                 user = User(
# #                     first_name=user_data['first_name'],
# #                     last_name=user_data['last_name'],
# #                     username=user_data['username'],
# #                     email=user_data['email'],
# #                     is_verified=True,
# #                 )
# #                 user.set_password(user_data['password'])  # Hash the password
# #                 user.save()

# #                 # Clear temporary data
# #                 del otp_storage[email]
# #                 del user_storage[email]
# #                 return redirect('login')
# #             else:
# #                 return render(request, 'verify_email.html', {'error': 'Invalid OTP request'})
# #         else:
# #             return render(request, 'verify_email.html', {'error': 'Invalid OTP'})
# #     return render(request, 'verify_email.html', {'email': email})

# # def login_view(request):
# #     if request.method == "POST":
# #         form = LoginForm(request.POST)
# #         if form.is_valid():
# #             username = form.cleaned_data['username']
# #             password = form.cleaned_data['password']
# #             try:
# #                 user = User.objects.get(username=username)
# #                 if user.is_verified and user.check_password(password):  # Use check_password to verify the password
# #                     # For simplicity, store user ID in session
# #                     request.session['user_id'] = user.id
# #                     return redirect('home')
# #                 else:
# #                     return render(request, 'login.html', {'form': form, 'error': 'Invalid credentials or account not verified'})
# #             except User.DoesNotExist:
# #                 return render(request, 'login.html', {'form': form, 'error': 'Invalid credentials'})
# #     else:
# #         form = LoginForm()
# #     return render(request, 'login.html', {'form': form})

# # def home(request):
# #     if 'user_id' in request.session:
# #         user = User.objects.get(id=request.session['user_id'])
# #         return render(request, 'home.html', {'user': user})
# #     return redirect('login')

# from django.shortcuts import render, redirect
# from django.core.mail import send_mail
# from django.conf import settings
# from .models import User
# from .forms import SignupForm, LoginForm
# import random
# from django.contrib.auth.hashers import make_password
# from django.contrib import messages  # Import the messages module

# otp_storage = {}  # Temporary OTP storage for demonstration purposes.
# user_storage = {}  # Temporary user storage before OTP verification.

# def signup(request):
#     if request.method == "POST":
#         form = SignupForm(request.POST)
#         if form.is_valid():
#             email = form.cleaned_data['email']
#             username = form.cleaned_data['username']

#             # Check if the email is already registered
#             if User.objects.filter(email=email).exists():
#                 messages.error(request, 'Email is already registered.')
#                 return render(request, 'signup.html', {'form': form})

#             # Check if the username is already taken
#             if User.objects.filter(username=username).exists():
#                 messages.error(request, 'Username is already taken.')
#                 return render(request, 'signup.html', {'form': form})

#             # Temporarily store user data before OTP verification
#             user_data = {
#                 'first_name': form.cleaned_data['first_name'],
#                 'last_name': form.cleaned_data['last_name'],
#                 'username': username,
#                 'email': email,
#                 'password': form.cleaned_data['password'],
#             }
#             # Store user data temporarily in user_storage
#             otp_storage[user_data['email']] = None
#             user_storage[user_data['email']] = user_data

#             # Generate and send OTP
#             otp = random.randint(1000, 9999)
#             otp_storage[user_data['email']] = otp
#             send_mail(
#                 'Your OTP for Verification',
#                 f'Your OTP is: {otp}',
#                 settings.EMAIL_HOST_USER,
#                 [user_data['email']],
#                 fail_silently=False,
#             )
#             messages.success(request, 'OTP sent successfully! Please verify your email.')
#             return redirect('verify_email', email=user_data['email'])
#     else:
#         form = SignupForm()
#     return render(request, 'signup.html', {'form': form})

# # def verify_email(request, email):
# #     if request.method == "POST":
# #         otp = request.POST.get('otp')
        
# #         # Validate OTP length and if it's numeric
# #         if len(otp) != 4 or not otp.isdigit():
# #             messages.error(request, 'OTP should be a 4-digit number.')
# #             return render(request, 'verify_email.html', {'error': 'Invalid OTP format.'})

# #         # Check if OTP matches and is valid
# #         if otp_storage.get(email) == int(otp):
# #             # OTP verified, now create the user
# #             user_data = user_storage.get(email)
# #             if user_data:
# #                 user = User(
# #                     first_name=user_data['first_name'],
# #                     last_name=user_data['last_name'],
# #                     username=user_data['username'],
# #                     email=user_data['email'],
# #                     is_verified=True,
# #                 )
# #                 user.set_password(user_data['password'])  # Hash the password
# #                 user.save()

# #                 # Clear temporary data
# #                 del otp_storage[email]
# #                 del user_storage[email]
# #                 messages.success(request, 'Account created successfully! You can now log in.')
# #                 return redirect('login')
# #             else:
# #                 messages.error(request, 'Invalid OTP request.')
# #                 return render(request, 'verify_email.html')
# #         else:
# #             messages.error(request, 'Invalid OTP.')
# #             return render(request, 'verify_email.html')
# #     return render(request, 'verify_email.html', {'email': email})


# def verify_email(request, email):
#     if request.method == "POST":
#         otp = request.POST.get('otp')

#         # Validate OTP length and if it's numeric
#         if len(otp) != 4 or not otp.isdigit():
#             messages.error(request, 'OTP should be a 4-digit number.')
#             return render(request, 'verify_email.html', {'error': 'Invalid OTP format.', 'email': email})

#         # Check if OTP matches and is valid
#         if otp_storage.get(email) == int(otp):
#             # OTP verified, now create the user
#             user_data = user_storage.get(email)
#             if user_data:
#                 user = User(
#                     first_name=user_data['first_name'],
#                     last_name=user_data['last_name'],
#                     username=user_data['username'],
#                     email=user_data['email'],
#                     is_verified=True,
#                 )
#                 user.set_password(user_data['password'])  # Hash the password
#                 user.save()

#                 # Clear temporary data
#                 del otp_storage[email]
#                 del user_storage[email]
#                 messages.success(request, 'Account created successfully! You can now log in.')
#                 return redirect('login')
#             else:
#                 messages.error(request, 'Invalid OTP request.')
#                 return render(request, 'verify_email.html', {'email': email})
#         else:
#             messages.error(request, 'Invalid OTP.')
#             return render(request, 'verify_email.html', {'email': email})
#     return render(request, 'verify_email.html', {'email': email})



# def login_view(request):
#     if request.method == "POST":
#         form = LoginForm(request.POST)
#         if form.is_valid():
#             username = form.cleaned_data['username']
#             password = form.cleaned_data['password']
#             try:
#                 user = User.objects.get(username=username)
#                 if user.is_verified and user.check_password(password):  # Use check_password to verify the password
#                     # For simplicity, store user ID in session
#                     request.session['user_id'] = user.id
#                     messages.success(request, 'Logged in successfully!')
#                     return redirect('home')
#                 else:
#                     messages.error(request, 'Invalid credentials or account not verified.')
#                     return render(request, 'login.html', {'form': form})
#             except User.DoesNotExist:
#                 messages.error(request, 'Invalid credentials.')
#                 return render(request, 'login.html', {'form': form})
#     else:
#         form = LoginForm()
#     return render(request, 'login.html', {'form': form})

# def home(request):
#     if 'user_id' in request.session:
#         user = User.objects.get(id=request.session['user_id'])
#         return render(request, 'home.html', {'user': user})
#     else:
#         messages.info(request, 'Please log in to access your account.')
#         return redirect('login')


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
            otp_storage[user_data['email']] = None
            user_storage[user_data['email']] = user_data

            # Generate and send OTP
            otp = random.randint(1000, 9999)
            otp_storage[user_data['email']] = otp
            send_mail(
                'Your OTP for Verification',
                f'Your OTP is: {otp}',
                settings.EMAIL_HOST_USER,
                [user_data['email']],
                fail_silently=False,
            )
            messages.success(request, 'OTP sent successfully! Please verify your email.')
            return redirect('verify_email', email=user_data['email'])
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})

def verify_email(request, email):
    if request.method == "POST":
        otp = request.POST.get('otp')
        if otp and otp_storage.get(email) == int(otp):
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
