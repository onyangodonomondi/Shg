from django.shortcuts import render, get_object_or_404
from .models import Room, Message
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse

@login_required
def chat_room(request, room_name):
    room = get_object_or_404(Room, name=room_name)
    messages = room.messages.all()
    return render(request, 'chat/chat_room.html', {'room': room, 'messages': messages})

@login_required
def rooms(request):
    rooms = Room.objects.all()
    return render(request, 'chat/rooms.html', {'rooms': rooms})

@login_required
def chat_room(request, room_name):
    room = get_object_or_404(Room, name=room_name)
    if request.method == 'POST':
        message_content = request.POST['message']
        Message.objects.create(room=room, user=request.user, content=message_content)
        return HttpResponseRedirect(reverse('chat_room', args=[room_name]))
    
    messages = room.messages.all()
    return render(request, 'chat/chat_room.html', {'room': room, 'messages': messages})