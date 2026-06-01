from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import SignupForm, LoginForm, ProfileUpdateForm

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.username}! Your account has been created.')
            return redirect('dashboard')
    else:
        form = SignupForm()

    interest_field_list = [
        {'name': 'pref_culture',   'label': 'Culture',    'emoji': '🏛️'},
        {'name': 'pref_adventure', 'label': 'Adventure',  'emoji': '🏔️'},
        {'name': 'pref_nature',    'label': 'Nature',     'emoji': '🌿'},
        {'name': 'pref_beaches',   'label': 'Beaches',    'emoji': '🏖️'},
        {'name': 'pref_nightlife', 'label': 'Nightlife',  'emoji': '🌃'},
        {'name': 'pref_cuisine',   'label': 'Cuisine',    'emoji': '🍜'},
        {'name': 'pref_wellness',  'label': 'Wellness',   'emoji': '🧘'},
        {'name': 'pref_urban',     'label': 'Urban',      'emoji': '🏙️'},
        {'name': 'pref_seclusion', 'label': 'Seclusion',  'emoji': '🌲'},
    ]
    return render(request, 'accounts/signup.html', {
        'form': form,
        'interest_field_list': interest_field_list,
    })

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect(request.GET.get('next', 'dashboard'))
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})