from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.dashboard, name="dashboard"),
    path('add-assignment/', views.add_assignment, name='add_assignment'),
    path('add-meeting/', views.add_meeting, name='add_meeting'),
    path('meetings/<int:meeting_id>/attendance/', views.record_attendance, name='record_attendance'),
    path('delete-assignment/<int:assignment_id>/', views.delete_assignment, name='delete_assignment'),
    path('delete-meeting/<int:meeting_id>/', views.delete_meeting, name='delete_meeting'),
    path('edit-assignment/<int:assignment_id>/', views.edit_assignment, name='edit_assignment'),
    path('edit-meeting/<int:meeting_id>/', views.edit_meeting, name='edit_meeting'),

    path('vocab', views.test, name='vocab'),
    path('vocab/save-progress/', views.save_progress, name='save_progress'),
    path('vocab/load-progress/', views.load_progress, name='load_progress'),
]