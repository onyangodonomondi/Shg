from django.urls import path
from . import views

urlpatterns = [
    path('', views.rooms, name='chat_rooms'),  # List of all chat rooms
    path('create/', views.create_room, name='create_room'),  # URL for creating a new room
    path('<str:room_name>/', views.chat_room, name='chat_room'),  # URL for specific chat room
    path('ajax/<str:room_name>/', views.load_chat_room, name='load_chat_room'),  # AJAX call for chat room
    path('<str:room_name>/send/', views.send_message, name='send_message'),  # Sending messages in chat
]
