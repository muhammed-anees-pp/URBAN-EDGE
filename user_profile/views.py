from django.shortcuts import render, redirect, get_object_or_404
from .models import Address
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import re
from django.contrib.auth import update_session_auth_hash
# from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import authenticate


@login_required
def user_profile(request):
    addresses = Address.objects.filter(user = request.user,is_deleted=False)
    context = {
        'addresses' : addresses,
    }
    return render(request,'user/profile.html',context)

@login_required
def view_addresses(request):
    addresses = Address.objects.filter(user=request.user, is_deleted=False)
    return render(request, 'user/address.html', {'addresses': addresses})


@login_required
def add_address(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        country = request.POST.get('country', '').strip()
        postcode = request.POST.get('postcode', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        additional_info = request.POST.get('additional_info', '').strip()

        # Validation Errors
        errors = []
        if not all([name, address, city, state, country, postcode, phone]):
            errors.append("All fields except additional info and email are required.")
        if not postcode.isdigit():
            errors.append("Postcode must be numeric.")
        phone_regex = re.compile(r'^\+?[1-9]\d{1,14}$')
        if not phone_regex.match(phone):
            errors.append("Invalid phone number format.")
        if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            errors.append("Invalid email address.")

        # If there are errors, re-render the modal with errors
        if errors:
            return render(
                request,
                'user/address.html',
                {
                    'addresses': Address.objects.filter(user=request.user, is_deleted=False),
                    'add_errors': errors,
                    'add_data': {
                        'name': name,
                        'address': address,
                        'city': city,
                        'state': state,
                        'country': country,
                        'postcode': postcode,
                        'phone': phone,
                        'email': email,
                        'additional_info': additional_info,
                    },
                },
            )

        # Create new address
        Address.objects.create(
            user=request.user,
            name=name,
            address=address,
            city=city,
            state=state,
            country=country,
            postcode=postcode,
            phone=phone,
            email=email,
            additional_info=additional_info,
        )
        messages.success(request, "Address added successfully!")
        return redirect('addresses')


@login_required
def edit_address(request):
    if request.method == 'POST':
        address_id = request.POST.get('id')
        address = get_object_or_404(Address, id=address_id, user=request.user)

        name = request.POST.get('name', '').strip()
        address_line = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        country = request.POST.get('country', '').strip()
        postcode = request.POST.get('postcode', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()

        # Validation Errors
        errors = []
        if not all([name, address_line, city, state, country, postcode, phone]):
            errors.append("All fields except email are required.")
        if not postcode.isdigit():
            errors.append("Postcode must be numeric.")
        phone_regex = re.compile(r'^\+?[1-9]\d{1,14}$')
        if not phone_regex.match(phone):
            errors.append("Invalid phone number format.")
        if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            errors.append("Invalid email address.")

        # If there are errors, re-render the modal with errors
        if errors:
            return render(
                request,
                'user/address.html',
                {
                    'addresses': Address.objects.filter(user=request.user, is_deleted=False),
                    'edit_errors': errors,
                    'edit_data': {
                        'id': address.id,
                        'name': name,
                        'address': address_line,
                        'city': city,
                        'state': state,
                        'country': country,
                        'postcode': postcode,
                        'phone': phone,
                        'email': email,
                    },
                },
            )

        # Update address
        address.name = name
        address.address = address_line
        address.city = city
        address.state = state
        address.country = country
        address.postcode = postcode
        address.phone = phone
        address.email = email
        address.save()

        messages.success(request, "Address updated successfully!")
        return redirect('addresses')

@login_required
def delete_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)

    if request.method == 'POST':
        address.delete()  # Permanently delete the address from the database
        messages.success(request, 'Address deleted permanently!')
        return redirect('addresses')

    return redirect('addresses')


@login_required
def change_password(request):
    """Change user's password."""
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        # Validate the current password
        user = authenticate(username=request.user.username, password=current_password)
        if not user:
            messages.error(request, 'The current password you entered is incorrect.')
            return render(request, 'user/profile.html')

        # Validate new and confirm passwords
        if new_password != confirm_password:
            messages.error(request, 'The new password and confirm password do not match.')
            return render(request, 'user/profile.html')

        # Check the new password strength
        is_valid, error_message = validate_password(new_password)
        if not is_valid:
            messages.error(request, error_message)
            return render(request, 'user/profile.html')

        # Change the password
        user.set_password(new_password)
        user.save()

        # Update the session hash to keep the user logged in after password change
        update_session_auth_hash(request, user)

        messages.success(request, 'Your password has been successfully changed.')
        return redirect('user_profile')  # Redirect to the user profile page or another page you want

    return render(request, 'user/profile.html')

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












# from django.shortcuts import render,redirect,get_object_or_404
# from .models import Address


# from django.contrib.auth.decorators import login_required
# from django.contrib.auth.models import User
# from django.contrib import messages
# from django.core.validators import RegexValidator
# from django.core.exceptions import ValidationError
# import re
# from django.contrib.auth.hashers import check_password
# # from Order.models import Order,OrderItem
# # from Products.models import SizeVariant


# # Create your views here.

# @login_required
# def user_profile(request):
#     addresses = Address.objects.filter(user = request.user,is_deleted=False)
#     context = {
#         'addresses' : addresses,
#     }
#     return render(request,'user/profile.html',context)


# @login_required
# def view_addresses(request):
#     addresses = Address.objects.filter(user=request.user, is_deleted=False)

#     context = {
#         'addresses': addresses
#     }

#     return render(request, 'user/address.html', context)


# @login_required
# def add_address(request):
#     if request.method == 'POST':
#         # Get form data
#         name = request.POST.get('name')
#         address = request.POST.get('address')
#         city = request.POST.get('city')
#         state = request.POST.get('state')
#         country = request.POST.get('country')
#         postcode = request.POST.get('postcode')
#         phone = request.POST.get('phone')
#         email = request.POST.get('email')
#         additional_info = request.POST.get('additional_info')

#         # Validate required fields
#         if not name or not address or not city or not state or not country or not postcode or not phone:
#             messages.error(request, 'All fields are required except additional info.')
#             return redirect('addresses')

#         # Validate postcode
#         if not postcode.isdigit():
#             messages.error(request, 'Postcode must be numeric.')
#             return redirect('addresses')

#         # Validate phone number
#         phone_regex = re.compile(r'^\+?[1-9]\d{1,14}$')
#         if not phone_regex.match(phone):
#             messages.error(request, 'Invalid phone number format.')
#             return redirect('addresses')

#         # Validate email if provided
#         if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
#             messages.error(request, 'Invalid email address.')
#             return redirect('addresses')

#         # Create new address
#         Address.objects.create(
#             user=request.user,
#             name=name,
#             address=address,
#             city=city,
#             state=state,
#             country=country,
#             postcode=postcode,
#             phone=phone,
#             email=email,
#             additional_info=additional_info
#         )

#         messages.success(request, 'Address added successfully!')
#         return redirect('addresses')

#     return redirect('addresses')


# @login_required
# def edit_address(request):
#     if request.method == 'POST':
#         address_id = request.POST.get('id')
#         address = get_object_or_404(Address, id=address_id, user=request.user)
        
#         # Get updated details from the form
#         name = request.POST.get('name')
#         address_line = request.POST.get('address')
#         city = request.POST.get('city')
#         state = request.POST.get('state')
#         country = request.POST.get('country')
#         postcode = request.POST.get('postcode')
#         phone = request.POST.get('phone')
#         email = request.POST.get('email')

#         # Validate inputs
#         if not postcode.isdigit():
#             messages.error(request, 'Postcode must be numeric.')
#             return redirect('addresses')

#         phone_regex = re.compile(r'^\+?[1-9]\d{1,14}$')
#         if not phone_regex.match(phone):
#             messages.error(request, 'Invalid phone number format.')
#             return redirect('addresses')

#         if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
#             messages.error(request, 'Invalid email address.')
#             return redirect('addresses')

#         # Update the address object
#         address.name = name
#         address.address = address_line
#         address.city = city
#         address.state = state
#         address.country = country
#         address.postcode = postcode
#         address.phone = phone
#         address.email = email
#         address.save()

#         messages.success(request, 'Address updated successfully!')
#         return redirect('addresses')

#     return redirect('addresses')


# @login_required
# def delete_address(request, address_id):
#     address = get_object_or_404(Address, id=address_id, user=request.user)

#     if request.method == 'POST':
#         address.is_deleted = True
#         address.save()
#         messages.success(request, 'Address deleted successfully!')
#         return redirect('addresses')

#     return redirect('addresses')










# @login_required
# def add_address(request):
#     if request.method == 'POST':
#         name = request.POST.get('name')
#         address = request.POST.get('address')
#         city = request.POST.get('city')
#         state = request.POST.get('state')
#         country = request.POST.get('country')
#         postcode = request.POST.get('postcode')
#         phone = request.POST.get('phone')
#         email = request.POST.get('email')
#         additional_info = request.POST.get('additional_info')

#         # Validation for required fields
#         if not name or not address or not city or not state or not country or not postcode or not phone:
#             messages.error(request, 'All fields are required except additional info.')
#             return redirect('account')

       
#         if not postcode.isdigit():
#             messages.error(request, 'Postcode must be numeric.')
#             return redirect('account')

        
#         phone_regex = re.compile(r'^\+?[1-9]\d{1,14}$')
#         if not phone_regex.match(phone):
#             messages.error(request, 'Invalid phone number format.')
#             return redirect('account')

        
#         if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
#             messages.error(request, 'Invalid email address.')
#             return redirect('account')

        
#         Address.objects.create(
#             user=request.user,
#             name=name,
#             address=address,
#             city=city,
#             state=state,
#             country=country,
#             postcode=postcode,
#             phone=phone,
#             email=email,
#             additional_info=additional_info
#         )

#         messages.success(request, 'Address added successfully!')
#         return redirect('account') 

#     return redirect('account') 


# @login_required
# def edit_address(request):
#     if request.method == 'POST':
#         address_id = request.POST.get('id')
#         address = get_object_or_404(Address, id=address_id)
#         print(address_id,"address id yaan")

#         name = request.POST.get('name')
#         address_line = request.POST.get('address')
#         city = request.POST.get('city')
#         state = request.POST.get('state')
#         country = request.POST.get('country')
#         postcode = request.POST.get('postcode')
#         phone = request.POST.get('phone')
#         print(name)
#         print(address_line)
#         print(city)
#         print(state)
#         print(country)
#         print(postcode)
#         print(phone)
        
#         if not postcode.isdigit():
#             messages.error(request, 'Postcode must be numeric.')
#             return redirect('account')

       
#         phone_regex = re.compile(r'^\+?[1-9]\d{1,14}$')
#         if not phone_regex.match(phone):
#             messages.error(request, 'Invalid phone number format.')
#             return redirect('account')

        
#         email = request.POST.get('account')
#         if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
#             messages.error(request, 'Invalid email address.')
#             return redirect('account')

       
#         address.name = name
#         address.address = address_line
#         address.city = city
#         address.state = state
#         address.country = country
#         address.postcode = postcode
#         address.phone = phone
#         address.additional_info = request.POST.get('additional_info')

#         address.save()

#         messages.success(request, 'Address updated successfully.')
#         return redirect('account') 

#     return redirect('account')



# @login_required
# def delete_address(request, address_id):
#     address = get_object_or_404(Address, id=address_id, user=request.user)

#     if request.method == 'POST':
#         address.is_deleted = True
#         messages.success(request, 'Address deleted successfully!')
#         return redirect('account') 


#     return redirect('account')



# @login_required
# def update_username(request):
#     if request.method == 'POST':
#         username = request.POST.get('username')
#         user = request.user

        
#         if len(username) < 3 or len(username) > 30:
#             messages.error(request, 'Username must be between 3 and 30 characters.')
#         elif not username.isalnum():
#             messages.error(request, 'Username can only contain alphanumeric characters.')
#         elif User.objects.filter(username=username).exists():
#             messages.error(request, 'Username already taken.')
#         else:
#             try:
#                 validator = RegexValidator(r'^[a-zA-Z0-9]*$', 'Username must be alphanumeric.')
#                 validator(username)
                
#                 user.username = username
#                 user.save()
#                 messages.success(request, 'Username updated successfully!')
#                 return redirect('update_username')

#             except ValidationError as e:
#                 messages.error(request, f'Invalid username: {e.message}')

#     return render(request, 'accounts.html')




# @login_required
# def add_address(request):
#     if request.method == 'POST':
#         name = request.POST.get('name')
#         address = request.POST.get('address')
#         city = request.POST.get('city')
#         state = request.POST.get('state')
#         country = request.POST.get('country')
#         postcode = request.POST.get('postcode')
#         phone = request.POST.get('phone')
#         email = request.POST.get('email')
#         additional_info = request.POST.get('additional_info')

#         # Validation for required fields
#         if not name or not address or not city or not state or not country or not postcode or not phone:
#             messages.error(request, 'All fields are required except additional info.')
#             return redirect('account')

       
#         if not postcode.isdigit():
#             messages.error(request, 'Postcode must be numeric.')
#             return redirect('account')

        
#         phone_regex = re.compile(r'^\+?[1-9]\d{1,14}$')
#         if not phone_regex.match(phone):
#             messages.error(request, 'Invalid phone number format.')
#             return redirect('account')

        
#         if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
#             messages.error(request, 'Invalid email address.')
#             return redirect('account')

        
#         Address.objects.create(
#             user=request.user,
#             name=name,
#             address=address,
#             city=city,
#             state=state,
#             country=country,
#             postcode=postcode,
#             phone=phone,
#             email=email,
#             additional_info=additional_info
#         )

#         messages.success(request, 'Address added successfully!')
#         return redirect('account') 

#     return redirect('account') 


# @login_required
# def edit_address(request):
#     if request.method == 'POST':
#         address_id = request.POST.get('id')
#         address = get_object_or_404(Address, id=address_id)
#         print(address_id,"address id yaan")

#         name = request.POST.get('name')
#         address_line = request.POST.get('address')
#         city = request.POST.get('city')
#         state = request.POST.get('state')
#         country = request.POST.get('country')
#         postcode = request.POST.get('postcode')
#         phone = request.POST.get('phone')
#         print(name)
#         print(address_line)
#         print(city)
#         print(state)
#         print(country)
#         print(postcode)
#         print(phone)
        
#         if not postcode.isdigit():
#             messages.error(request, 'Postcode must be numeric.')
#             return redirect('account')

       
#         phone_regex = re.compile(r'^\+?[1-9]\d{1,14}$')
#         if not phone_regex.match(phone):
#             messages.error(request, 'Invalid phone number format.')
#             return redirect('account')

        
#         email = request.POST.get('account')
#         if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
#             messages.error(request, 'Invalid email address.')
#             return redirect('account')

       
#         address.name = name
#         address.address = address_line
#         address.city = city
#         address.state = state
#         address.country = country
#         address.postcode = postcode
#         address.phone = phone
#         address.additional_info = request.POST.get('additional_info')

#         address.save()

#         messages.success(request, 'Address updated successfully.')
#         return redirect('account') 

#     return redirect('account')



# @login_required
# def delete_address(request, address_id):
#     address = get_object_or_404(Address, id=address_id, user=request.user)

#     if request.method == 'POST':
#         address.is_deleted = True
#         messages.success(request, 'Address deleted successfully!')
#         return redirect('account') 


#     return redirect('account')





# @login_required
# def update_password(request):
#     if request.method == 'POST':
#         current_password = request.POST.get('current_password')
#         password = request.POST.get('new_password')
#         confirm_password = request.POST.get('confirm_password')
#         user = request.user


#         if user.check_password(current_password):
#             if password == confirm_password:
#                 user.set_password(password)
#                 user.save()
#                 messages.success(request, 'Password updated successfully')
#                 return redirect('account')
#             else:
#                 messages.error(request, 'Passwords do not match')
#         else:
#             messages.error(request, 'Old password is incorrect')

#     return redirect('account')




