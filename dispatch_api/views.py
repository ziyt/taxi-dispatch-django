from math import radians, sin, cos, asin, sqrt
from django.db import transaction
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from dispatch_core.models import Driver, RideOrder, DriverStatus, OrderStatus
from .serializers import DriverSerializer, RideOrderSerializer

# Реалтайм (Channels)
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# Геокодер опционален
try:
    from dispatch_core.geocode import geocode
except Exception:
    geocode = None

def broadcast(payload: dict):
    """
    Безопасная отправка WS-события.
    Если Redis/Channel layer не поднят — просто логируем и не роняем API.
    """
    layer = get_channel_layer()
    if not layer:
        print("[WS] channel layer is None, skip broadcast:", payload.get("type"))
        return
    try:
        async_to_sync(layer.group_send)("dispatch", {"type": "dispatch.event", "payload": payload})
    except Exception as e:
        print("[WS] broadcast failed:", e, "| payload:", payload)

def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlmb = radians(lon2 - lon1)
    a = sin(dphi/2)**2 + cos(p1)*cos(p2)*sin(dlmb/2)**2
    return 2*R*asin(sqrt(a))

class DriverViewSet(viewsets.ModelViewSet):
    queryset = Driver.objects.all().order_by("callsign")
    serializer_class = DriverSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["callsign", "status"]

    @action(detail=True, methods=["post"])
    def position(self, request, pk=None):
        d = self.get_object()
        # простая и безопасная валидация
        lat = request.data.get("lat")
        lng = request.data.get("lng")
        status_in = request.data.get("status")
        if lat is not None:
            try: d.lat = float(lat)
            except: return Response({"detail":"lat must be float"}, status=status.HTTP_400_BAD_REQUEST)
        if lng is not None:
            try: d.lng = float(lng)
            except: return Response({"detail":"lng must be float"}, status=status.HTTP_400_BAD_REQUEST)
        if status_in in dict(DriverStatus.CHOICES):
            d.status = status_in
        d.save()
        data = DriverSerializer(d).data
        broadcast({"type": "driver_update", "driver": data})
        return Response(data)

class RideOrderViewSet(viewsets.ModelViewSet):
    queryset = RideOrder.objects.all().order_by("-created_at")
    serializer_class = RideOrderSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["customer_phone", "from_address", "to_address", "status"]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        # геокод по желанию
        if geocode:
            if not data.get("from_lat") or not data.get("from_lng"):
                latlng = geocode(data.get("from_address"))
                if latlng and latlng[0] and latlng[1]:
                    data["from_lat"], data["from_lng"] = latlng
            if not data.get("to_lat") or not data.get("to_lng"):
                latlng = geocode(data.get("to_address"))
                if latlng and latlng[0] and latlng[1]:
                    data["to_lat"], data["to_lng"] = latlng

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        out = serializer.data
        broadcast({"type": "order_created", "order": out})
        headers = self.get_success_headers(serializer.data)
        return Response(out, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=["get"])
    def nearest_driver(self, request, pk=None):
        order = self.get_object()
        if order.from_lat is None or order.from_lng is None:
            return Response({"detail": "У заказа нет координат пункта подачи."},
                            status=status.HTTP_400_BAD_REQUEST)
        candidates = Driver.objects.filter(status=DriverStatus.AVAILABLE, lat__isnull=False, lng__isnull=False)
        if not candidates.exists():
            return Response({"detail": "Нет доступных водителей с координатами."}, status=status.HTTP_404_NOT_FOUND)
        best = None
        best_dist = None
        for d in candidates:
            dist = haversine_m(order.from_lat, order.from_lng, d.lat, d.lng)
            if best is None or dist < best_dist:
                best, best_dist = d, dist
        payload = DriverSerializer(best).data
        payload["distance_m"] = round(best_dist or 0.0, 1)
        return Response(payload)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def assign(self, request, pk=None):
        """
        Назначение водителя.
        Причины 500 обычно:
        - кривой driver_id
        - Redis/channels упали на broadcast
        - сериализатор упал
        """
        order = self.get_object()
        driver_id = request.data.get("driver_id")
        if not driver_id:
            return Response({"detail": "driver_id required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            driver = Driver.objects.select_for_update().get(pk=driver_id)
        except Driver.DoesNotExist:
            return Response({"detail": "Driver not found"}, status=status.HTTP_404_NOT_FOUND)
        if driver.status != DriverStatus.AVAILABLE:
            return Response({"detail": "Driver not available"}, status=status.HTTP_409_CONFLICT)

        driver.status = DriverStatus.BUSY
        order.assigned_driver = driver
        order.status = OrderStatus.DRIVER_ASSIGNED
        driver.save()
        order.save()

        data = self.get_serializer(order).data
        # защищённый broadcast
        broadcast({"type": "order_assigned", "order": data})
        return Response(data)

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        order = self.get_object()
        if not order.assigned_driver:
            return Response({"detail": "У заказа нет назначенного водителя."}, status=status.HTTP_409_CONFLICT)
        order.status = OrderStatus.IN_PROGRESS
        order.save()
        data = self.get_serializer(order).data
        broadcast({"type": "order_started", "order": data})
        return Response(data)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        order = self.get_object()
        order.status = OrderStatus.COMPLETED
        if order.assigned_driver:
            d = order.assigned_driver
            d.status = DriverStatus.AVAILABLE
            d.save()
        order.save()
        data = self.get_serializer(order).data
        broadcast({"type": "order_completed", "order": data})
        return Response(data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        oid = str(instance.id)
        self.perform_destroy(instance)
        broadcast({"type": "order_deleted", "order_id": oid})
        return Response(status=status.HTTP_204_NO_CONTENT)