# your_app/management/commands/run_cleanup.py
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from datetime import datetime as dt
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

def send_broadcast_email(subject, body_plaintext, body_html=None):
    # 1. Fetch all user email addresses (excluding empty fields)
    User = get_user_model()
    bcc_recipients = list(
        User.objects.filter(is_active=True)
        .exclude(email="")
        .values_list("email", flat=True)
    )

    if not bcc_recipients:
        return "No users found to email."

    current_recipient_list=[]
    for recipient in bcc_recipients:
        current_recipient_list.append(recipient)

        if len(current_recipient_list) == 19 or recipient == bcc_recipients[-1]:
            # 2. Construct and send the email
            email = EmailMultiAlternatives(
                subject=subject,
                body=body_plaintext,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[settings.DEFAULT_FROM_EMAIL], # Best practice: put yourself in the 'To' field
                bcc=current_recipient_list,
            )
            current_recipient_list = []

            if body_html:
                email.attach_alternative(body_html, "text/html")

            email.send(fail_silently=False)

class Command(BaseCommand):
    help = "Handles all daily updates"


    def handle(self, *args, **options):
        # Your task logic goes here
        now = dt.now()
        dotw = now.weekday()

        # --- Send Meeting Reminder ---
        if dotw == 0:
            subject = f"Programming Club Meeting Reminder"
            message_plain = """Hi everybody,
I just want to remind you all that we will have a programming club meeting as usual tomorrow during lunch in room 3101.
Sincerely,
Evren

--
Evren Kececioglu
Awty MS Programming Club Founder"""

            message_html = """<div style="font-family: sans-serif;">
  <p>Hi everybody,</p>
  <p>I just want to remind you all that we will have a programming club meeting as usual tomorrow during lunch in room 3101.</p>
  <p>Sincerely,<br>
  Evren</p>
  <br><br>
  <div style="color: gray;">
    --<br>
    Evren Kececioglu
  </div>
  <div style="color: darkgreen; font-weight: bold;">
    Awty MS Programming Club Founder
  </div>
</div>"""

        send_broadcast_email(subject, message_plain, message_html)



        # --- Send Assignment Reminder ---


        # --- Send Leaderboard Stats (In Progress) ---

        self.stdout.write("Successfully ran scheduled task!")
