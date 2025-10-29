from django.contrib import admin
from .models import Driver, RideOrder

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ("callsign", "status", "lat", "lng", "updated_at")
    list_filter = ("status",)
    search_fields = ("callsign",)

@admin.register(RideOrder)
class RideOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_phone", "status", "created_at", "assigned_driver")
    list_filter = ("status", "created_at")
    search_fields = ("customer_phone", "from_address", "to_address")
    autocomplete_fields = ("assigned_driver",)