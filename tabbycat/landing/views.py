from django.views.generic import TemplateView
from billing.models import Plan

class LandingPageView(TemplateView):
    template_name = 'landing/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['plans'] = Plan.objects.filter(is_active=True)
        return context

class PricingView(TemplateView):
    template_name = 'landing/pricing.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['plans'] = Plan.objects.filter(is_active=True)
        return context

class FeaturesView(TemplateView):
    template_name = 'landing/features.html'
    
class ContactView(TemplateView):
    template_name = 'landing/contact.html'
