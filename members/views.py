from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, FileResponse
from .forms import UserUpdateForm, ProfileUpdateForm, UserSignUpForm
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

def home(request):
    return render(request, 'members/home.html')

@login_required
def profile(request):
    user = request.user
    contributions = Contribution.objects.filter(profile=user.profile)
    
    # Calculate total contributions
    total_contributed = contributions.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Determine time of day for greeting
    current_hour = datetime.now().hour
    if current_hour < 12:
        greeting_time = 'morning'
    elif 12 <= current_hour < 18:
        greeting_time = 'afternoon'
    else:
        greeting_time = 'evening'
    
    context = {
        'user_contributions': contributions,
        'total_contributed': total_contributed,
        'greeting_time': greeting_time,
    }
    return render(request, 'profile.html', context)

@login_required
def profile(request):
    user = request.user
    contributions = Contribution.objects.filter(profile=user.profile)
    
    # Calculate total contributions
    total_contributed = contributions.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Determine time of day for greeting
    current_hour = datetime.now().hour
    if current_hour < 12:
        greeting_time = 'morning'
    elif 12 <= current_hour < 18:
        greeting_time = 'afternoon'
    else:
        greeting_time = 'evening'
    
    # Fetch the most recent events user has contributed to
    recent_contributions = contributions.order_by('-event__date')[:5]
    
    context = {
        'user_contributions': contributions,
        'total_contributed': total_contributed,
        'greeting_time': greeting_time,
        'recent_contributions': recent_contributions,
    }
    return render(request, 'members/profile.html', context)

@login_required
def update_profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect('profile', user_id=request.user.id)
    else:
        form = ProfileUpdateForm(instance=request.user.profile)
    
    return render(request, 'members/update_profile.html', {'form': form})

def events_page(request):
    events = Event.objects.filter(is_active=True)  # Only show active events
    total_members = Profile.objects.count()  # Get total number of members

    # Apply filters based on request.GET parameters
    date_filter = request.GET.get('date')
    min_amount = request.GET.get('min_amount')
    max_amount = request.GET.get('max_amount')

    if date_filter:
        events = events.filter(date=date_filter)
    if min_amount:
        events = events.filter(contributions__amount__gte=min_amount)
    if max_amount:
        events = events.filter(contributions__amount__lte=max_amount)

    event_data = []

    for event in events:
        total_contributed = Contribution.objects.filter(event=event).aggregate(Sum('amount'))['amount__sum'] or 0
        percentage_contributed = (total_contributed / event.required_amount) * 100 if event.required_amount > 0 else 0
        contributor_count = Contribution.objects.filter(event=event).aggregate(Count('profile', distinct=True))['profile__count'] or 0

        event_data.append({
            'name': event.name,
            'total_contributed': total_contributed,
            'percentage_contributed': percentage_contributed,
            'contributor_count': contributor_count,
            'total_members': total_members,  # Include total members in the data
        })

    context = {
        'event_data': event_data,
    }
    return render(request, 'events_page.html', context)

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

    title_style = getSampleStyleSheet()['Heading1']
    title_style.alignment = 1  # Center the title
    title = Paragraph("Contributions Report", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.5 * inch))

    data = [["Profile Name", "Event", "Amount", "Status"]]
    for contribution in contributions:
        profile_name = f"{contribution.profile.surname} {contribution.profile.othernames}"
        event_name = contribution.event.name
        amount = f"{contribution.amount} Ksh"
        status = contribution.category
        data.append([profile_name, event_name, amount, status])

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

    header_format = workbook.add_format({'bold': True, 'text_wrap': True, 'valign': 'top', 'fg_color': '#D7E4BC', 'border': 1})
    worksheet.write(0, 0, 'Profile Name', header_format)
    worksheet.write(0, 1, 'Event', header_format)
    worksheet.write(0, 2, 'Amount', header_format)
    worksheet.write(0, 3, 'Status', header_format)

    for row_num, contribution in enumerate(contributions, 1):
        worksheet.write(row_num, 0, f"{contribution.profile.surname} {contribution.profile.othernames}")
        worksheet.write(row_num, 1, contribution.event.name)
        worksheet.write(row_num, 2, f"{contribution.amount} Ksh")
        worksheet.write(row_num, 3, contribution.category)

    workbook.close()

    output.seek(0)
    response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=contributions.xlsx'
    return response
