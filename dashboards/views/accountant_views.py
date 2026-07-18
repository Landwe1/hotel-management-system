from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

# Models
from bookings.models import Booking
from finance.models import Expense, ExpenseCategory, Invoice, Payment
from rooms.models import RoomTier


@login_required
def accountant_dashboard(request):
    """
    Main Accountant Dashboard View:
    Calculates Real-time Revenue, Receivables, Operational Expenses, Net Cash Flow,
    and lists items needing immediate action (Pending Balances & Unpaid Invoices).
    """
    today = date.today()

    # ---------------------------------------------------------
    # 1. REVENUE METRICS (INFLOW)
    # ---------------------------------------------------------
    valid_bookings = Booking.objects.exclude(status='CANCELLED')

    # Total lifetime revenue collected
    total_revenue_collected = Payment.objects.filter(
        booking__in=valid_bookings
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Today's Cash Flow Inflow (Night Audit Daily Balance Check)
    today_revenue = Payment.objects.filter(
        created_at__date=today
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Outstanding Receivables (Total Room Balances Unpaid)
    total_receivables = valid_bookings.aggregate(
        pending=Sum(
            ExpressionWrapper(
                F('total_amount') - F('amount_paid'),
                output_field=DecimalField()
            )
        )
    )['pending'] or Decimal('0.00')

    # ---------------------------------------------------------
    # 2. EXPENSE & OUTFLOW METRICS
    # ---------------------------------------------------------
    # Total Expenses Logged
    total_expenses = Expense.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Today's Expenses Logged
    today_expenses = Expense.objects.filter(
        expense_date=today
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Net Cash Flow Computation
    net_profit = total_revenue_collected - total_expenses

    # Breakdown of Expenses by Category
    expense_by_category = ExpenseCategory.objects.annotate(
        category_total=Sum('expenses__amount')
    ).values('name', 'category_total')

    # ---------------------------------------------------------
    # 3. PAYMENT METHOD BREAKDOWN (Night Audit Reconciliation)
    # ---------------------------------------------------------
    payment_methods_summary = Payment.objects.values('payment_method').annotate(
        method_total=Sum('amount'),
        transaction_count=Count('id')
    )

    # ---------------------------------------------------------
    # 4. ACTION ITEMS & TABLES
    # ---------------------------------------------------------
    # Bookings needing collection (Unpaid or partially paid)
    unsettled_bookings = valid_bookings.filter(
        is_paid=False
    ).select_related('room', 'room__tier', 'user').order_by('-created_at')[:10]

    # Recent Recorded Payments
    recent_payments = Payment.objects.select_related(
        'booking', 'recorded_by'
    ).order_by('-created_at')[:10]

    # Overdue or Issued Corporate Invoices
    pending_invoices = Invoice.objects.filter(
        status__in=['ISSUED', 'OVERDUE']
    ).select_related('booking').order_by('due_date')[:5]

    context = {
        # High Level Totals
        'total_revenue_collected': total_revenue_collected,
        'today_revenue': today_revenue,
        'total_receivables': total_receivables,
        'total_expenses': total_expenses,
        'today_expenses': today_expenses,
        'net_profit': net_profit,
        
        # Categorized Summaries
        'expense_by_category': expense_by_category,
        'payment_methods_summary': payment_methods_summary,
        
        # Action Lists
        'unsettled_bookings': unsettled_bookings,
        'recent_payments': recent_payments,
        'pending_invoices': pending_invoices,
    }

    return render(request, 'dashboards/accountant_home.html', context)


@login_required
def record_payment_view(request, booking_id):
    """
    View for the accountant/cashier to record an incoming payment for a booking.
    Calculates remaining balance and automatically updates Booking status.
    """
    booking = get_object_or_404(Booking, id=booking_id)

    if request.method == 'POST':
        amount = request.POST.get('amount')
        payment_method = request.POST.get('payment_method')
        payment_type = request.POST.get('payment_type')
        transaction_reference = request.POST.get('transaction_reference', '')

        try:
            # Create payment record
            Payment.objects.create(
                booking=booking,
                amount=amount,
                payment_method=payment_method,
                payment_type=payment_type,
                transaction_reference=transaction_reference,
                recorded_by=request.user
            )
            messages.success(request, f"Payment of ZMK {amount} successfully logged for Booking #{booking.id}.")
            return redirect('dashboards:accountant_home')

        except Exception as e:
            messages.error(request, f"Error processing payment: {str(e)}")

    return render(request, 'dashboards/record_payment.html', {'booking': booking})


@login_required
def log_expense_view(request):
    """
    View for logging operational expenses (e.g., fuel, supplies, maintenance).
    """
    categories = ExpenseCategory.objects.all()

    if request.method == 'POST':
        category_id = request.POST.get('category')
        title = request.POST.get('title')
        amount = request.POST.get('amount')
        vendor_supplier = request.POST.get('vendor_supplier', '')
        expense_date = request.POST.get('expense_date', date.today())
        receipt_doc = request.FILES.get('receipt_doc')

        category = get_object_or_404(ExpenseCategory, id=category_id)

        Expense.objects.create(
            category=category,
            title=title,
            amount=amount,
            vendor_supplier=vendor_supplier,
            expense_date=expense_date,
            receipt_doc=receipt_doc,
            approved_by=request.user
        )
        messages.success(request, f"Expense '{title}' recorded successfully.")
        return redirect('dashboards:accountant_home')

    return render(request, 'dashboards/log_expense.html', {'categories': categories})


@login_required
def add_expense_category_view(request):
    """
    Handles inline modal submission from accountant_home to quickly register new categories.
    """
    if request.method == 'POST':
        category_name = request.POST.get('name')
        if category_name:
            clean_name = category_name.strip()
            category, created = ExpenseCategory.objects.get_or_create(name=clean_name)
            if created:
                messages.success(request, f"Expense Category '{clean_name}' created successfully.")
            else:
                messages.warning(request, f"Category '{clean_name}' already exists.")
    
    return redirect('dashboards:accountant_home')


@login_required
def manage_expense_categories_view(request):
    """
    Dedicated view for Accountants/Managers to list and manage expense categories.
    """
    if request.method == 'POST':
        category_name = request.POST.get('name')
        if category_name:
            clean_name = category_name.strip()
            ExpenseCategory.objects.get_or_create(name=clean_name)
            messages.success(request, f"Category '{clean_name}' created successfully.")
            return redirect('dashboards:manage_expense_categories')

    categories = ExpenseCategory.objects.all()
    return render(request, 'dashboards/manage_expense_categories.html', {'categories': categories})

