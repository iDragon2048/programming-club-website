from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from .forms import CodeFileForm
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, UpdateView
from .models import CodeFile


# Create your views here.
@login_required
def editor_view(request):
    if request.method == 'POST':
        form = CodeFileForm(request.POST)
        if form.is_valid():
            saved_code = form.save(commit=False)
            saved_code.creator = request.user
            saved_code.save()
            return redirect(reverse('home'))
        else:
            print(form.errors)
    else:
        form = CodeFileForm()
    return render(request, 'code_interpreter/editor.html', {'form': form})

class CodeFileList(ListView):
    model = CodeFile
    template_name = 'code_interpreter/file_list.html'
    context_object_name = 'files'
    ordering = ['-creation_time']
    paginate_by = 10

class UpdateFile(UpdateView):
    model = CodeFile
    form_class = CodeFileForm
    template_name = 'code_interpreter/editor.html'
    success_url = reverse_lazy('file_list')