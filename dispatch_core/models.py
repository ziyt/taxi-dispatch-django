from django.db import models
import uuid

class DriverStatus:
    AVAILABLE = "Available"
    BUSY = "Busy"
    OFFLINE = "Offline"

    CHOICES = [
        (AVAILABLE, "Available"),
        (BUSY, "Busy"),
        (OFFLINE, "Offline"),
    ]

class OrderStatus:
    NEW = "New"
    DRIVER_ASSIGNED = "DriverAssigned"
    IN_PROGRESS = "InProgress"   # ← добавили
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

    CHOICES = [
        (NEW, "New"),
        (DRIVER_ASSIGNED, "DriverAssigned"),
        (IN_PROGRESS, "InProgress"),
        (COMPLETED, "Completed"),
        (CANCELLED, "Cancelled"),
    ]

class Driver(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    callsign = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=32, choices=DriverStatus.CHOICES, default=DriverStatus.AVAILABLE)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.callsign

class RideOrder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer_phone = models.CharField(max_length=32)
    from_address = models.CharField(max_length=255)
    to_address = models.CharField(max_length=255, blank=True, default="")
    from_lat = models.FloatField(null=True, blank=True)
    from_lng = models.FloatField(null=True, blank=True)
    to_lat = models.FloatField(null=True, blank=True)
    to_lng = models.FloatField(null=True, blank=True)
    assigned_driver = models.ForeignKey(Driver, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=32, choices=OrderStatus.CHOICES, default=OrderStatus.NEW)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer_phone} {self.from_address} → {self.to_address}"