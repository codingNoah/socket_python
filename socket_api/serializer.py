from rest_framework import serializers 
from django.contrib.auth import get_user_model
from .models import Room, Message, GroupMembers, MessageReadBy
from django.shortcuts import get_object_or_404

User = get_user_model()


class IntegerListField(serializers.ListField):

    child = serializers.IntegerField()

class MessageIdListSerializer(serializers.Serializer):
    message_ids = IntegerListField()


class UserSerializer(serializers.ModelSerializer):

    class Meta:

        model = User 
        exclude = ["password"]


class RoomSerializer(serializers.ModelSerializer):

    created_by = UserSerializer(required=False)
    members = UserSerializer(many=True, required=False)
    last_message = serializers.SerializerMethodField()
    unread_messages = serializers.SerializerMethodField()

    class Meta:

        model = Room
        fields = "__all__"
        read_only_fields = ['created_by', 'members']

    def get_last_message(self, obj):

        message = Message.objects.filter(room_id=obj.id).order_by('-created_at').first()

        if message:

            return MessageSerializer(message, context={"request": self.context.get("request", None)}).data

        return None

    def get_unread_messages(self, obj):

        if not self.context.get("request", None):
            return 0

        return Message.objects.filter(room_id=obj.id).exclude(created_by=self.context.get("request", None).user.id).count() - MessageReadBy.objects.filter(message__room_id=obj.id, reader_id=self.context.get("request", None).user.id).exclude(message__created_by=self.context.get("request", None).user.id).count()

class RoomForwardedMessageSerializer(serializers.ModelSerializer):

    created_by = UserSerializer(required=False)
    
    class Meta:

        model = Room
        fields = ['created_by', 'created_at', 'group_type', 'id', 'name']


    

class GroupMemberSerializer(serializers.ModelSerializer):

    class Meta:

        model = GroupMembers
        fields = "__all__"

    def validate(self, attrs):

        room = Room.objects.filter(id=attrs["room"].id).first()
        if room:
            if room.group_type == "Private":
                member_count = GroupMembers.objects.filter(room_id=room.id).count()
                if member_count >= 2:
                    raise serializers.ValidationError("Private room is full")

        if self.context.get("create_from", None) != "Room":

            current_user_member = GroupMembers.objects.filter(member=self.context.get("request", None).user.id, room=attrs["room"]).first()

            if not current_user_member:
                raise serializers.ValidationError("User can't add members to this room")
                
            member = GroupMembers.objects.filter(member_id=attrs["member"], room_id=attrs["room"]).first()
            
            if member:
                raise serializers.ValidationError(f"Member already exists")

        if self.context.get("create_from", None) == "Room" and room.group_type == "Private":
            otherMember = self.context.get("request", None).data["otherMember"]
            member = Room.objects.filter(members__in=[self.context.get("request", None).user.id, otherMember], group_type="Private").first()

            if member:
                raise serializers.ValidationError("Member already exists")

        return super().validate(attrs)


class DisplayGroupMemberSerializer(serializers.ModelSerializer):

    member = UserSerializer()
    room = RoomSerializer()

    class Meta:

        model = GroupMembers
        fields = "__all__"


class MessageReadBySerializer(serializers.ModelSerializer):

    reader = UserSerializer(required=False)

    class Meta:

        model = MessageReadBy
        fields = "__all__"
        read_only_fields = ['reader']

    def validate(self, attrs):

        message = get_object_or_404(Message, id=attrs["message"].id)
        
        if message.created_by == self.context.get("request", None).user:
            raise serializers.ValidationError(f"Message can't be seen by its creator {message.created_by} {message.id} {message.text}")

        try:
            GroupMembers.objects.get(room_id=message.room.id, member_id=self.context.get("request", None).user.id)

        except:
            raise serializers.ValidationError("User does not belong in this room")

        item = MessageReadBy.objects.filter(message_id=message.id, reader_id=self.context.get("request", None).user.id).first()

        if item:
            raise serializers.ValidationError(f"User has already seen this message {message.id} {message.text}")

        return super().validate(attrs)


class MessageSerializer(serializers.ModelSerializer):

    created_by = UserSerializer(required=False)
    read_by = UserSerializer(many=True, required=False)
    read_by_current_user = serializers.SerializerMethodField()

    class Meta:

        model = Message
        fields = "__all__"
        read_only_fields = ['created_by']
    
    def validate(self, attrs):  
        
        if self.context.get("request", None).method == "PATCH":
            
            message = Message.objects.filter(id=self.context.get("pk", None)).first()
            
            if message.created_by_id != self.context.get("request", None).user.id:
                raise serializers.ValidationError("You can't update this message")
        
        return super().validate(attrs)

    def get_read_by_current_user(self, obj):

        if not self.context.get("request"):
            return False

        item = MessageReadBy.objects.filter(reader_id=self.context.get("request").user.id, message_id=obj.id).first()

        if item: 
            return MessageReadBySerializer(item).data

        return None

    def get_read_by(self, obj):

        serializer = MessageReadBySerializer(MessageReadBy.objects.filter(message_id=obj.id), many=True)

        return serializer.data

class MessageForwardSerializer(serializers.ModelSerializer):

    created_by = UserSerializer(required=False)
    read_by = UserSerializer(many=True, required=False)
    read_by_current_user = serializers.SerializerMethodField()
    room = RoomForwardedMessageSerializer()

    class Meta:

        model = Message
        fields = "__all__"
        read_only_fields = ['created_by']
    
    def validate(self, attrs):
        
        if self.context.get("request", None).method == "PATCH":
            
            message = Message.objects.filter(id=self.context.get("pk", None)).first()
            
            if message.created_by_id != self.context.get("request", None).user.id:
                raise serializers.ValidationError("You can't update this message")

        return super().validate(attrs)

    def get_read_by_current_user(self, obj):


        if not self.context.get("request"):
            return False

        item = MessageReadBy.objects.filter(reader_id=self.context.get("request").user.id, message_id=obj.id).first()

        if item: 
            return MessageReadBySerializer(item).data

        return None

    def get_read_by(self, obj):

        serializer = MessageReadBySerializer(MessageReadBy.objects.filter(message_id=obj.id), many=True)

        return serializer.data



class MessageReplySerializer(serializers.ModelSerializer):

    created_by = UserSerializer(required=False)
    read_by = serializers.SerializerMethodField()
    reply = MessageSerializer()
    read_by_current_user = serializers.SerializerMethodField()
    forwarded_from = MessageForwardSerializer()

    class Meta:

        model = Message
        fields = "__all__"
        read_only_fields = ['created_by', 'reply', "forwarded_from"]

    def get_read_by_current_user(self, obj):


        if not self.context.get("request"):
            return False

        item = MessageReadBy.objects.filter(reader_id=self.context.get("request").user.id, message_id=obj.id).first()

        if item: 
            return MessageReadBySerializer(item).data

        return None

    def get_read_by(self, obj):

        serializer = MessageReadBySerializer(MessageReadBy.objects.filter(message_id=obj.id), many=True)
        return serializer.data

