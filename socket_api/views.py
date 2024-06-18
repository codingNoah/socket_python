from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.backends import TokenBackend
from rest_framework.decorators import api_view, permission_classes
from .serializer import RoomSerializer, UserSerializer, MessageSerializer,MessageIdListSerializer, GroupMemberSerializer, IntegerListField ,DisplayGroupMemberSerializer, MessageReadBySerializer, MessageReplySerializer
from .models import Room, Message, CustomUser, GroupMembers, MessageReadBy
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .socket_actions import SocketActions
from .filter import UserFilterBackend, MessageFilterBackend, MessageReadByFilterBackend
from rest_framework.decorators import action
from rest_framework import serializers
import datetime
from .tasks import send


User = get_user_model()


class GroupMembersViewSet(ModelViewSet):

    serializer_class = GroupMemberSerializer
    queryset = GroupMembers.objects.all()
    permission_classes=[IsAuthenticated]

    def list(self, request, *args, **kwargs):

        room_id = request.query_params.get("room_id", None)

        if room_id:

            get_object_or_404(Room, pk = room_id)
            
            serializer = DisplayGroupMemberSerializer(GroupMembers.objects.filter(room__id=room_id), many=True)

            return Response(data=serializer.data, status=200)
        
        return super().list(request, *args, **kwargs)
            

class RoomViewSet(ModelViewSet):

    serializer_class = RoomSerializer
    queryset = Room.objects.all()
    permission_classes=[IsAuthenticated]

    def get_queryset(self):

        return Room.objects.filter(members=self.request.user)

    def perform_create(self, serializer):

        serializer.save(created_by_id=self.request.user.id)

        memberSerializer = GroupMemberSerializer(data={"member": self.request.user.id, "room": serializer.data.get("id", None)}, context={"request": self.request, "create_from": "Room"})
        memberSerializer.is_valid(raise_exception=True)

        memberSerializer.save()


class UserViewSet(ModelViewSet):

    serializer_class = UserSerializer
    queryset = User.objects.all()
    filter_backends = [UserFilterBackend]


class MessageReadByViewSet(ModelViewSet):

    serializer_class = MessageReadBySerializer
    queryset = MessageReadBy.objects.all()
    permission_classes=[IsAuthenticated]
    filter_backends=[MessageReadByFilterBackend]

    def perform_create(self, serializer):

        return serializer.save(reader=self.request.user)

    @action(detail=False, methods=['post'])
    def update_read(self, request):

        serializer = MessageIdListSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        message_ids = serializer.data.get("message_ids", None)
        messages = []
        for id in message_ids:
            message = Message.objects.filter(id=id).first()
            item = MessageReadBy.objects.filter(reader_id=request.user.id, message_id=id).first()
            if message and not item:
                MessageReadBy.objects.create(reader_id=request.user.id, message_id=message.id) 
                messages.append(message)
                
                
        serializer = MessageReplySerializer(messages, many=True)
        
        
        
        if len(serializer.data) > 0:
            memberSerializer = DisplayGroupMemberSerializer(GroupMembers.objects.filter(room_id=serializer.data[0]["room"]), many=True)

            channel_layer = get_channel_layer()

            for item in memberSerializer.data:
                
                async_to_sync(channel_layer.group_send)(
                    f"chat_{item['member']['id']}", {"type": "chat.message", "message": {'action': SocketActions.MESSAGE_READ, 'data': {'user_id': self.request.user.id, "room_id": item['room']['id'], "messages": serializer.data}}}
                )
            
        return Response(serializer.data,status=200)

class MessageViewSet(ModelViewSet):

    serializer_class = MessageSerializer
    queryset = Message.objects.all()
    permission_classes=[IsAuthenticated]
    filter_backends=[MessageFilterBackend]

    def get_serializer_class(self):
        
        if self.action == "list" or self.action == "retrieve":
            return MessageReplySerializer
        
        return super().get_serializer_class()

    def get_queryset(self):

        return Message.objects.filter(room__members=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        
        print(kwargs.get("pk"))
        instance = self.get_object()
        print("instance", instance)
        if instance.created_by_id != request.user.id:
            raise serializers.ValidationError("Can't delete this message")
        
        self.perform_destroy(instance)
        
        memberSerializer = DisplayGroupMemberSerializer(GroupMembers.objects.filter(room=instance.room), many=True)
        
        channel_layer = get_channel_layer()

        for item in memberSerializer.data:
            async_to_sync(channel_layer.group_send)(
                f"chat_{item['member']['id']}", {"type": "chat.message", "message": {'action': SocketActions.MESSAGE_DELETED, 'data': {'user_id': self.request.user.id, "room_id": item['room']['id'], "message_id": kwargs.get("pk")}}}
            )
            
        return Response(status=204)

    
    def create(self, request, *args, **kwargs):

        serializer = MessageSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        
        serializer.save(created_by_id=self.request.user.id)
        
        memberSerializer = DisplayGroupMemberSerializer(GroupMembers.objects.filter(room=serializer.data['room']), many=True)
        
        room = Room.objects.filter(id=serializer.data['room']).first()
        date = datetime.datetime.now()
        room.last_updated = date
        room.save()

        
        channel_layer = get_channel_layer()

        for item in memberSerializer.data:
            async_to_sync(channel_layer.group_send)(
                f"chat_{item['member']['id']}", {"type": "chat.message", "message": {'action': SocketActions.MESSAGE_CREATED, 'data': {'user_id': self.request.user.id, "room_id": item['room']['id'], "message_id": int(serializer.data['id'])}}}
            )
            
        message = Message.objects.get(id=serializer.data.get("id", None))
        return Response(MessageReplySerializer(message).data, status=201)

    def update(self, request, *args, **kwargs):


        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        if request.data.get("text"):
            request.data["edited"] = True
            
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer = MessageSerializer(instance=instance, data=request.data, partial=partial, context={"request": request, "pk": kwargs.get("pk")})
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):

            instance._prefetched_objects_cache = {}

        memberSerializer = DisplayGroupMemberSerializer(GroupMembers.objects.filter(room=serializer.data['room']), many=True)
        
        channel_layer = get_channel_layer()

        for item in memberSerializer.data:
            async_to_sync(channel_layer.group_send)(
                f"chat_{item['member']['id']}", {"type": "chat.message", "message": {'action': SocketActions.MESSAGE_UPDATED, 'data': {'user_id': self.request.user.id, "room_id": item['room']['id'], "message_id": serializer.data['id']}}}
            )
            
        message = Message.objects.get(id=serializer.data.get("id", None))
        return Response(MessageReplySerializer(message).data, status=201)
        

        
    
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user(request):

        user = get_object_or_404(User, pk=request.user.id)

        serializer = UserSerializer(user)

        return Response(data=serializer.data, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search(request):
        
        search = request.query_params.get("search", None)

        
        if search:

            groups = Room.objects.filter(name__icontains=search, members__id=request.user.id).exclude(group_type="Private")
            privates = Room.objects.filter(name__icontains=search, members__id=request.user.id, group_type="Private")

            return Response(data={"privates": RoomSerializer(privates, many=True).data, "groups": RoomSerializer(groups, many=True).data}, status=200)
        
        else:
            groups = Room.objects.filter(group_type="Group")
            privates = Room.objects.filter(group_type="Private")
            
            return Response(data={"privates": RoomSerializer(privates, many=True).data, "groups": RoomSerializer(groups, many=True).data}, status=200)


@api_view(['POST'])
@permission_classes([AllowAny])

def create_room(request):
        print("sending1...")
        send.delay()
        
        return Response("send", status=200)


