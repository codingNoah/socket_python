from rest_framework import permissions
from .models import GroupMembers
from .serializer import GroupMemberSerializer


class MessagePermissions(permissions.BasePermission):

    def has_permission(self, request, view):

        if request.method == "POST":
            
            queryset = GroupMemberSerializer(GroupMembers.objects.filter(room_id=request.data.get("room", None), member_id=request.user.id), many=True)

            if not len(queryset.data):
                return False
            
        return True