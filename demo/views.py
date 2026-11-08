from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, DeleteView
from .models import Message, UserIPHistory
from .forms import MessageForm
from django.urls import reverse, reverse_lazy
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth import logout, login
from django.contrib import messages
from .forms import CustomUserCreationForm
import os
import re
import json
import requests
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from cryptography.fernet import Fernet
from django.conf import settings
import logging
from google import genai
from .ai_service import get_gemini_code_answer
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.contrib.auth.models import User
from .utils import get_client_ip
from django.conf import settings

logger = logging.getLogger(__name__)

# Discord Environment Variables

# WEBHOOK_1 = os.environ.get('DISCORD_WEBHOOK_CHANNEL_1')
# WEBHOOK_2 = os.environ.get('DISCORD_WEBHOOK_CHANNEL_2')

# CHANNEL_TO_ROOM = {
#     "1536838651273814134": "1",
#     "1536840542359519242": "2"
#     }


# Create your views here.
# class TestView(CreateView):
#     model = Message
#     template_name = "demo/chat.html"
#     form_class = MessageForm
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["messages"] = Message.objects.all()
#         return context

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user_ip = get_client_ip(request)

            # Option A: Strict check - block if this IP was EVER recorded by any account
            # if UserIPHistory.objects.filter(ip_address=user_ip).exists():
            #     messages.error(request, 'Registration is unavailable from this IP Address.')
            #     return render(request, 'demo/register.html', {'form': form})

            # Option B: Time-windowed check - block if used in the past 7 days
            # time_threshold = timezone.now() - timedelta(days=7)
            # if UserIPHistory.objects.filter(ip_address=user_ip, created_at__gte=time_threshold).exists():
            #     messages.error(request, 'An account was recently registered from this network. Try again later.')
            #     return render(request, 'register.html', {'form': form})

            user = form.save()
            user.is_active = False
            user.save()

            UserIPHistory.objects.create(user=user, ip_address=user_ip)
            # Optional: automatically log in the user after registration
            # login(request, user)
            username = form.cleaned_data.get('username')
            current_site = get_current_site(request)
            mail_subject = 'Activate your account.'
            message = render_to_string('demo/acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(mail_subject, message, to=[to_email])
            email.send()
            messages.success(request, f'Account created for {username}. Please check your email in order to complete verification.')
            return redirect('login') # Redirect to your login page
    else:
        form = CustomUserCreationForm()
    return render(request, 'demo/register.html', {'form': form})

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, f'Email successfully verified! You can now log in')
        return redirect('login')
    else:
        return HttpResponse('Activation link is invalid!')


# @login_required()
# def create_message(request):
#     if request.method == 'POST':
#         form = MessageForm(request.POST)
#         if form.is_valid():
#             message = form.save(commit=False)
#             message.sender = request.user
#             message.save()
#             return redirect(reverse('chat')) # render(request, 'demo/chat.html', {'form':form, 'messages': Message.objects.all()})
#     else:
#         form = MessageForm()

#     return render(request, 'demo/chat.html', {'form':form, 'chat_messages': Message.objects.all(), 'user': request.user})
@login_required()
def create_message(request, room_id='1536838651273814134'):
    # --- ADMIN SECURITY CHECK ---
    if room_id == '1536840542359519242' and not request.user.is_staff:
        # Send them back to the general chat if they aren't an admin
        return redirect('chat', room_id='1536838651273814134')
    # ----------------------------
    if request.method == 'POST':
        user_email = (request.user.email or '').strip().lower()
        logger.warning("POST request received from email='%s' in room_id='%s'", user_email, room_id)
        banned_emails = {email.lower() for email in getattr(settings, 'QA_BANNED_USERS', [])}
        logger.warning(str(banned_emails))

        if user_email in banned_emails:
            logger.warning("Blocked banned user submission: email='%s', room_id='%s'", user_email, room_id)
            messages.error(request, "You are banned from sending messages.")
            return redirect('chat', room_id=room_id)
        else:
            form = MessageForm(request.POST)
            if form.is_valid():
                message = form.save(commit=False)
                message.sender = request.user
                # Automatically assign the room_id from the URL
                message.channel_id = room_id
                if room_id == "bug-report":
                    message.delivered = True
                message.save()
                # Redirect back to the exact room they are in
                return redirect('chat', room_id=room_id)
    else:
        form = MessageForm()

    # Filter the database to ONLY grab messages for this specific room
    room_messages = Message.objects.filter(channel_id=room_id).order_by('timestamp')

    return render(request, 'demo/chat.html', {
        'form': form,
        'chat_messages': room_messages,
        'room_id': room_id, # Pass the room ID to the HTML template
        'user': request.user
    })

def chat_messages_partial(request, room_id):
    # Fetch messages for the given room
    messages = Message.objects.filter(channel_id=room_id).order_by('timestamp')
    return render(request, 'demo/messages_partial.html', {'chat_messages': messages})

def home_view(request):
    return render(request, 'demo/home.html', {'user': request.user})

