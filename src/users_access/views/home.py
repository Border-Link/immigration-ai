from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = 'user_access/welcome.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['app_title'] = 'Borderlink: Immigration Intelligence Platform'
        context['app_welcome'] = 'Welcome to Your Immigration Intelligence Platform'
        context['app_content'] = """The Immigration Intelligence Platform is a compliance-aware AI system 
        that helps immigration applicants understand their visa eligibility, prepare required documents, 
        and make informed decisions. The platform provides **decision support** and **information interpretation**—not 
        legal advice—through explainable AI and human-in-the-loop workflows."""
        return context