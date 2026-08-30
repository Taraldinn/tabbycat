from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('checkout/<int:subscription_id>/', views.PaymentCheckoutView.as_view(), name='checkout'),
    path('status/<int:subscription_id>/', views.PaymentStatusView.as_view(), name='status'),
]
