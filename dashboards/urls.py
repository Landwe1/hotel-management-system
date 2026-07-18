from django.urls import path

from .views import (
    accountant_views,
    central_dashboard_router,
    chef_views,
    manager_views,
    receptionist_views,
    stores_views,
)

app_name = 'dashboards'


urlpatterns = [
    # Central Router Hub
    path('', central_dashboard_router, name='dashboard_hub'),

    # ---------------------------------------------------------
    # Receptionist Routes
    # ---------------------------------------------------------
    path('receptionist/', receptionist_views.dashboard_home, name='receptionist_home'),
    path('receptionist/book/', receptionist_views.create_walkin_booking, name='create_walkin_booking'),
    path('receptionist/checkout/<int:booking_id>/', receptionist_views.checkout_guest, name='checkout_guest'),
    path('receptionist/clean-room/<int:room_id>/', receptionist_views.clean_room_complete, name='clean_room_complete'),

    # ---------------------------------------------------------
    # Accountant & Finance Routes
    # ---------------------------------------------------------
    path('accountant/', accountant_views.accountant_dashboard, name='accountant_home'),
    path('accountant/payment/<int:booking_id>/', accountant_views.record_payment_view, name='record_payment'),
    path('accountant/expense/log/', accountant_views.log_expense_view, name='log_expense'),
    path('accountant/category/add/', accountant_views.add_expense_category_view, name='add_expense_category'),
    path('accountant/categories/', accountant_views.manage_expense_categories_view, name='manage_expense_categories'),

    # ---------------------------------------------------------
    # Stores / Inventory Routes
    # ---------------------------------------------------------
    path('stores/', stores_views.dashboard_home, name='stores_home'),
    path('stores/adjust-stock/', stores_views.adjust_stock, name='adjust_stock'),
    path('stores/lost-found/', stores_views.manage_lost_found, name='manage_lost_found'),
    path('stores/borrowing/', stores_views.manage_borrowing, name='manage_borrowing'),

    # ---------------------------------------------------------
    # Chef & Kitchen Routes
    # ---------------------------------------------------------
    path('chef/', chef_views.dashboard_home, name='chef_home'),

    # ---------------------------------------------------------
    # General Manager & Executive Routes
    # ---------------------------------------------------------
    path('manager/', manager_views.manager_home_view, name='manager_home'),
    path('manager/staff/', manager_views.staff_management_view, name='staff_management'),
    path('manager/rooms/', manager_views.room_management_view, name='room_management'),
    path('manager/rooms/tier/<int:tier_id>/update-price/', manager_views.update_tier_price_view, name='update_tier_price'),
    path('manager/announcements/create/', manager_views.create_announcement_view, name='create_announcement'),
    path('manager/calendar/', manager_views.calendar_events_view, name='calendar_events'),
]
