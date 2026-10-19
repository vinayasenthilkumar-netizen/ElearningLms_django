# import os so we can set environment variables for django
import os

# import auth middleware stack so websocket connections can use logged in users
from channels.auth import AuthMiddlewareStack

# import routing helpers to route http and websocket protocols
from channels.routing import ProtocolTypeRouter, URLRouter

# import validator to make sure websocket origins match allowed hosts
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

# import websocket routes from the accounts app
from accounts.routing import websocket_urlpatterns as account_websocket_urlpatterns

# import websocket routes from the chat app
from chat.routing import websocket_urlpatterns as chat_websocket_urlpatterns

# import websocket routes from the courses app
from courses.routing import websocket_urlpatterns as course_websocket_urlpatterns


# set the default settings module for django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# create the django asgi application for handling http requests
django_asgi_app = get_asgi_application()

# import websocket routes again
from accounts.routing import websocket_urlpatterns as account_websocket_urlpatterns
from chat.routing import websocket_urlpatterns as chat_websocket_urlpatterns

# define the main asgi application router
application = ProtocolTypeRouter({
    # route normal http traffic to django
    "http": django_asgi_app,
    # route websocket traffic through validators and middleware
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                account_websocket_urlpatterns
                + chat_websocket_urlpatterns
                + course_websocket_urlpatterns
            )
        )
    ),
})