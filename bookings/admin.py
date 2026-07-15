from django.contrib import admin
from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['room', 'guest_display_name', 'check_in_date', 'check_out_date', 'status', 'is_paid']
    list_filter = ['status', 'is_paid', 'check_in_date']