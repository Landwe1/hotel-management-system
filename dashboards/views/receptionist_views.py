from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from rooms.models import Room
from bookings.models import Booking
from datetime import datetime
from decimal import Decimal

@login_required
def dashboard_home(request):
    all_rooms = Room.objects.select_related('tier').order_by('room_number')
    active_bookings = Booking.objects.select_related('room', 'user').filter(
        status__in=['PENDING', 'CHECKED_IN']
    ).order_by('check_in_date')

    # Available rooms list specifically to populate our room selection dropdown
    available_dropdown = Room.objects.filter(status='AVAILABLE').order_by('room_number')

    context = {
        'rooms': all_rooms,
        'available_dropdown': available_dropdown,
        'bookings': active_bookings,
        'total_rooms': all_rooms.count(),
        'available_rooms': all_rooms.filter(status='AVAILABLE').count(),
        'occupied_rooms': all_rooms.filter(status='OCCUPIED').count(),
        'dirty_rooms': all_rooms.filter(status='DIRTY').count(),
    }
    return render(request, 'dashboards/receptionist_home.html', context)


@login_required
@require_POST
def create_walkin_booking(request):
    """Processes incoming form submission to instantaneously register a guest room booking with precise math."""
    room_id = request.POST.get('room_id')
    first_name = request.POST.get('first_name')
    last_name = request.POST.get('last_name')
    phone = request.POST.get('phone')
    
    # Parse string dates into Python date objects
    check_in_str = request.POST.get('check_in_date')
    check_out_str = request.POST.get('check_out_date')
    date_format = "%Y-%m-%d"
    
    check_in_date = datetime.strptime(check_in_str, date_format).date()
    check_out_date = datetime.strptime(check_out_str, date_format).date()
    
    # 1. Dynamically calculate nights spent
    nights = (check_out_date - check_in_date).days
    if nights <= 0:
        nights = 1 

    # 2. Fetch targeted room info and cross-reference rate
    room = Room.objects.select_related('tier').get(id=room_id)
    room_rate = room.tier.base_price
    computed_total = room_rate * nights

    # 3. Process cash collected
    raw_paid = request.POST.get('amount_paid', '0')
    amount_paid = Decimal(raw_paid) if raw_paid else Decimal('0.00')
    
    # Check if marked as fully paid or if amount matches the bill
    is_fully_paid = (request.POST.get('is_paid') == 'on') or (amount_paid >= computed_total)
    if is_fully_paid and amount_paid < computed_total:
        amount_paid = computed_total

    # 4. Save walk-in transaction details
    Booking.objects.create(
        room=room,
        guest_first_name=first_name,
        guest_last_name=last_name,
        guest_phone_fallback=phone,
        check_in_date=check_in_date,
        check_out_date=check_out_date,
        total_amount=computed_total,
        amount_paid=amount_paid,
        is_paid=is_fully_paid,
        status='CHECKED_IN'
    )

    # 5. Lock down room state status layout
    room.status = 'OCCUPIED'
    room.save()

    # Redirect directly without namespace path parameters
    return redirect('receptionist_home')


@login_required
def checkout_guest(request, booking_id):
    """Processes guest departure, marks booking settled, and flags room as dirty for housekeeping."""
    booking = get_object_or_404(Booking.objects.select_related('room'), id=booking_id)
    
    # 1. Finalize financial transactions and update booking status
    booking.status = 'CHECKED_OUT'
    booking.is_paid = True  
    booking.amount_paid = booking.total_amount  # Clear any remaining balances
    booking.save()
    
    # 2. Kick room to dirty state so cleaner roles see it on their screen
    room = booking.room
    room.status = 'DIRTY'
    room.save()
    
    return redirect('receptionist_home')

@login_required
def clean_room_complete(request, room_id):
    """Resets a dirty room back to available status once housekeeping is finished."""
    room = get_object_or_404(Room, id=room_id)
    if room.status == 'DIRTY':
        room.status = 'AVAILABLE'
        room.save()
    return redirect('receptionist_home')