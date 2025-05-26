import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
import catalog.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web_project.settings')
django.setup() 

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            catalog.routing.websocket_urlpatterns
        )
    ),
})