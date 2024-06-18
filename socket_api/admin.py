from django.contrib import admin
from .models import Room, CustomUser, Message, GroupMembers, MessageReadBy
# Register your models here.

class UserAdmin(admin.ModelAdmin):

    fieldsets = [
        (None, {"fields": [ "first_name", "last_name", "email", "online_count", "username", "password", "is_staff", "is_active", "is_superuser", "show_last_seen"]}),
        
    ]


class RoomAdmin(admin.ModelAdmin):

    fieldsets = [
        (None, {"fields": [ "name", "created_by", "group_type"]}),
        
    ]


class MessageAdmin(admin.ModelAdmin):

    fieldsets = [
        (None, {"fields": [ "text", "created_by", "room"]}),
        
    ]


class GroupMemberAdmin(admin.ModelAdmin):

    fieldsets = [
        (None, {"fields": [ "member", "room"]}),
        
    ]

class MessageReadByAdmin(admin.ModelAdmin):

    fieldsets = [
        (None, {"fields": [ "reader", "message"]}),
        
    ]




admin.site.register(CustomUser, UserAdmin)
admin.site.register(Room, RoomAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(GroupMembers, GroupMemberAdmin)
admin.site.register(MessageReadBy, MessageReadByAdmin)
