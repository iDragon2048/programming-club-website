from django.urls import path, include
from . import views
from django.views.generic import RedirectView
# from django.contrib.auth import views as auth_views

urlpatterns = [
    path('chat/', RedirectView.as_view(url='/chat/1536838651273814134/')),
    path('chat/<str:room_id>/', views.create_message, name='chat'),
    path('chat/<str:room_id>/messages/', views.chat_messages_partial, name='chat_messages_partial'),
    path('', views.home_view, name="home"),
    path('logout/', views.logout_request, name='logoutr'),
    path('message/delete/<pk>', views.DeleteMessage.as_view(), name='delete_message'),
    path('sounds/', views.soundboard, name='sounds'),
    path('register/', views.register, name='register'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('api/bridge/', views.bridge_api, name='bridge_api'),
    path("api/pending-messages/", views.pending_messages, name="pending_messages"),
    path("api/mark-delivered/", views.mark_delivered, name="mark_delivered"),
    path('api/code-review/', views.code_review_api, name='code_review_api'),
    # path('ai-assistant/', views.ai_qa_view, name='ai_qa'),
]