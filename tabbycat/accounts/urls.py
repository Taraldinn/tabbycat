from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.RegisterTenantView.as_view(), name='register'),
    path('onboarding-success/', views.TenantOnboardingSuccessView.as_view(), name='onboarding-success'),
    path('dashboard/', views.ClientDashboardView.as_view(), name='dashboard'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
]
