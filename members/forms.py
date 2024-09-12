from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, Contribution, Event

# User Sign-Up Form
class UserSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone_number = forms.CharField(max_length=15, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()
            # Update the profile after it's created by the signal
            user.profile.phone_number = self.cleaned_data['phone_number']
            user.profile.save()
        return user


# User Update Form
class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']


# Profile Update Form (with lineage fields)
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image', 'bio', 'location', 'birthdate', 'phone_number', 'father', 'mother', 'has_children', 'number_of_children']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'birthdate': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'father': forms.Select(attrs={'class': 'form-control'}),  # Dropdown for selecting father
            'mother': forms.Select(attrs={'class': 'form-control'}),  # Dropdown for selecting mother
            'has_children': forms.CheckboxInput(attrs={'class': 'form-check-input'}),  # Checkbox for has_children
            'number_of_children': forms.NumberInput(attrs={'class': 'form-control', 'min': 0})  # Input for number_of_children
        }

    def clean_number_of_children(self):
        """Validate number_of_children based on the value of has_children"""
        has_children = self.cleaned_data.get('has_children')
        number_of_children = self.cleaned_data.get('number_of_children')

        if has_children and (number_of_children is None or number_of_children < 1):
            raise forms.ValidationError("Please specify the number of children.")
        elif not has_children:
            return 0  # Return 0 if user has no children
        return number_of_children


# Event Form
class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'date', 'required_amount_male', 'required_amount_female', 'is_active']

# Contribution Form
class ContributionForm(forms.ModelForm):
    class Meta:
        model = Contribution
        fields = ['profile', 'event', 'amount']  # 'category' removed as it's a computed property
