from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Tag, Assignment, Meeting, UserAssignment
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime
import json
from django.http import JsonResponse
import os

User = get_user_model()

# Create your views here.

def send_assignment_email(user, assignment):
    """Sends an email notification to a user when assigned to a problem."""
    if not user.email:
        return

    # Safely format due_date across datetime objects, ISO strings, or None
    due_date_str = "No due date"
    if assignment.due_date:
        if hasattr(assignment.due_date, 'strftime'):
            due_date_str = assignment.due_date.strftime('%b %d, %Y at %I:%M %p')
        elif isinstance(assignment.due_date, str):
            try:
                dt = datetime.fromisoformat(assignment.due_date)
                due_date_str = dt.strftime('%b %d, %Y at %I:%M %p')
            except ValueError:
                due_date_str = assignment.due_date

    subject = f"New Assignment: {assignment.title}"
    message = (
        f"Hi {user.username},\n\n"
        f"You have been assigned to a new programming assignment: '{assignment.title}'.\n\n"
        f"Platform: {assignment.get_platform_display()}\n"
        f"Due Date: {due_date_str}\n\n"
        f"Log in to your student dashboard to review and solve it!\n"
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'webmaster@localhost'),
        recipient_list=[user.email],
        fail_silently=True,  # Prevents 500 error if SMTP service fails temporarily
    )

@login_required
def dashboard(request):
    now = timezone.now()
    user = request.user

    # Fetch all user assignments
    user_assignments = UserAssignment.objects.filter(user=user).select_related("assignment").prefetch_related("assignment__tags")

    all_assignments = list(user_assignments)

    # 1. Attach a computed category for the single loop
    for ua in all_assignments:
        a = ua.assignment
        if ua.status == UserAssignment.Status.COMPLETE:
            ua.computed_category = 'completed'
        elif ua.status == UserAssignment.Status.IN_PROGRESS:
            ua.computed_category = 'in_progress'
        elif not a.is_required:
            ua.computed_category = 'optional'
        elif a.due_date and a.due_date < now:
            ua.computed_category = 'overdue'
        else:
            ua.computed_category = 'upcoming'

    # 2. Sort so critical items appear first when viewing "All"
    category_priority = {'overdue': 0, 'in_progress': 1, 'upcoming': 2, 'optional': 3, 'completed': 4}
    # Sort by priority, then by due date (putting items without due dates last within their group)
    max_date = timezone.make_aware(timezone.datetime.max)
    all_assignments.sort(key=lambda x: (category_priority[x.computed_category], x.assignment.due_date or max_date))

    upcoming_meetings = Meeting.objects.filter(date__gte=now.date())
    past_meetings = Meeting.objects.filter(date__lt=now.date())
    missed_meetings = past_meetings.exclude(attended_users=user).order_by("-date")

    context = {
        'all_assignments': all_assignments,
        'upcoming_meetings': upcoming_meetings,
        'missed_meetings': missed_meetings,
        'tags': Tag.objects.all(),
        'platforms': Assignment._meta.get_field('platform').choices,
        'all_users': User.objects.all(),
    }

    return render(request, 'portal/dashboard.html', context)

@staff_member_required
def add_assignment(request):
    if request.method == 'POST':
        assignment = Assignment.objects.create(
            title=request.POST.get('title'),
            platform=request.POST.get('platform'),
            description=request.POST.get('description'),
            due_date=request.POST.get('due_date') or None,
            url=request.POST.get('url'),
            is_required=request.POST.get('is_required') == 'True'
        )

        tag_ids = request.POST.getlist('tags')
        if tag_ids:
            assignment.tags.set(tag_ids)

        assigned_user_ids = request.POST.getlist('assigned_users') or [request.user.id]

        # Create through model records for each user
        UserAssignment.objects.bulk_create([
            UserAssignment(user_id=uid, assignment=assignment) for uid in assigned_user_ids
        ])

        assigned_users = User.objects.filter(id__in=assigned_user_ids)
        for user in assigned_users:
            send_assignment_email(user, assignment)

        return redirect('dashboard')

    return redirect('dashboard')

