from django.urls import path
from . import views

app_name = 'superadmin'

urlpatterns = [
    # Dashboard
    path('', views.SuperAdminDashboardView.as_view(), name='dashboard'),

    # Tenants
    path('tenants/', views.TenantListView.as_view(), name='tenant-list'),
    path('tenants/create/', views.TenantCreateView.as_view(), name='tenant-create'),
    path('tenants/<int:pk>/', views.TenantDetailView.as_view(), name='tenant-detail'),
    path('tenants/<int:pk>/edit/', views.TenantUpdateView.as_view(), name='tenant-edit'),
    path('tenants/<int:pk>/toggle-active/', views.TenantToggleActiveView.as_view(), name='tenant-toggle-active'),

    # Plans
    path('plans/', views.PlanListView.as_view(), name='plan-list'),
    path('plans/create/', views.PlanCreateView.as_view(), name='plan-create'),
    path('plans/<int:pk>/edit/', views.PlanUpdateView.as_view(), name='plan-edit'),
    path('plans/<int:pk>/delete/', views.PlanDeleteView.as_view(), name='plan-delete'),

    # Subscriptions
    path('subscriptions/', views.SubscriptionListView.as_view(), name='subscription-list'),
    path('subscriptions/<int:pk>/edit/', views.SubscriptionUpdateView.as_view(), name='subscription-edit'),

    # Payments & Verification
    path('payments/', views.PaymentListView.as_view(), name='payment-list'),
    path('payments/<int:pk>/', views.PaymentDetailView.as_view(), name='payment-detail'),
    path('payments/<int:pk>/verify/', views.PaymentVerifyView.as_view(), name='payment-verify'),
    path('payments/<int:pk>/reject/', views.PaymentRejectView.as_view(), name='payment-reject'),

    # Tournaments & Users
    path('tournaments/', views.GlobalTournamentListView.as_view(), name='tournament-list'),
    path('users/', views.GlobalUserListView.as_view(), name='user-list'),
]
