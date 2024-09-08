from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, FileResponse
from .forms import UserUpdateForm, ProfileUpdateForm, UserSignUpForm, EventForm, ContributionForm
from .models import Profile, Event, Contribution, Notification
from django.db.models import Sum, Count
from django.contrib.auth.views import PasswordResetView, LoginView
from django.urls import reverse_lazy
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
import io
import xlsxwriter
from reportlab.lib.units import inch
from datetime import datetime
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

from django.shortcuts import render
from django.db.models import Sum, Count
from .models import Contribution, Event
from django.core.paginator import Paginator
from django.http import JsonResponse
from random import choice
def home(request):
    # Fetch all contributions
    contributions = Contribution.objects.all()

    contributions_data = []

    for contribution in contributions:
        # Count the unique events for each profile
        event_count = Contribution.objects.filter(profile=contribution.profile).values('event').distinct().count()

        # Sum of all contributions for each profile
        total_contributions = Contribution.objects.filter(profile=contribution.profile).aggregate(Sum('amount'))['amount__sum'] or 0

        # Determine if the contribution is full based on event required amount
        required_amount = contribution.event.required_amount
        is_full = contribution.amount >= required_amount

        # Append the contribution data, including event count, total contributions, and full/partial status
        contributions_data.append({
            'profile': contribution.profile,
            'event': contribution.event,
            'amount': contribution.amount,
            'is_full': is_full,
            'event_count': event_count,
            'total_contributions': total_contributions
        })

    # Paginate the contributions (10 per page)
    paginator = Paginator(contributions_data, 10)  # Show 10 contributions per page

    # Get the current page number from the request
    page_number = request.GET.get('page')

    # Get the contributions for the current page
    page_obj = paginator.get_page(page_number)

    return render(request, 'members/home.html', {'page_obj': page_obj})

def lineage_view(request):
    # Get all profiles
    profiles = Profile.objects.all()

    # Group profiles by their father
    families = {}
    for profile in profiles:
        # If no father, they are the top-most individuals
        if profile.father is None:
            families[profile] = []
        else:
            # Add children under their respective fathers
            if profile.father not in families:
                families[profile.father] = []
            families[profile.father].append(profile)

    context = {
        'families': families,
    }
    return render(request, 'members/lineage.html', context)

def profile_detail(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    siblings = profile.get_siblings()
    context = {
        'profile': profile,
        'siblings': siblings,
    }
    return render(request, 'profile_detail.html', context)

@user_passes_test(lambda u: u.is_staff)
def manage_contributions(request):
    if request.method == 'POST':
        form = ContributionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('contributions_page')
        else:
            # Print form errors to console for debugging
            print(form.errors)
    else:
        form = ContributionForm()

    contributions = Contribution.objects.all()
    return render(request, 'members/manage_contributions.html', {'form': form, 'contributions': contributions})

@user_passes_test(lambda u: u.is_staff)
def manage_events(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('events_page')
        else:
            # Print form errors to console for debugging
            print(form.errors)
    else:
        form = EventForm()

    events = Event.objects.all()
    return render(request, 'members/manage_events.html', {'form': form, 'events': events})

@login_required
def profile(request, user_id):
    user = get_object_or_404(User, pk=user_id)  # Fetch the user by user_id
    contributions = Contribution.objects.filter(profile=user.profile)

    # Calculate total contributions
    total_contributed = contributions.aggregate(Sum('amount'))['amount__sum'] or 0

    # Determine time of day for greeting
    current_hour = datetime.now().hour
    if current_hour < 12:
        greeting_time = 'Good morning'
    elif 12 <= current_hour < 18:
        greeting_time = 'Good afternoon'
    else:
        greeting_time = 'Good evening'

    # Check if today is the user's birthday
    today = datetime.today().date()
    if user.profile.birthdate and user.profile.birthdate == today:
        greeting_message = f"Happy Birthday, {user.first_name}!"
    else:
        greeting_message = f"{greeting_time}, {user.first_name}!"

    # Total number of users
    total_users = Profile.objects.count()

    # Event contribution statistics
    event_contribution_stats = []
    events = Event.objects.all()
    for event in events:
        total_contributions = Contribution.objects.filter(event=event).aggregate(Sum('amount'))['amount__sum'] or 0
        contributors_count = Contribution.objects.filter(event=event).aggregate(Count('profile', distinct=True))['profile__count'] or 0
        event_contribution_stats.append({
            'event_name': event.name,
            'total_contributed': total_contributions,
            'contributors_count': contributors_count,
            'total_users': total_users
        })

    context = {
        'user_contributions': contributions,
        'total_contributed': total_contributed,
        'greeting_message': greeting_message,
        'event_contribution_stats': event_contribution_stats,
        'profile_user': user,  # Add this to refer to the profile's user
    }
    return render(request, 'profile.html', context)

@login_required
def update_profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect('profile', user_id=request.user.id)  # Pass user_id in redirect
    else:
        form = ProfileUpdateForm(instance=request.user.profile)

    return render(request, 'members/update_profile.html', {'form': form})

from django.core.paginator import Paginator

from django.shortcuts import render
from django.db.models import Sum, Count
from .models import Event, Contribution, Profile

from django.core.paginator import Paginator

def events_page(request):
    events = Event.objects.all()
    
    event_data = []
    for event in events:
        total_contributed = Contribution.objects.filter(event=event).aggregate(Sum('amount'))['amount__sum'] or 0
        contributor_count = Contribution.objects.filter(event=event).aggregate(Count('profile', distinct=True))['profile__count'] or 0

        event_data.append({
            'name': event.name,
            'date': event.date,
            'total_contributed': total_contributed,
            'contributor_count': contributor_count,
            'is_active': event.is_active
        })

    # Paginate the event data (5 events per page)
    paginator = Paginator(event_data, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'events': event_data,  # Pass event data to the template
        'total_events': len(events),
        'active_events': len([event for event in events if event.is_active]),
        'total_contributions': sum([e['total_contributed'] for e in event_data]),
        'total_contributors': sum([e['contributor_count'] for e in event_data]),
    }
    return render(request, 'events_page.html', context)

@login_required
def contributions_page(request):
    selected_event = request.GET.get('event')
    events = Event.objects.all()
    if selected_event:
        contributions = Contribution.objects.filter(event__name=selected_event)
    else:
        contributions = Contribution.objects.all()

    context = {
        'contributions': contributions,
        'events': events,
        'selected_event': selected_event,
    }
    return render(request, 'contributions_page.html', context)

def signup(request):
    if request.method == 'POST':
        form = UserSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Automatically log in the user
            login(request, user)
            # Redirect to the home page
            return redirect('home')
        else:
            # Print form errors to console for debugging
            print(form.errors)
    else:
        form = UserSignUpForm()

    return render(request, 'registration/signup.html', {'form': form})

class CustomPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset_form.html'
    success_url = reverse_lazy('password_reset_done')
    email_template_name = 'registration/password_reset_email.html'

class CustomLoginView(LoginView):
    template_name = 'login.html'

def members_page(request):
    profiles = Profile.objects.all()
    return render(request, 'members/members_page.html', {'profiles': profiles})

def export_contributions_pdf(request):
    selected_event = request.GET.get('event')
    if selected_event and selected_event != 'None':
        contributions = Contribution.objects.filter(event__name=selected_event)
    else:
        contributions = Contribution.objects.all()

    if not contributions.exists():
        return HttpResponse("No contributions found for export.", status=404)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    # Title
    title_style = getSampleStyleSheet()['Heading1']
    title_style.alignment = 1  # Center align the title
    title = Paragraph("Contributions Report", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.5 * inch))

    # Table data
    data = [["Member Name", "Event", "Amount", "Status"]]
    
    # Access user names via the User model associated with Profile
    for contribution in contributions:
        profile = contribution.profile
        user = profile.user
        profile_name = f"{user.first_name} {user.last_name}"  # Fetch full name from User model
        event_name = contribution.event.name
        amount = f"{contribution.amount} Ksh"
        status = contribution.category
        data.append([profile_name, event_name, amount, status])

    # Create the table
    table = Table(data, colWidths=[2 * inch, 2 * inch, 1.5 * inch, 1.5 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
    ]))

    elements.append(table)
    doc.build(elements)

    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename='contributions.pdf')

