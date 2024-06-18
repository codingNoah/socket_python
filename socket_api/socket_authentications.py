from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .serializer import UserSerializer
import jwt


User = get_user_model()


@database_sync_to_async
def get_user(user_id):

    try:
        serializer = UserSerializer(User.objects.get(id=user_id))
        return serializer.data
    except:
        return None


class QueryAuthMiddleware:

    def __init__(self, app):
        # Store the ASGI application we were passed
        self.app = app

    async def __call__(self, scope, receive, send):

        try:
            decoded_str = scope["query_string"].decode('utf-8')

            token = decoded_str.split('=')[1]

            payload = jwt.decode(jwt=token, key="SECRET_KEY", algorithms=['HS256'])

            user = await get_user(payload["user_id"])

            if not user:
                raise ValueError()
            scope["user_id"] = user["id"]
            
            print(user)
            return await self.app(scope, receive, send)

        except Exception as e:
            print("Exception", e)
            # raise ValueError()
            


