from django.shortcuts import render
from django.views.generic import TemplateView, CreateView
from django.contrib.auth.models import User

# Create your views here.
class TestView(CreateView):
    template_name = "pyquiz/base_quiz.html"

    def get_context_data(self):
        context = super().get_context_data()
        context['members'] = User.objects.all()
        return context