def export_contributions_excel(request):
    selected_event = request.GET.get('event')
    if selected_event and selected_event != 'None':
        contributions = Contribution.objects.filter(event__name=selected_event)
    else:
        contributions = Contribution.objects.all()

    if not contributions.exists():
        return HttpResponse("No contributions found for export.", status=404)

    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet()

    # Add headers
    header_format = workbook.add_format({'bold': True, 'text_wrap': True, 'valign': 'top', 'fg_color': '#D7E4BC', 'border': 1})
    worksheet.write(0, 0, 'Member Name', header_format)
    worksheet.write(0, 1, 'Event', header_format)
    worksheet.write(0, 2, 'Amount', header_format)
    worksheet.write(0, 3, 'Status', header_format)

    # Populate rows with contributions
    for row_num, contribution in enumerate(contributions, 1):
        profile = contribution.profile
        user = profile.user  # Access the related User model
        profile_name = f"{user.first_name} {user.last_name}"  # Fetch full name from User model
        event_name = contribution.event.name
        amount = f"{contribution.amount} Ksh"
        status = contribution.category

        worksheet.write(row_num, 0, profile_name)
        worksheet.write(row_num, 1, event_name)
        worksheet.write(row_num, 2, amount)
        worksheet.write(row_num, 3, status)

    workbook.close()

    output.seek(0)
    response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=contributions.xlsx'
    return response
def some_view(request):
    return redirect(reverse('login'))

def member_contributions_json(request):
    # Get all profiles
    profiles = Profile.objects.all()

    if profiles.exists():
        selected_member = choice(profiles)
        contributions = Contribution.objects.filter(profile=selected_member)

        total_contributions = contributions.aggregate(Sum('amount'))['amount__sum'] or 0
        event_count = contributions.values('event').distinct().count()

        # Debugging output
        print(f"Selected member: {selected_member.user.first_name} {selected_member.user.last_name}")
        print(f"Total contributions: {total_contributions}, Event count: {event_count}")

        data = {
            'name': f'{selected_member.user.first_name} {selected_member.user.last_name}',
            'email': selected_member.user.email,
            'total_contributions': total_contributions,
            'event_count': event_count,
            'total_amount': total_contributions,
            'profile_pic': selected_member.image.url if selected_member.image else '/static/images/default_profile.jpg',
        }
    else:
        data = {
            'name': 'No Members Available',
            'email': 'N/A',
            'total_contributions': 0,
            'event_count': 0,
            'total_amount': 0,
            'profile_pic': '/static/images/default_profile.jpg',
        }

    return JsonResponse(data)