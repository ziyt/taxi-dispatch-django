from rest_framework import serializers
from dispatch_core.models import Driver, RideOrder

class DriverSerializer(serializers.ModelSerializer):
    distance_m = serializers.FloatField(required=False, read_only=True)

    class Meta:
        model = Driver
        fields = "__all__"

class RideOrderSerializer(serializers.ModelSerializer):
    assigned_driver_callsign = serializers.SerializerMethodField()
    has_coords = serializers.SerializerMethodField()

    class Meta:
        model = RideOrder
        fields = "__all__"

    def get_assigned_driver_callsign(self, obj):
        return obj.assigned_driver.callsign if obj.assigned_driver else None

    def get_has_coords(self, obj):
        return obj.from_lat is not None and obj.from_lng is not None