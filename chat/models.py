from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Room(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

class Message(models.Model):
    room = models.ForeignKey(Room, related_name='messages', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='messages', on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)  # Allow blank content if it's just an image
    image = models.ImageField(upload_to='chat_images/', blank=True, null=True)  # Optional image field
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        if self.content:
            return f'{self.user.username}: {self.content[:50]}'
        elif self.image:
            return f'{self.user.username} sent an image'
        else:
            return f'{self.user.username}: [Empty message]'

    class Meta:
        ordering = ['timestamp']