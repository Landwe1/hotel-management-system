from django.db import models

class RoomTier(models.Model):
    """E.g., Standard, Deluxe, Presidential Suite"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Base rate per night")

    def __str__(self):
        return self.name

class Room(models.Model):
    ROOM_STATUS = (
        ('AVAILABLE', 'Available / Ready'),
        ('OCCUPIED', 'Occupied'),
        ('DIRTY', 'Dirty / Needs Housekeeping'),
        ('MAINTENANCE', 'Out of Order / Maintenance'),
    )

    room_number = models.CharField(max_length=10, unique=True)
    tier = models.ForeignKey(RoomTier, on_delete=models.PROTECT, related_name="rooms")
    floor = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=ROOM_STATUS, default='AVAILABLE')
    max_capacity = models.IntegerField(default=2, help_text="Maximum guests allowed")

    def __str__(self):
        return f"Room {self.room_number} ({self.tier.name})"
