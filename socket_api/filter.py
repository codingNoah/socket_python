from rest_framework.filters import BaseFilterBackend
from rest_framework.compat import coreapi, coreschema

class UserFilterBackend(BaseFilterBackend):


    def filter_queryset(self, request, queryset, view):

        email = request.query_params.get("email")
        user_id = request.query_params.get("user_id")

        if email:
            queryset = queryset.filter(email__icontains=email)
        
        if user_id:
            queryset = queryset.filter(id=user_id)

        return queryset


class MessageFilterBackend(BaseFilterBackend):


    def filter_queryset(self, request, queryset, view):

        room_id = request.query_params.get("room_id")

        if room_id:
            queryset = queryset.filter(room__id=room_id)

        return queryset


class MessageReadByFilterBackend(BaseFilterBackend):


    def filter_queryset(self, request, queryset, view):

        message_id = request.query_params.get("message_id")

        if message_id:
            queryset = queryset.filter(message__id=message_id)

        return queryset
