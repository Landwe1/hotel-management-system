from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class InventoryItem(models.Model):
    UNIT_CHOICES = [
        ('PCS', 'Pieces'),
        ('KG', 'Kilograms'),
        ('LITERS', 'Liters'),
        ('PACKS', 'Packs'),
        ('BOTTLES', 'Bottles'),
    ]
    
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='PCS')
    min_stock_level = models.DecimalField(max_digits=10, decimal_places=2, default=5.00, help_text="Triggers low stock alert")
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_value(self):
        return self.quantity * self.cost_per_unit

    @property
    def is_low_stock(self):
        return self.quantity <= self.min_stock_level

    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit})"


class StockTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('ADD', 'Stock In / Restock'),
        ('REMOVE', 'Stock Out / Issued'),
        ('DAMAGE', 'Reported Damaged'),
        ('MISSING', 'Reported Missing'),
        ('DONATION', 'Donation Outbound'),
    ]
    
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=15, choices=TRANSACTION_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.quantity} {self.item.unit} of {self.item.name}"


class LostAndFound(models.Model):
    STATUS_CHOICES = [
        ('FOUND', 'Found & Secured'),
        ('CLAIMED', 'Claimed by Owner'),
        ('DONATED', 'Donated (Unclaimed)'),
        ('DISPOSED', 'Disposed'),
    ]
    
    item_name = models.CharField(max_length=200)
    description = models.TextField()
    location_found = models.CharField(max_length=200, help_text="e.g. Room 204 or Lobby Bar")
    found_date = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='FOUND')
    finder_name = models.CharField(max_length=100, blank=True, null=True)
    claimant_name = models.CharField(max_length=100, blank=True, null=True, help_text="Filled when claimed")
    claimant_phone = models.CharField(max_length=30, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.item_name} ({self.get_status_display()})"


class BorrowedItem(models.Model):
    """Tracks physical assets lent out (e.g., irons, adapters, hair dryers, tools) to guests or staff."""
    item_name = models.CharField(max_length=200)
    borrower_name = models.CharField(max_length=150, help_text="Guest name/Room or Staff Member")
    contact_info = models.CharField(max_length=100, blank=True, null=True)
    borrowed_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField()
    returned_date = models.DateField(blank=True, null=True)
    is_returned = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        status = "Returned" if self.is_returned else "Active Loan"
        return f"{self.item_name} borrowed by {self.borrower_name} ({status})"

