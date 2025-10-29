from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DriverViewSet, RideOrderViewSet

router = DefaultRouter()
router.register(r"drivers", DriverViewSet)
router.register(r"orders", RideOrderViewSet)

urlpatterns = [
    path("", include(router.urls)),
]