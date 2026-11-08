from django import forms
from .models import Message
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ('message_text', )

        # Override the default widget to use a Textarea with custom attributes
        widgets = {
            'message_text': forms.Textarea(attrs={
                'rows': 1,
                'placeholder': 'Type a message...',
                'style': 'resize: none; overflow-y: hidden; box-sizing: border-box; min-height: 46px; padding-top: 14px; width: 100%;',
            })
        }

class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(
        max_length=30,  # Set your desired limit here
        help_text="Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only."
    )
    class Meta:
        model = User
        fields = ["username", "email"]
    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower()

        # Check domain
        if not email.endswith('@awty.org'):
            raise ValidationError("You must use an official @awty.org email address to register.")

        # Check if email is already taken
        if User.objects.filter(email=email).exists():
            raise ValidationError("An account with this email address already exists.")

        return email