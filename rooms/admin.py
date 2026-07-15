from django.contrib import admin
from .models import RoomTier, Room

admin.site.register(RoomTier)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['room_number', 'tier', 'floor', 'status', 'max_capacity']
    list_filter = ['status', 'tier', 'floor']