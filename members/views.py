from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, FileResponse, JsonResponse
from .forms import UserUpdateForm, ProfileUpdateForm, UserSignUpForm, EventForm, ContributionForm
from .models import Profile, Event, Contribution
from django.db.models import Sum, Count, Q
from django.contrib.auth.views import PasswordResetView, LoginView
from django.urls import reverse_lazy
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
import io
import xlsxwriter
from datetime import datetime
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from random import choice
from django.contrib.auth.models import User

# Home View
def home(request):
    # Fetch contributions and profiles
    contributions = Contribution.objects.annotate(
        event_count=Count('event', distinct=True),
        total_contributions=Sum('amount')
    ).order_by('-event__date')

    # Initialize counters for contributors
    active_contributors = 0
    dormant_contributors = 0
    partial_contributors = 0
    total_members = Profile.objects.count()

    contributions_data = []
    for contribution in contributions:
        # Determine the required amount based on the user's gender and the event's amounts
        if contribution.profile.gender == 'F':
            required_amount = contribution.event.required_amount_female  # Use female-specific amount
        elif contribution.profile.gender == 'M':
            required_amount = contribution.event.required_amount_male  # Use male-specific amount
        else:
            required_amount = contribution.event.required_amount_female  # Default to female amount for unknown gender

        # Determine if the contribution is full based on the required amount
        is_full = contribution.amount >= required_amount

        # Classify the contributor as active, dormant, or partial
        if is_full:
            active_contributors += 1
        elif contribution.amount == 0:
            dormant_contributors += 1
        else:
            partial_contributors += 1

        # Add the contribution details to the contributions_data list
        contributions_data.append({
            'profile': contribution.profile,
            'event': contribution.event,
            'amount': contribution.amount,
            'is_full': is_full,
            'event_count': contribution.event_count,
            'total_contributions': contribution.total_contributions
        })

    # Paginate the contributions (10 per page)
    paginator = Paginator(contributions_data, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Add the new fields to the context
    context = {
        'page_obj': page_obj,
        'total_members': total_members,
        'active_contributors': active_contributors,
        'dormant_contributors': dormant_contributors,
        'partial_contributors': partial_contributors,
    }

    return render(request, 'members/home.html', context)


# Custom Password Reset View
class CustomPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset_form.html'
    success_url = reverse_lazy('password_reset_done')
    email_template_name = 'registration/password_reset_email.html'

# Custom Login View
class CustomLoginView(LoginView):
    template_name = 'login.html'

# Recursive family tree logic
def get_children(profile, visited=None, depth=0, max_depth=10):
    if visited is None:
        visited = set()

    if profile in visited or depth > max_depth:
        return {}

    visited.add(profile)

    children_as_father = Profile.objects.filter(father=profile)
    children_as_mother = Profile.objects.filter(mother=profile)

    family_tree = {}
    all_children = list(children_as_father) + list(children_as_mother)

    for child in all_children:
        family_tree[child] = get_children(child, visited, depth + 1, max_depth)
    
    return family_tree

# Identify couples with children
def get_couples_with_children():
    couples = set()
    children_with_both_parents = Profile.objects.filter(father__isnull=False, mother__isnull=False)

    for child in children_with_both_parents:
        father, mother = child.father, child.mother
        if (father, mother) not in couples and (mother, father) not in couples:
            couples.add((father, mother))
    
    return couples

# Lineage view
def lineage_view(request):
    processed_profiles = set()
    couples = get_couples_with_children()

    families = {}
    for father, mother in couples:
        if father not in processed_profiles and mother not in processed_profiles:
            families[(father, mother)] = get_children(father)
            processed_profiles.add(father)
            processed_profiles.add(mother)

    unknown_parents_no_descendants = Profile.objects.filter(father=None, mother=None)
    no_descendants = [
        profile for profile in unknown_parents_no_descendants 
        if not Profile.objects.filter(father=profile).exists() and not Profile.objects.filter(mother=profile).exists()
    ]

    unknown_parents_with_descendants = [
        profile for profile in unknown_parents_no_descendants
        if Profile.objects.filter(father=profile).exists() or Profile.objects.filter(mother=profile).exists()
    ]
    for profile in unknown_parents_with_descendants:
        if profile not in processed_profiles:
            families[profile] = get_children(profile)
            processed_profiles.add(profile)

    families_list = list(families.items())
    paginator = Paginator(families_list, 1)
    page = request.GET.get('page', 1)

    try:
        paginated_families = paginator.page(page)
    except PageNotAnInteger:
        paginated_families = paginator.page(1)
    except EmptyPage:
        paginated_families = paginator.page(paginator.num_pages)

    return render(request, 'members/lineage.html', {'paginated_families': paginated_families})

# Admin: Manage Contributions
@user_passes_test(lambda u: u.is_staff)
def manage_contributions(request):
    if request.method == 'POST':
        form = ContributionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('contributions_page')
    else:
        form = ContributionForm()

    contributions = Contribution.objects.all()
    return render(request, 'members/manage_contributions.html', {'form': form, 'contributions': contributions})

# Admin: Manage Events
@user_passes_test(lambda u: u.is_staff)
def manage_events(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('events_page')
    else:
        form = EventForm()

    events = Event.objects.all()
    return render(request, 'members/manage_events.html', {'form': form, 'events': events})

# User Profile
@login_required
def profile(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    contributions = Contribution.objects.filter(profile=user.profile)

    total_contributed = contributions.aggregate(Sum('amount'))['amount__sum'] or 0

    current_hour = datetime.now().hour
    greeting_time = 'Good morning' if current_hour < 12 else 'Good afternoon' if 12 <= current_hour < 18 else 'Good evening'

    today = datetime.today().date()
    greeting_message = f"Happy Birthday, {user.first_name}!" if user.profile.birthdate and user.profile.birthdate == today else f"{greeting_time}, {user.first_name}!"

    total_users = Profile.objects.count()

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

    return render(request, 'profile.html', {
        'user_contributions': contributions,
        'total_contributed': total_contributed,
        'greeting_message': greeting_message,
        'event_contribution_stats': event_contribution_stats,
        'profile_user': user,
    })

# Update Profile
@login_required
def update_profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect('profile', user_id=request.user.id)
    else:
        form = ProfileUpdateForm(instance=request.user.profile)

    return render(request, 'members/update_profile.html', {'form': form})

# Event Page with Pagination
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

    paginator = Paginator(event_data, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'events_page.html', {
        'page_obj': page_obj,
        'events': event_data,
        'total_events': len(events),
        'active_events': len([event for event in events if event.is_active]),
        'total_contributions': sum([e['total_contributed'] for e in event_data]),
        'total_contributors': sum([e['contributor_count'] for e in event_data]),
    })

# Contributions Page with Pagination and Filters
@login_required
def contributions_page(request):
    selected_event = request.GET.get('event')
    selected_status = request.GET.get('status')  # Capture the selected status
    events = Event.objects.all()

    # Base query for contributions
    contributions = Contribution.objects.all()

    # Filter by event if selected
    if selected_event:
        contributions = contributions.filter(event__name=selected_event)

    # Filter by status if selected
    if selected_status:
        if selected_status == 'Fully Contributed':
            # Include members who contributed the required amount or more
            contributions = contributions.filter(
                Q(profile__gender='F', amount__gte=300) | 
                Q(profile__gender='M', amount__gte=500)
            )
        elif selected_status == 'Partially Contributed':
            # Include members who contributed between 1 and less than the required amount
            contributions = contributions.filter(
                Q(profile__gender='F', amount__gt=0, amount__lt=300) |
                Q(profile__gender='M', amount__gt=0, amount__lt=500)
            )
        elif selected_status == 'No Contribution':
            contributions = contributions.filter(amount=0)

    # Order the contributions to ensure consistent pagination
    contributions = contributions.order_by('event__date', 'profile__user__last_name')

    # Paginate contributions (e.g., 10 per page)
    paginator = Paginator(contributions, 10)  # Adjust the number as needed
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'contributions': page_obj,
        'events': events,
        'selected_event': selected_event,
        'selected_status': selected_status,  # Pass the selected status to the template
    }
    return render(request, 'contributions_page.html', context)


# Member Page with Category Filters and Pagination
@login_required
def members_page(request):
    profiles = Profile.objects.all()
    categorized_members = []

    for profile in profiles:
        category = "Deceased" if profile.is_deceased else "Exempt" if profile.is_exempt else "Dormant"
        contributions = Contribution.objects.filter(profile=profile).order_by('-event__date')[:2]

        is_super_member, is_active_member, is_dormant_member = False, False, False
        required_amount = 300 if profile.gender == 'F' else 500

        for contribution in contributions:
            if contribution.amount >= 3 * required_amount:
                is_super_member = True
            elif contribution.amount == required_amount:
                is_active_member = True
            elif contribution.amount < required_amount:
                is_dormant_member = True

        category = "Super Member" if is_super_member else "Active Member" if is_active_member else "Dormant"

        categorized_members.append({'profile': profile, 'category': category})

    selected_category = request.GET.get('category')
    if selected_category:
        if selected_category == "Deceased":
            categorized_members = [member for member in categorized_members if member['profile'].is_deceased]
        elif selected_category == "Exempt":
            categorized_members = [member for member in categorized_members if member['profile'].is_exempt]
        else:
            categorized_members = [member for member in categorized_members if member['category'] == selected_category]

    paginator = Paginator(categorized_members, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'members/members_page.html', {
        'profiles': page_obj,
        'selected_category': selected_category,
    })
def member_contributions_json(request):
    # Get all profiles
    profiles = Profile.objects.all()

    if profiles.exists():
        # Select a random member for demo purposes, you can modify this logic
        selected_member = choice(profiles)
        contributions = Contribution.objects.filter(profile=selected_member)

        # Check if contributions exist and get the latest event
        latest_contribution = contributions.order_by('-event__date').first()
        latest_event = latest_contribution.event.name if latest_contribution else "No Event Available"

        # Calculate total contributions and event count
        total_contributions = contributions.aggregate(Sum('amount'))['amount__sum'] or 0
        event_count = contributions.values('event').distinct().count()

        # Prepare data to be sent in JSON response
        data = {
            'name': f'{selected_member.user.first_name} {selected_member.user.last_name}',
            'event_name': latest_event,  # Set latest event here
            'total_contributions': total_contributions,
            'event_count': event_count,
            'total_amount': total_contributions,
            'profile_pic': selected_member.image.url if selected_member.image else '/static/images/default_profile.jpg',
        }
    else:
        # If no profiles are available, return default values
        data = {
            'name': 'No Members Available',
            'event_name': 'No Event Available',
            'total_contributions': 0,
            'event_count': 0,
            'total_amount': 0,
            'profile_pic': '/static/images/default_profile.jpg',
        }

    return JsonResponse(data)

    return JsonResponse(data)
def signup(request):
    if request.method == 'POST':
        form = UserSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Automatically log in the user after signup
            login(request, user)
            return redirect('home')  # Redirect to home or any other page after successful signup
        else:
            print(form.errors)  # Print form errors for debugging
    else:
        form = UserSignUpForm()

    return render(request, 'registration/signup.html', {'form': form})

def export_contributions_pdf(request):
    # Get filter parameters (optional)
    selected_event = request.GET.get('event')
    selected_status = request.GET.get('status')

    # Get all contributions
    contributions = Contribution.objects.all()

    # If 'None' is passed as the event or status, it should not filter
    if selected_event and selected_event != 'None':
        contributions = contributions.filter(event__name=selected_event)

    if selected_status and selected_status != 'None':
        if selected_status == 'Fully Contributed':
            contributions = contributions.filter(
                Q(profile__gender='F', amount__gte=300) | 
                Q(profile__gender='M', amount__gte=500)
            )
        elif selected_status == 'Partially Contributed':
            contributions = contributions.filter(
                Q(profile__gender='F', amount__gt=0, amount__lt=300) |
                Q(profile__gender='M', amount__gt=0, amount__lt=500)
            )
        elif selected_status == 'No Contribution':
            contributions = contributions.filter(amount=0)

    if not contributions.exists():
        # Handle case where no contributions match the filter
        return HttpResponse("No data available to export.", status=404)

    # Create a PDF document
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    # Add title to the PDF
    styles = getSampleStyleSheet()
    title = Paragraph("Contributions Report", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))

    # Table headers
    data = [["Member Name", "Event", "Amount", "Status"]]

    # Add table data from contributions
    for contribution in contributions:
        profile_name = f"{contribution.profile.user.first_name} {contribution.profile.user.last_name}"
        event_name = contribution.event.name
        amount = f"{contribution.amount} Ksh"
        status = "Fully Contributed" if contribution.amount >= (500 if contribution.profile.gender == 'M' else 300) else "Partially Contributed"
        data.append([profile_name, event_name, amount, status])

    # Create table with data
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)

    # Build the PDF document
    doc.build(elements)

    # Serve the PDF as a response
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename='contributions_report.pdf')


