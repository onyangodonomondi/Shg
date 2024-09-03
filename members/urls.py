from django.urls import path
from . import views
from .views import CustomPasswordResetView, CustomLoginView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'), 
    path('events/', views.events_page, name='events_page'),
    path('register/', views.signup, name='register_member'),
    path('contributions/', views.contributions_page, name='contributions_page'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/<int:user_id>/', views.profile, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),

    # Members and Contributions URLs
    path('members/', views.members_page, name='members'),

    # Export URLs
    path('export/pdf/', views.export_contributions_pdf, name='export_contributions_pdf'),
    path('export/excel/', views.export_contributions_excel, name='export_contributions_excel'),
    
    # Authentication URLs
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='logout.html'), name='logout'),
    path('signup/', views.signup, name='signup'),  # Custom signup view
    path('profile/', views.profile, name='profile'),

    # Password reset URLs
    path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='custom_password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='custom_password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='custom_password_reset_complete.html'), name='password_reset_complete'),
    
    # Account profile URL
    path('accounts/profile/', views.profile, name='profile'),
]
