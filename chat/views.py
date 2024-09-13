from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Room, Message

# Chat room view
@login_required
def chat_room(request, room_name):
    room = get_object_or_404(Room, name=room_name)
    
    # Handle message submission
    if request.method == 'POST':
        message_content = request.POST.get('message', '')  # Get message content
        image = request.FILES.get('image')  # Get uploaded image if any

        if message_content or image:  # Ensure at least message or image is provided
            Message.objects.create(room=room, user=request.user, content=message_content, image=image)

        return HttpResponseRedirect(reverse('chat_room', args=[room_name]))  # Redirect to prevent duplicate form submissions
    
    # Get all messages for the room
    messages = room.messages.all()
    return render(request, 'chat/chat_room.html', {'room': room, 'messages': messages})

# View to list all rooms
@login_required
def rooms(request):
    rooms = Room.objects.all()
    return render(request, 'chat/rooms.html', {'rooms': rooms})

# View to handle sending messages (if needed separately, although chat_room can handle it)
@login_required
def send_message(request, room_name):
    room = get_object_or_404(Room, name=room_name)
    
    if request.method == 'POST':
        message_content = request.POST.get('message', '')
        image = request.FILES.get('image')  # Get the uploaded image if any

        if message_content or image:  # Ensure at least message or image is provided
            Message.objects.create(room=room, user=request.user, content=message_content, image=image)

        return redirect('chat_room', room_name=room_name)

@login_required
def load_chat_room(request, room_name):
    room = get_object_or_404(Room, name=room_name)
    messages = room.messages.all()
    html = render_to_string('chat/chat_room_content.html', {'room': room, 'messages': messages}, request)
    return JsonResponse({'html': html})

def create_room(request):
    if request.method == 'POST':
        room_name = request.POST.get('room_name')
        if room_name:
            Room.objects.create(name=room_name)
            return redirect('chat_rooms')  # Redirect back to the room list after creation

    return render(request, 'chat/create_room.html')