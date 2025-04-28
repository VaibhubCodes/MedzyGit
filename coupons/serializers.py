# serializers.py

from rest_framework import serializers
from .models import Coupon

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ['id','code', 'discount_amount', 'expiry_date', 'usage_limit', 'times_used']
