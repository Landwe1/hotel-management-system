from django.db import models
from django.conf import settings

class Announcement(models.Model):
    TARGET_ROLE_CHOICES = (
        ('ALL', 'All Staff'),
        ('RECEPTIONIST', 'Receptionists Only'),
        ('ACCOUNTANT', 'Accountants Only'),
        ('CHEF', 'Chefs / Kitchen Only'),
        ('STORES_MANAGER', 'Stores Managers Only'),
        ('MANAGER', 'Managers & Executives'),
    )

    title = models.CharField(max_length=200)
    content = models.TextField()
    target_role = models.CharField(max_length=20, choices=TARGET_ROLE_CHOICES, default='ALL')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='announcements')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_target_role_display()})"


class CalendarEvent(models.Model):
    EVENT_TYPES = (
        ('EVENT', 'General Event / Function'),
        ('MAINTENANCE', 'Room Maintenance'),
        ('AUDIT', 'Inventory / Stock Audit'),
        ('MEETING', 'Staff / Management Meeting'),
    )

    title = models.CharField(max_length=200)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, default='EVENT')
    description = models.TextField(blank=True, null=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_date']

    def __str__(self):
        return f"{self.title} ({self.start_date.strftime('%Y-%m-%d')})"

