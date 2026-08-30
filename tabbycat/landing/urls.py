from django.urls import path
from . import views

app_name = 'landing'
urlpatterns = [
    path('', views.LandingPageView.as_view(), name='home'),
    path('pricing/', views.PricingView.as_view(), name='pricing'),
    path('features/', views.FeaturesView.as_view(), name='features'),
    path('contact/', views.ContactView.as_view(), name='contact'),
]
