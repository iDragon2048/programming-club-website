from django import forms
from .models import CodeFile

class CodeFileForm(forms.ModelForm):
    class Meta:
        model = CodeFile
        fields = ['title', 'code']
        widgets = {
            'code': forms.Textarea(attrs={'id': 'code-editor-textarea'}),
        }