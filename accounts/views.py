# accounts/views.py

import re
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from .models import Profile


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username  = request.POST.get('username', '').strip()
        email     = request.POST.get('email', '').strip()
        phone     = request.POST.get('phone', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        has_error = False

        # 1. Blank fields
        if not all([username, email, password1, password2]):
            messages.error(request, 'All required fields must be filled.')
            has_error = True

        # 2. Username format
        if username and not re.match(r'^[\w]{3,30}$', username):
            messages.error(request, 'Username must be 3–30 characters (letters, numbers, underscores only).')
            has_error = True

        # 3. Email format
        if email:
            try:
                validate_email(email)
            except ValidationError:
                messages.error(request, 'Enter a valid email address.')
                has_error = True

        # 4. Phone format
        if phone and not re.match(r'^\+?\d{7,15}$', phone):
            messages.error(request, 'Enter a valid phone number (7–15 digits).')
            has_error = True

        # 5. Password match
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            has_error = True

        # 6. Password strength
        if password1 == password2 and password1:
            try:
                validate_password(password1)
            except ValidationError as e:
                for error in e.messages:
                    messages.error(request, error)
                has_error = True

        # 7. Duplicate username
        if username and User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            has_error = True

        # 8. Duplicate email
        if email and User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            has_error = True

        # ✅ render (NOT redirect) so all messages are preserved
        if has_error:
            return render(request, 'accounts/register.html')

        # All good — create the user
        user = User.objects.create_user(username=username, email=email, password=password1)
        Profile.objects.get_or_create(user=user, defaults={'phone': phone})
        messages.success(request, 'Account created! Please log in.')
        return redirect('login')

    return render(request, 'accounts/register.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return render(request, 'accounts/login.html')

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            next_url = request.GET.get('next', '/')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password!')

    return render(request, 'accounts/login.html')


def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'Logged out successfully!')
    return redirect('home')


@login_required
def profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        email      = request.POST.get('email', '').strip()
        phone      = request.POST.get('phone', '').strip()
        address    = request.POST.get('address', '').strip()
        license_no = request.POST.get('license_no', '').strip()

        has_error = False

        # 1. Email format
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Enter a valid email address.')
            has_error = True

        # 2. Email uniqueness (exclude current user)
        if email and User.objects.filter(email=email).exclude(pk=request.user.pk).exists():
            messages.error(request, 'That email is already in use by another account.')
            has_error = True

        # 3. Phone format
        if phone and not re.match(r'^\+?\d{7,15}$', phone):
            messages.error(request, 'Enter a valid phone number (7–15 digits).')
            has_error = True

        # 4. Profile picture
        if request.FILES.get('profile_pic'):
            pic = request.FILES['profile_pic']
            if pic.content_type not in ['image/jpeg', 'image/png', 'image/webp']:
                messages.error(request, 'Only JPEG, PNG, or WebP images are allowed.')
                has_error = True
            if pic.size > 2 * 1024 * 1024:
                messages.error(request, 'Image must be under 2 MB.')
                has_error = True

        if has_error:
            return render(request, 'accounts/profile.html', {'profile': profile})

        # Update User
        request.user.first_name = first_name
        request.user.last_name  = last_name
        request.user.email      = email
        request.user.save()

        # Update Profile
        profile.phone      = phone
        profile.address    = address
        profile.license_no = license_no

        if request.FILES.get('profile_pic'):
            profile.profile_pic = request.FILES['profile_pic']

        profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')

    return render(request, 'accounts/profile.html', {'profile': profile})