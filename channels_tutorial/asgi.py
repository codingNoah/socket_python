import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application
from socket_api.socket_authentications import QueryAuthMiddleware

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "channels_tutorial.settings")
# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

from socket_api.routing import websocket_urlpatterns

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            QueryAuthMiddleware(URLRouter(websocket_urlpatterns))
        ),
    }
)
