from django.urls import path
from .views import central_dashboard_router
from .views import receptionist_views, accountant_views, chef_views, stores_views, manager_views

urlpatterns = [
    path('', central_dashboard_router, name='dashboard_hub'),

    # Explicit role routing paths: Receptionist
    path('receptionist/', receptionist_views.dashboard_home, name='receptionist_home'),
    path('receptionist/book/', receptionist_views.create_walkin_booking, name='create_walkin_booking'),
    path('receptionist/checkout/<int:booking_id>/', receptionist_views.checkout_guest, name='checkout_guest'), # 🌟 Added target checkout hook
    path('receptionist/clean-room/<int:room_id>/', receptionist_views.clean_room_complete, name='clean_room_complete'),

    # Explicit role routing paths: Other Departments
    path('accountant/', accountant_views.dashboard_home, name='accountant_home'),
    path('chef/', chef_views.dashboard_home, name='chef_home'),
    path('stores/', stores_views.dashboard_home, name='stores_home'),
    path('manager/', manager_views.dashboard_home, name='manager_home'),
    
     # Explicit role routing paths: Stores / Inventory
    path('stores/', stores_views.dashboard_home, name='stores_home'),
    path('stores/adjust-stock/', stores_views.adjust_stock, name='adjust_stock'),
    path('stores/lost-found/', stores_views.manage_lost_found, name='manage_lost_found'),
    path('stores/borrowing/', stores_views.manage_borrowing, name='manage_borrowing'),
]