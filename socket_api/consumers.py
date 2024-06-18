
import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.contrib.auth import get_user_model
from .serializer import UserSerializer, GroupMemberSerializer, DisplayGroupMemberSerializer
from .socket_actions import SocketActions 
from .models import GroupMembers
import datetime


User = get_user_model()


class ChatConsumer(WebsocketConsumer):

    def connect(self):

        self.room_name = self.scope["user_id"]

        self.room_group_name = f"chat_{self.room_name}"

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )

        self.accept()

        self.announce_online_status_to_users(SocketActions.ONLINE, self.room_name)

        self.update_user_online_count(self.room_name, SocketActions.ONLINE)

    def disconnect(self, close_code):
        # Leave room group
        
        print("Leaving a room")
        self.update_user_last_seen(self.room_name)
        self.update_user_online_count(self.room_name, SocketActions.OFFLINE)

        self.announce_online_status_to_users(SocketActions.OFFLINE, self.room_name )

        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        # message = text_data_json["message"]
        action = text_data_json.get("action", None)
        data = text_data_json.get("data", None)

        if action == SocketActions.TYPING:

            room_id = data.get("room_id", None)

            serializer = DisplayGroupMemberSerializer(GroupMembers.objects.filter(room_id=room_id), many=True)
            print(serializer.data[0])
            for item in serializer.data:
                async_to_sync(self.channel_layer.group_send)(
                    f"chat_{item['member']['id']}", {"type": "chat_message", "message": {'action': SocketActions.TYPING, 'data': {'user_id': self.room_name, "room_id": room_id}}}
                )
            return

    # Receive message from room group
    def chat_message(self, event):
        message = event["message"]

        # Send message to WebSocket
        self.send(text_data=json.dumps({"message": message}))
    
    def announce_online_status_to_users(self, status, user_id):

        serializer =  UserSerializer(User.objects.all(), many=True)

        for user in serializer.data:

            async_to_sync(self.channel_layer.group_send)(
                f"chat_{user['id']}", {"type": "chat_message", "message": {'action': status, 'data': {'user_id': user_id}}}
            )
    
    def update_user_online_count(self, user_id, online_status):

        try:
            user = User.objects.get(id=user_id)
            print(user.online_count)
            if online_status == SocketActions.ONLINE:

                user.online_count = user.online_count + 1

            if online_status == SocketActions.OFFLINE and user.online_count != 0:
                user.online_count = user.online_count - 1

            user.save()
            print(user.online_count)
        except Exception as e:
            print("exception", e)
        
    def update_user_last_seen(self, user_id):
        
        user = User.objects.filter(id=user_id).first()
        
        if user:
            
            user.last_seen = datetime.datetime.now()
            user.save()
    