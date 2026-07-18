from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q, DecimalField, ExpressionWrapper, F
from django.contrib.auth import get_user_model
from datetime import date
from decimal import Decimal

# Models
from rooms.models import Room, RoomTier
from bookings.models import Booking
from finance.models import Payment, Expense
from dashboards.models import Announcement, CalendarEvent

CustomUser = get_user_model()


def is_manager_or_admin(user):
    return user.is_staff or user.is_superuser or user.role in ['MANAGER', 'EXECUTIVE']


@login_required
def manager_home_view(request):
    """
    Central Executive Dashboard:
    High-level KPIs, operational stats across departments, announcements, and events.
    """
    if not is_manager_or_admin(request.user):
        messages.error(request, "Access denied. Manager privileges required.")
        return redirect('dashboards:dashboard_hub')

    # -------------------------------------------------------------
    # PRESENTATION MODE OVERRIDE (Handles ?view=ROLE query params)
    # -------------------------------------------------------------
    presentation_view = request.GET.get('view')
    if presentation_view:
        if presentation_view == 'RECEPTIONIST':
            return redirect('dashboards:receptionist_home')
        elif presentation_view == 'ACCOUNTANT':
            return redirect('dashboards:accountant_home')
        elif presentation_view == 'CHEF':
            return redirect('dashboards:chef_home')
        elif presentation_view == 'STORES_MANAGER':
            return redirect('dashboards:stores_home')
    # -------------------------------------------------------------

    today = date.today()

    # 1. High-Level Financial Summaries (Using Decimal('0.00') instead of floats)
    total_revenue = Payment.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    today_revenue = Payment.objects.filter(created_at__date=today).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    total_expenses = Expense.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Guaranteed Decimal arithmetic—no float type errors
    net_profit = total_revenue - total_expenses

    # 2. Occupancy & Room Analytics
    total_rooms = Room.objects.count()
    occupied_rooms = Room.objects.filter(status='OCCUPIED').count()
    dirty_rooms = Room.objects.filter(status='DIRTY').count()
    available_rooms = Room.objects.filter(status='AVAILABLE').count()

    occupancy_rate = (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0

    # 3. Recent Memos & Upcoming Events
    recent_announcements = Announcement.objects.all()[:5]
    upcoming_events = CalendarEvent.objects.filter(start_date__gte=today)[:5]
    
    # 4. Staff Overview
    staff_members = CustomUser.objects.exclude(role='GUEST').order_by('role')

    context = {
        'total_revenue': total_revenue,
        'today_revenue': today_revenue,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'total_rooms': total_rooms,
        'occupied_rooms': occupied_rooms,
        'dirty_rooms': dirty_rooms,
        'available_rooms': available_rooms,
        'occupancy_rate': round(occupancy_rate, 1),
        'recent_announcements': recent_announcements,
        'upcoming_events': upcoming_events,
        'staff_count': staff_members.count(),
    }

    return render(request, 'dashboards/manager_home.html', context)


@login_required
def staff_management_view(request):
    """
    Allows Managers to view all staff and register new staff members into the system.
    """
    if not is_manager_or_admin(request.user):
        messages.error(request, "Access denied.")
        return redirect('dashboards:dashboard_hub')

    staff_members = CustomUser.objects.exclude(role='GUEST').order_by('role')

    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        role = request.POST.get('role')
        password = request.POST.get('password')

        if CustomUser.objects.filter(phone_number=phone_number).exists():
            messages.error(request, f"User with phone number {phone_number} already exists.")
        else:
            try:
                user = CustomUser.objects.create_user(
                    phone_number=phone_number,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    role=role
                )
                if role in ['MANAGER', 'EXECUTIVE']:
                    user.is_staff = True
                    user.save()

                messages.success(request, f"Staff member {first_name} {last_name} ({role}) added successfully.")
                return redirect('dashboards:staff_management')
            except Exception as e:
                messages.error(request, f"Error creating staff member: {str(e)}")

    context = {
        'staff_members': staff_members,
        'roles': CustomUser.ROLE_CHOICES,
    }
    return render(request, 'dashboards/staff_management.html', context)


@login_required
def create_announcement_view(request):
    """
    Allows Manager to post system-wide or role-targeted announcements/memos.
    """
    if not is_manager_or_admin(request.user):
        messages.error(request, "Access denied.")
        return redirect('dashboards:dashboard_hub')

    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        target_role = request.POST.get('target_role', 'ALL')

        Announcement.objects.create(
            title=title,
            content=content,
            target_role=target_role,
            created_by=request.user
        )
        messages.success(request, f"Announcement '{title}' posted successfully.")
        return redirect('dashboards:manager_home')

    return render(request, 'dashboards/create_announcement.html', {
        'target_roles': Announcement.TARGET_ROLE_CHOICES
    })


@login_required
def calendar_events_view(request):
    """
    View and create events on the manager calendar.
    """
    if not is_manager_or_admin(request.user):
        messages.error(request, "Access denied.")
        return redirect('dashboards:dashboard_hub')

    events = CalendarEvent.objects.all()

    if request.method == 'POST':
        title = request.POST.get('title')
        event_type = request.POST.get('event_type')
        description = request.POST.get('description', '')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        CalendarEvent.objects.create(
            title=title,
            event_type=event_type,
            description=description,
            start_date=start_date,
            end_date=end_date,
            created_by=request.user
        )
        messages.success(request, f"Event '{title}' added to calendar.")
        return redirect('dashboards:calendar_events')

    context = {
        'events': events,
        'event_types': CalendarEvent.EVENT_TYPES,
    }
    return render(request, 'dashboards/calendar_events.html', context)


@login_required
def room_management_view(request):
    """
    Allows managers to adjust room tier pricing, change individual room status,
    and register new rooms/tiers.
    """
    if not is_manager_or_admin(request.user):
        messages.error(request, "Access denied.")
        return redirect('dashboards:dashboard_hub')

    tiers = RoomTier.objects.all().prefetch_related('rooms')
    rooms = Room.objects.select_related('tier').order_by('room_number')

    # Handle creating new room tiers or rooms directly
    if request.method == 'POST':
        action_type = request.POST.get('action_type')

        # Add New Room Tier
        if action_type == 'add_tier':
            name = request.POST.get('name')
            base_price = request.POST.get('base_price')
            description = request.POST.get('description', '')

            RoomTier.objects.create(
                name=name,
                base_price=base_price,
                description=description
            )
            messages.success(request, f"Room tier '{name}' created successfully.")
            return redirect('dashboards:room_management')

        # Add New Individual Room
        elif action_type == 'add_room':
            room_number = request.POST.get('room_number')
            tier_id = request.POST.get('tier_id')
            floor = request.POST.get('floor', 1)
            max_capacity = request.POST.get('max_capacity', 2)

            tier = get_object_or_404(RoomTier, id=tier_id)
            Room.objects.create(
                room_number=room_number,
                tier=tier,
                floor=floor,
                max_capacity=max_capacity
            )
            messages.success(request, f"Room {room_number} added successfully under {tier.name}.")
            return redirect('dashboards:room_management')

        # Update Individual Room Status (e.g., MAINTENANCE, DIRTY)
        elif action_type == 'update_room_status':
            room_id = request.POST.get('room_id')
            new_status = request.POST.get('status')
            
            room = get_object_or_404(Room, id=room_id)
            room.status = new_status
            room.save()
            messages.success(request, f"Room {room.room_number} status updated to {room.get_status_display()}.")
            return redirect('dashboards:room_management')

    context = {
        'tiers': tiers,
        'rooms': rooms,
        'room_statuses': Room.ROOM_STATUS,
    }
    return render(request, 'dashboards/room_management.html', context)


@login_required
def update_tier_price_view(request, tier_id):
    """
    Updates base nightly price for a specific RoomTier.
    """
    if not is_manager_or_admin(request.user):
        messages.error(request, "Access denied.")
        return redirect('dashboards:dashboard_hub')

    tier = get_object_or_404(RoomTier, id=tier_id)

    if request.method == 'POST':
        new_price = request.POST.get('base_price')
        if new_price:
            tier.base_price = new_price
            tier.save()
            messages.success(request, f"Updated rate for {tier.name} to ZMK {new_price}.")
        else:
            messages.error(request, "Invalid price provided.")

    return redirect('dashboards:room_management')

