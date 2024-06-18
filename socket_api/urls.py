from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
from .views import RoomViewSet, UserViewSet, get_user, MessageViewSet, GroupMembersViewSet, MessageReadByViewSet, search, create_room
from django.urls import path, include
from rest_framework.routers import  SimpleRouter


router = SimpleRouter()

router.register('rooms', RoomViewSet )
router.register('users', UserViewSet )
router.register('messages', MessageViewSet )
router.register('members', GroupMembersViewSet)
router.register('message_readby', MessageReadByViewSet)


urlpatterns = [
    path('',include(router.urls)),
    
    path('search/', search, name='search'),
    path('send/', create_room, name='create_room'),
    path('get_user/', get_user, name='index'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),

]
