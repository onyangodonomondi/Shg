from django.db import models
from datetime import date
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import Image


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')
    bio = models.TextField(max_length=500, blank=True)  # Field for bio
    location = models.CharField(max_length=100, blank=True)  # Field for location
    birthdate = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    othernames = models.CharField(max_length=100)
    has_children = models.BooleanField(default=False)
    number_of_children = models.PositiveIntegerField(null=True, blank=True)

    
    # Lineage tracking fields
    father = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='father_children')
    mother = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='mother_children')

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'
    
    def age(self):
        if self.birthdate:
            today = date.today()
            return today.year - self.birthdate.year - ((today.month, today.day) < (self.birthdate.month, self.birthdate.day))
        return None

    age.short_description = 'Age'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.optimize_image()

    def optimize_image(self):
        """Resize and crop the image to a square while focusing on the head."""
        img = Image.open(self.image.path)

        # Set the desired output size (e.g., 300x300)
        output_size = (300, 300)

        # Resize while maintaining the aspect ratio
        img.thumbnail(output_size)

        # Crop to focus on the top portion (to keep the head centered)
        width, height = img.size
        if width > height:
            left = (width - height) // 2
            right = left + height
            top, bottom = 0, height
        else:
            top = (height - width) // 4  # Headroom bias
            bottom = top + width
            left, right = 0, width

        img = img.crop((left, top, right, bottom))
        
        # Save the optimized image in a proper format
        img.save(self.image.path, quality=85, optimize=True)


class EventCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name


class Event(models.Model):
    name = models.CharField(max_length=200)
    date = models.DateField()
    required_amount = models.DecimalField(max_digits=10, decimal_places=2, default=200.00)
    is_active = models.BooleanField(default=True)  # Field to indicate if the event is active

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
