from django.db import models
from datetime import date
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')
    bio = models.TextField(max_length=500, blank=True)  # New field for bio
    location = models.CharField(max_length=100, blank=True)  # New field for location
    birthdate = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    othernames = models.CharField(max_length=100)
    has_children = models.BooleanField(default=False)
    number_of_children = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f'{self.user.username} Profile'

    def age(self):
        if self.birthdate:
            today = date.today()
            return today.year - self.birthdate.year - ((today.month, today.day) < (self.birthdate.month, self.birthdate.day))
        return None

    age.short_description = 'Age'

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

class EventCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name

class Event(models.Model):
    name = models.CharField(max_length=200)
    date = models.DateField()
    required_amount = models.DecimalField(max_digits=10, decimal_places=2, default=200.00)
    is_active = models.BooleanField(default=True)  # New field to indicate if the event is active

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Automatically mark the event as inactive if the date has passed
        if self.date < date.today():
            self.is_active = False
        super(Event, self).save(*args, **kwargs)

class Contribution(models.Model):
    profile = models.ForeignKey(Profile, related_name='contributions', on_delete=models.CASCADE)
    event = models.ForeignKey(Event, related_name='contributions', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.profile.user.username} - {self.event.name}: {self.amount} Ksh"

    @property
    def category(self):
        if self.amount >= self.event.required_amount:
            return 'Fully Contributed'
        elif 0 < self.amount < self.event.required_amount:
            return 'Partially Contributed'
        else:
            return 'No Contribution'

class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ('Reminder', 'Reminder'),
        ('Announcement', 'Announcement'),
        ('Alert', 'Alert'),
    ]

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    message = models.TextField()
    type = models.CharField(max_length=50, choices=NOTIFICATION_TYPE_CHOICES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification to {self.profile.user.username} - {self.type}"