@staff_member_required
def edit_assignment(request, assignment_id):
    if request.method == 'POST':
        assignment = get_object_or_404(Assignment, pk=assignment_id)

        assignment.title = request.POST.get('title')
        assignment.platform = request.POST.get('platform')
        assignment.description = request.POST.get('description')
        assignment.due_date = request.POST.get('due_date') or None
        assignment.url = request.POST.get('url')
        assignment.is_required = request.POST.get('is_required') == 'True'

        tag_ids = request.POST.getlist('tags')
        if tag_ids:
            assignment.tags.set(tag_ids)

        assignment.save()
        assignment.refresh_from_db()

        # Update assigned users
        new_user_ids = set(int(uid) for uid in request.POST.getlist('assigned_users'))
        current_user_ids = set(assignment.assigned_users.values_list('id', flat=True))

        # Add newly assigned users
        users_to_add = new_user_ids - current_user_ids
        UserAssignment.objects.bulk_create([
            UserAssignment(user_id=uid, assignment=assignment) for uid in users_to_add
        ])

        # Remove unselected users
        users_to_remove = current_user_ids - new_user_ids
        UserAssignment.objects.filter(assignment=assignment, user_id__in=users_to_remove).delete()

        newly_assigned_users = User.objects.filter(id__in=users_to_add)
        for user in newly_assigned_users:
            send_assignment_email(user, assignment)

        return redirect('dashboard')

    return redirect('dashboard')


@staff_member_required
def add_meeting(request):
    if request.method == 'POST':
        topic = request.POST.get('topic')
        date = request.POST.get('date')
        description = request.POST.get('description', '')
        recap_video_1 = request.POST.get('recap_video_1', '')
        recap_video_2 = request.POST.get('recap_video_2', '')
        recap_video_3 = request.POST.get('recap_video_3', '')

        Meeting.objects.create(
            topic=topic,
            date=date,
            description=description,
            recap_video_1=recap_video_1,
            recap_video_2=recap_video_2,
            recap_video_3=recap_video_3,
        )

        return redirect('dashboard')

    return redirect('dashboard')

@staff_member_required
def record_attendance(request, meeting_id):
    if request.method == 'POST':
        meeting = get_object_or_404(Meeting, pk=meeting_id)
        attended_user_ids = request.POST.getlist('attended_users')

        # Sync selected user IDs to the ManyToMany field
        meeting.attended_users.set(attended_user_ids)
        return redirect('dashboard')

    return redirect('dashboard')

@staff_member_required
def delete_assignment(request, assignment_id):
    if request.method == 'POST':
        assignment = get_object_or_404(Assignment, pk=assignment_id)
        assignment.delete()
    return redirect('dashboard')

@staff_member_required
def delete_meeting(request, meeting_id):
    if request.method == 'POST':
        meeting = get_object_or_404(Meeting, pk=meeting_id)
        meeting.delete()
    return redirect('dashboard')

@staff_member_required
def edit_meeting(request, meeting_id):
    if request.method == 'POST':
        meeting = get_object_or_404(Meeting, pk=meeting_id)
        meeting.topic = request.POST.get('topic')
        meeting.date = request.POST.get('date')
        meeting.description = request.POST.get('description', '')
        meeting.recap_video_1 = request.POST.get('recap_video_1', '')
        meeting.recap_video_2 = request.POST.get('recap_video_2', '')
        meeting.recap_video_3 = request.POST.get('recap_video_3', '')
        meeting.save()
        return redirect('dashboard')

    return redirect('dashboard')

def test(request):

    context = {
        "user": request.user
    }

    return render(request, "vocab/evren-isee-vocab-v1.2.html", context)

@user_passes_test(lambda u: u.is_superuser)
def save_progress(request):
    file_path = os.path.join(settings.BASE_DIR, 'portal/templates/vocab/progress.json')

    if request.method == 'POST':
        data = json.loads(request.body)
        with open(file_path, 'w') as f:
            json.dump(data, f)
        return JsonResponse({'status': 'saved'})
    return JsonResponse({'error': 'bad request'}, status=400)

@user_passes_test(lambda u: u.is_superuser)
def load_progress(request):
    file_path = os.path.join(settings.BASE_DIR, 'portal/templates/vocab/progress.json')

    # Check if the file exists yet
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
        return JsonResponse(data) # Django automatically formats this as JSON
    else:
        # If no progress exists yet, return an empty dictionary or default state
        return JsonResponse({})
