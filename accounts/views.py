from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
from .forms import PhoneAuthenticationForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboards:dashboard_hub')

    if request.method == 'POST':
        form = PhoneAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('dashboards:dashboard_hub') # Added namespace 'dashboards:'
    else:
        form = PhoneAuthenticationForm()
        
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    auth_logout(request)
    return redirect('login')