def export_contributions_excel(request):
    # Get filter parameters (optional)
    selected_event = request.GET.get('event')
    selected_status = request.GET.get('status')

    # Get all contributions
    contributions = Contribution.objects.all()

    # Apply filtering if necessary
    if selected_event:
        contributions = contributions.filter(event__name=selected_event)
    if selected_status:
        if selected_status == 'Fully Contributed':
            contributions = contributions.filter(
                Q(profile__gender='F', amount__gte=300) | 
                Q(profile__gender='M', amount__gte=500)
            )
        elif selected_status == 'Partially Contributed':
            contributions = contributions.filter(
                Q(profile__gender='F', amount__gt=0, amount__lt=300) |
                Q(profile__gender='M', amount__gt=0, amount__lt=500)
            )
        elif selected_status == 'No Contribution':
            contributions = contributions.filter(amount=0)

    if not contributions.exists():
        # Handle case where no contributions match the filter
        return HttpResponse("No data available to export.", status=404)

    # Create an in-memory output file for the new Excel file.
    output = io.BytesIO()

    # Create a workbook and add a worksheet using xlsxwriter
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet()

    # Add headers to the worksheet
    headers = ['Member Name', 'Event', 'Amount', 'Status']
    header_format = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC'})
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header, header_format)

    # Write data to the worksheet
    for row_num, contribution in enumerate(contributions, start=1):
        profile_name = f"{contribution.profile.user.first_name} {contribution.profile.user.last_name}"
        event_name = contribution.event.name
        amount = contribution.amount
        status = "Fully Contributed" if contribution.amount >= (500 if contribution.profile.gender == 'M' else 300) else "Partially Contributed"
        
        worksheet.write(row_num, 0, profile_name)
        worksheet.write(row_num, 1, event_name)
        worksheet.write(row_num, 2, amount)
        worksheet.write(row_num, 3, status)

    # Close the workbook after writing
    workbook.close()

    # Rewind the buffer
    output.seek(0)

    # Serve the Excel file as a response
    response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=contributions_report.xlsx'

    return response


def home_details_json(request):
    user = request.user
    # Dummy data for recent activity, total events, ongoing projects, and contributions
    recent_activity = "None"
    total_events = Event.objects.count()  # Example to count all events
    ongoing_projects = Project.objects.filter(status="ongoing").count()  # Replace 'Project' with the appropriate model
    latest_contributions = Contribution.objects.filter(profile=user.profile).aggregate(Sum('amount'))['amount__sum'] or 0

    return JsonResponse({
        'username': user.get_full_name() or user.username,
        'recent_activity': recent_activity,
        'total_events': total_events,
        'ongoing_projects': ongoing_projects,
        'latest_contributions': latest_contributions,
    })