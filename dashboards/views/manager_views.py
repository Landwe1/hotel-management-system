from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_home(request):
    user_role = request.user.role
    is_staff_or_admin = request.user.is_staff or user_role in ['MANAGER', 'EXECUTIVE'] or request.user.is_superuser

    # 1. INTERCEPT PRESENTATION CLICKS HERE TOO!
    forced_view = request.GET.get('view')
    if forced_view and is_staff_or_admin:
        if forced_view == 'RECEPTIONIST': return redirect('receptionist_home')
        elif forced_view == 'ACCOUNTANT': return redirect('accountant_home')
        elif forced_view == 'CHEF': return redirect('chef_home')
        elif forced_view == 'STORES_MANAGER': return redirect('stores_home')
        elif forced_view == 'MANAGER': return redirect('manager_home')

    # 2. FALLBACK (If no ?view= parameter is clicked, show management deck normally)
    return render(request, 'dashboards/manager_home.html')