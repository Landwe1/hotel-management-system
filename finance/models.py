from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from bookings.models import Booking  # Import your existing Booking model


class Payment(models.Model):
    """
    Tracks all incoming revenue transactions (Night Audit / Daily Cash Drops / Digital Gateways).
    Connects directly to Bookings.
    """
    PAYMENT_METHODS = (
        ('CASH', 'Cash'),
        ('CARD', 'Credit / Debit Card'),
        ('MOBILE_MONEY', 'Mobile Money'),
        ('BANK_TRANSFER', 'Bank Transfer'),
    )

    PAYMENT_TYPES = (
        ('DEPOSIT', 'Advance Deposit / Down Payment'),
        ('FULL_PAYMENT', 'Full Settlement'),
        ('PARTIAL', 'Partial Payment'),
        ('REFUND', 'Refund / Payout'),
    )

    booking = models.ForeignKey(
        Booking, 
        on_delete=models.CASCADE, 
        related_name="payments"
    )
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0.01)]
    )
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES, default='FULL_PAYMENT')
    transaction_reference = models.CharField(
        max_length=100, 
        blank=True, 
        help_text="Receipt #, Mobile Money Ref, or Bank Transaction ID"
    )
    
    # Internal Audit tracking
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        help_text="Accountant or Receptionist who verified this transaction"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """
        Auto-update Booking financial stats upon saving a payment.
        """
        super().save(*args, **kwargs)
        # Recalculate booking total paid dynamically
        total_paid = self.booking.payments.aggregate(
            total=models.Sum('amount')
        )['total'] or 0.00
        
        self.booking.amount_paid = total_paid
        if self.booking.amount_paid >= self.booking.total_amount:
            self.booking.is_paid = True
        else:
            self.booking.is_paid = False
        self.booking.save()

    def __str__(self):
        return f"Payment of {self.amount} for Booking #{self.booking.id} ({self.payment_method})"


class ExpenseCategory(models.Model):
    """Categories for Cost Control: e.g., Generator Fuel, Kitchen Provisions, Laundry Supplies."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Expense Categories"

    def __str__(self):
        return self.name


class Expense(models.Model):
    """
    Tracks Accounts Payable & Outgoing Operational Expenses (Supplier payments, fuel, utilities).
    """
    category = models.ForeignKey(
        ExpenseCategory, 
        on_delete=models.PROTECT, 
        related_name="expenses"
    )
    title = models.CharField(max_length=200, help_text="e.g., Purchased 200L Diesel for Generator")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    vendor_supplier = models.CharField(max_length=150, blank=True, help_text="Name of supplier or company")
    receipt_doc = models.FileField(upload_to="receipts/%Y/%m/", blank=True, null=True)
    
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="approved_expenses"
    )
    expense_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - ${self.amount}"


class Invoice(models.Model):
    """
    City Ledger & Corporate Billing.
    Generates invoices for corporate clients or guests with outstanding balances.
    """
    INVOICE_STATUS = (
        ('DRAFT', 'Draft'),
        ('ISSUED', 'Issued / Sent'),
        ('PAID', 'Fully Paid'),
        ('OVERDUE', 'Overdue'),
        ('CANCELLED', 'Cancelled'),
    )

    invoice_number = models.CharField(max_length=50, unique=True)
    booking = models.OneToOneField(
        Booking, 
        on_delete=models.CASCADE, 
        related_name="invoice"
    )
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=INVOICE_STATUS, default='DRAFT')
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True, help_text="Payment terms, local tax compliance notes, or bank details")

    @property
    def grand_total(self):
        return self.booking.total_amount + self.tax_amount

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.booking.guest_display_name}"