def logout_request(request):
    logout(request)
    return redirect(reverse('home'))

class DeleteMessage(PermissionRequiredMixin, DeleteView):
    permission_required = 'is_staff'

    model = Message
    # form_class = MessageForm
    template_name = "demo"
    def get_success_url(self):
        return reverse('chat', kwargs={'room_id': self.object.channel_id})
    # success_url = reverse_lazy('chat', kwargs={'room_id': f'self.object.channel_id'})

def soundboard(request):
    return render(request, 'demo/sounds.html')

@csrf_exempt
def bridge_api(request):
    if request.method == 'POST' and request.content_type == 'application/json':
        try:
            KEY = settings.ENCRYPTION_KEY.encode()
            cipher = Fernet(KEY)

            enc_data = json.loads(request.body)
            encrypted_payload = enc_data.get('payload')
            # room_id = CHANNEL_TO_ROOM[channel_id]

            decrypted_str = cipher.decrypt(encrypted_payload.encode()).decode()
            data = json.loads(decrypted_str)
            dest_id = enc_data.get('channel_id', 'Unknown')
            if dest_id.startswith("15368"):
                # Save the message coming from Discord
                Message.objects.create(
                    message_text=data['content'],
                    external_sender=data['username'],
                    channel_id=dest_id,
                    delivered=True
                )

            return JsonResponse({'status': 'Message saved!'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Method not allowed'}, status=405)



cipher = Fernet(settings.ENCRYPTION_KEY.encode())

@csrf_exempt
@require_GET
def pending_messages(request):
    pending = (
        Message.objects
        .filter(delivered=False)
        .order_by("timestamp")[:50]
    )

    if not pending:
        return JsonResponse({"payload": None})

    data = [
        {
            "id": m.id,
            "channel_id": m.channel_id,
            "content": m.message_text,
            "username": re.sub(re.escape("evren"), "iDragon", m.sender.username, flags=re.IGNORECASE),
        }
        for m in pending
    ]

    encrypted = cipher.encrypt(json.dumps(data).encode()).decode()
    return JsonResponse({"payload": encrypted})


@csrf_exempt
@require_POST
def mark_delivered(request):
    try:
        body = json.loads(request.body)
        encrypted_payload = body.get("payload")
        decrypted = cipher.decrypt(encrypted_payload.encode()).decode()
        ids = json.loads(decrypted).get("ids", [])
    except Exception:
        return JsonResponse({"error": "bad request"}, status=400)

    if not ids:
        return JsonResponse({"ok": True, "updated": 0})

    updated = Message.objects.filter(id__in=ids).update(delivered=True)
    return JsonResponse({"ok": True, "updated": updated})

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
@login_required
def code_review_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            code = data.get('code', '')
            language = data.get('language', 'python')

            if not code.strip():
                return JsonResponse({'status': 'error', 'message': 'Code is empty.'})

            # Craft a safe, helpful prompt for the AI
            prompt = f"""
            You are a helpful coding mentor for a high school programming club.
            Please review the following {language} code. Keep your feedback concise, encouraging, and easy to understand.
            Point out any bugs, suggest improvements, or mention best practices. Do not rewrite the entire program for them, just guide them.

            Code:
            {code}
            """

            response = client.models.generate_content(
                model='gemini-3.5-flash-lite',
                contents=prompt,
            )

            return JsonResponse({'status': 'success', 'review': response.text})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})

@login_required()
def create_message(request, room_id='1536838651273814134'):
    # --- ADMIN SECURITY CHECK ---
    if room_id == '1536840542359519242' and not request.user.is_staff:
        return redirect('chat', room_id='1536838651273814134')
    # ----------------------------

    if request.method == 'POST':
        if room_id == 'ai-assistant':
            # Handle AI Q&A Submission
            question = request.POST.get("message_text", "").strip()
            code_snippet = request.POST.get("code_snippet", "").strip()
            selected_file = request.POST.get("selected_file", "").strip()

            if question:
                # 1. Save the user's question so it appears in the chat
                Message.objects.create(
                    sender=request.user,
                    message_text=question,
                    channel_id=room_id,
                    delivered=True
                )

                # 2. Ask Gemini
                ai_response = get_gemini_code_answer(question, code_snippet, selected_file)

                # 3. Save Gemini's response
                Message.objects.create(
                    external_sender="Gemini AI 🤖",
                    message_text=ai_response,
                    channel_id=room_id,
                    delivered=True
                )
            return redirect('chat', room_id=room_id)

        else:
            # Handle Standard Chat Submission
            form = MessageForm(request.POST)
            if form.is_valid():
                message = form.save(commit=False)
                message.sender = request.user
                message.channel_id = room_id
                if room_id == "bug-report":
                    message.delivered = True
                message.save()
                return redirect('chat', room_id=room_id)
    else:
        form = MessageForm()

    room_messages = Message.objects.filter(channel_id=room_id).order_by('timestamp')

    return render(request, 'demo/chat.html', {
        'form': form,
        'chat_messages': room_messages,
        'room_id': room_id,
        'user': request.user
    })