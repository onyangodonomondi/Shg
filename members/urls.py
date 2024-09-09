from django.urls import path
from . import views
from .views import CustomPasswordResetView, CustomLoginView, manage_events, manage_contributions
from django.contrib.auth import views as auth_views
from .views import member_contributions_json

urlpatterns = [
    # Home Page
    path('', views.home, name='home'),
    path('lineage/', views.lineage_view, name='lineage'),
    path('member-contributions-json/', member_contributions_json, name='member_contributions_json'),

    # Event Management
    path('events/', views.events_page, name='events_page'),
    path('manage/events/', manage_events, name='manage_events'),
    path('members/', views.members_page, name='members_page'),

    # Member Registration & Profile
    path('register/', views.signup, name='register_member'),
    path('profile/<int:user_id>/', views.profile, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),

    # Contributions
    path('contributions/', views.contributions_page, name='contributions_page'),
    path('manage/contributions/', manage_contributions, name='manage_contributions'),

    # Export Contributions (PDF & Excel)
    path('export/pdf/', views.export_contributions_pdf, name='export_contributions_pdf'),
    path('export/excel/', views.export_contributions_excel, name='export_contributions_excel'),

    # Members Page
    path('members/', views.members_page, name='members'),

    # Authentication URLs
    path('login/', CustomLoginView.as_view(), name='login'),  # Correct login path
    path('logout/', auth_views.LogoutView.as_view(template_name='logout.html'), name='logout'),
    path('signup/', views.signup, name='signup'),

    # Password Reset URLs
    path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='custom_password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='custom_password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='custom_password_reset_complete.html'), name='password_reset_complete'),
]