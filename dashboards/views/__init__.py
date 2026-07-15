from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def central_dashboard_router(request):
    user_role = request.user.role
    
    # Enhanced safety gate: Allow staff, designated managers, or global superusers
    is_staff_or_admin = (
        request.user.is_staff or 
        user_role in ['MANAGER', 'EXECUTIVE'] or 
        request.user.is_superuser
    )

    # Presentation Feature: Look for an explicit override in the URL (e.g., /dashboard/?view=CHEF)
    forced_view = request.GET.get('view')
    if forced_view and is_staff_or_admin:
        if forced_view == 'RECEPTIONIST': return redirect('receptionist_home')
        elif forced_view == 'ACCOUNTANT': return redirect('accountant_home')
        elif forced_view == 'CHEF': return redirect('chef_home')
        elif forced_view == 'STORES_MANAGER': return redirect('stores_home')
        elif forced_view == 'MANAGER': return redirect('manager_home')

    # Default Automated Routing Logic
    if user_role == 'RECEPTIONIST':
        return redirect('receptionist_home')
    elif user_role == 'ACCOUNTANT':
        return redirect('accountant_home')
    elif user_role == 'CHEF':
        return redirect('chef_home')
    elif user_role == 'STORES_MANAGER':
        return redirect('stores_home')
    elif user_role == 'MANAGER' or user_role == 'EXECUTIVE' or request.user.is_superuser:
        return redirect('manager_home') 
    else:
        return redirect('login')
