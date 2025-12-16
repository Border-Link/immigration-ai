from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = 'user_access/welcome.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['app_title'] = 'Cashra: Ai-Powered Finance Manager'
        context['app_welcome'] = 'Welcome to Your AI-Powered Finance Manager'
        context['app_content'] = """Take control of your finances with Cashra — a smart, 
        AI-driven platform designed to help you manage your money, track your spending, 
        and build a future of financial freedom."""
        return context