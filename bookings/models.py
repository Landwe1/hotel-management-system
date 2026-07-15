from django.db import models
from django.conf import settings
from rooms.models import Room

class Booking(models.Model):
    BOOKING_STATUS = (
        ('PENDING', 'Pending / Reserved'),
        ('CHECKED_IN', 'Checked In'),
        ('CHECKED_OUT', 'Checked Out'),
        ('CANCELLED', 'Cancelled'),
    )

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="bookings")
    
    # Decoupled Option 2: Optional link to a registered account
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="bookings"
    )
    
    # Fallback fields for walk-ins, international visitors, or phone-less guests
    guest_first_name = models.CharField(max_length=100, blank=True)
    guest_last_name = models.CharField(max_length=100, blank=True)
    guest_email = models.EmailField(blank=True)
    guest_phone_fallback = models.CharField(max_length=20, blank=True, help_text="For walk-ins without system accounts")

    # Dates
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    
    # Financial tracking fields
    status = models.CharField(max_length=20, choices=BOOKING_STATUS, default='PENDING')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Tracks down-payments/deposits
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking for {self.guest_display_name} - Room {self.room.room_number}"

    @property
    def guest_display_name(self):
        """Returns the registered profile name, or the manual walk-in text fields."""
        if self.user:
            return f"{self.user.first_name} {self.user.last_name}".strip() or str(self.user.phone_number)
        return f"{self.guest_first_name} {self.guest_last_name}".strip() or "Walk-In Guest"

    @property
    def remaining_balance(self):
        """Calculates outstanding balance dynamically on the fly."""
        return self.total_amount - self.amount_paid

