from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from bookings.models import Booking
from django.db.models import Sum

@login_required
def dashboard_home(request):
    # Pull data relevant to financials
    total_revenue = Booking.objects.filter(is_paid=True).aggregate(Sum('total_amount'))['total_amount__sum'] or 0.00
    pending_invoices = Booking.objects.filter(is_paid=False)

    context = {
        'total_revenue': total_revenue,
        'pending_invoices': pending_invoices,
    }
    return render(request, 'dashboards/accountant_home.html', context)