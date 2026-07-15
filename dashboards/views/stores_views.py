from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from stock_overview.models import Category, InventoryItem, StockTransaction, LostAndFound, BorrowedItem
from django.db.models import Sum
from datetime import date

@login_required
def dashboard_home(request):
    # Fetch all items & categories
    categories = Category.objects.all()
    items = InventoryItem.objects.select_related('category').all()
    
    # Smart warnings & aggregates
    low_stock_items = [item for item in items if item.is_low_stock]
    total_value = sum(item.total_value for item in items)
    
    # Lost & Found / Borrow sub-ledgers
    active_lost_found = LostAndFound.objects.filter(status='FOUND').order_index_by('-found_date') if hasattr(LostAndFound.objects, 'order_index_by') else LostAndFound.objects.filter(status='FOUND').order_by('-found_date')
    active_loans = BorrowedItem.objects.filter(is_returned=False).order_by('expected_return_date')
    
    # Dynamic Transaction Log (Recent 10)
    recent_transactions = StockTransaction.objects.select_related('item', 'reported_by').all().order_by('-created_at')[:10]

    context = {
        'categories': categories,
        'items': items,
        'low_stock_items': low_stock_items,
        'total_value': total_value,
        'active_lost_found': active_lost_found,
        'active_loans': active_loans,
        'recent_transactions': recent_transactions,
    }
    return render(request, 'dashboards/stores_home.html', context)


@login_required
def adjust_stock(request):
    """Processes quick inventory adjustments (Stock In, Issued, Damaged, Missing, Donated)"""
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        adjustment_type = request.POST.get('transaction_type')
        quantity_str = request.POST.get('quantity')
        notes = request.POST.get('notes', '')

        try:
            item = get_object_or_404(InventoryItem, id=item_id)
            qty = abs(float(quantity_str))
            
            # Inventory calculation logic
            if adjustment_type == 'ADD':
                item.quantity += qty
            elif adjustment_type in ['REMOVE', 'DAMAGE', 'MISSING', 'DONATION']:
                if item.quantity < qty:
                    messages.error(request, f"Insufficient stock! Available: {item.quantity} {item.unit}")
                    return redirect('stores_home')
                item.quantity -= qty
            
            item.save()

            # Record detailed transaction logs
            StockTransaction.objects.create(
                item=item,
                transaction_type=adjustment_type,
                quantity=qty,
                reported_by=request.user,
                notes=notes
            )
            messages.success(request, f"Successfully processed inventory adjustment for {item.name}.")
        except Exception as e:
            messages.error(request, f"Transaction failed: {str(e)}")

    return redirect('stores_home')


@login_required
def manage_lost_found(request):
    """Adds a newly found item or updates claim statuses."""
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            LostAndFound.objects.create(
                item_name=request.POST.get('item_name'),
                description=request.POST.get('description'),
                location_found=request.POST.get('location_found'),
                found_date=request.POST.get('found_date'),
                finder_name=request.POST.get('finder_name'),
                notes=request.POST.get('notes', '')
            )
            messages.success(request, "New found item logged into custody database.")
            
        elif action == 'claim':
            lf_id = request.POST.get('item_id')
            lf_item = get_object_or_404(LostAndFound, id=lf_id)
            lf_item.claimant_name = request.POST.get('claimant_name')
            lf_item.claimant_phone = request.POST.get('claimant_phone')
            lf_item.status = 'CLAIMED'
            lf_item.notes = f"Claimed on {date.today()}. " + lf_item.notes
            lf_item.save()
            messages.success(request, f"Item {lf_item.item_name} marked as claimed and handed over.")

    return redirect('stores_home')


@login_required
def manage_borrowing(request):
    """Processes checkout and return workflows for hotel properties."""
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'lend':
            BorrowedItem.objects.create(
                item_name=request.POST.get('item_name'),
                borrower_name=request.POST.get('borrower_name'),
                contact_info=request.POST.get('contact_info'),
                expected_return_date=request.POST.get('expected_return_date'),
                notes=request.POST.get('notes', '')
            )
            messages.success(request, "Loan asset record logged successfully.")
            
        elif action == 'return':
            loan_id = request.POST.get('loan_id')
            loan = get_object_or_404(BorrowedItem, id=loan_id)
            loan.is_returned = True
            loan.returned_date = date.today()
            loan.save()
            messages.success(request, f"Asset '{loan.item_name}' confirmed back in store inventory safely.")

    return redirect('stores_home')
