from . import views
from django.urls import path, include

urlpatterns = [
    path('', views.editor_view, name='editor'),
    path('list/', views.CodeFileList.as_view(), name='file_list'),
    path('edit/<pk>', views.UpdateFile.as_view(), name='file_edit')
]