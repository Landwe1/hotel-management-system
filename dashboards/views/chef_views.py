from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_home(request):
    # The chef will eventually see daily meal plans, orders, and kitchen requirements here
    return render(request, 'dashboards/chef_home.html')