from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile

@receiver(post_save, sender=User)
def create_or_update_profile(sender, instance, created, **kwargs):
    if created:
        # Create a profile for a newly created user
        Profile.objects.create(user=instance)
    else:
        # Update the profile if needed; typically, this shouldn't be necessary for OneToOneField
        instance.profile.save()
