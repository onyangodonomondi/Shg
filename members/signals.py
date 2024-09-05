from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile

@receiver(post_save, sender=User)
def create_or_update_profile(sender, instance, created, **kwargs):
    if created:
        # Only create the profile if it doesn't already exist
        Profile.objects.get_or_create(user=instance)
    else:
        # Update the profile if the user is updated
        try:
            instance.profile.save()
        except Profile.DoesNotExist:
            # If the profile doesn't exist (unlikely), create it
            Profile.objects.create(user=instance)