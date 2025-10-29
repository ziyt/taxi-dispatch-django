import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from django.urls import path
from dispatch_core.consumers import DispatchConsumer

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "taxi_dispatch.settings")

django_app = get_asgi_application()

websocket_urlpatterns = [
    path("ws/dispatch/", DispatchConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    "http": django_app,
    "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
})