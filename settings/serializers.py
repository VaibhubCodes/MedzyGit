from rest_framework import serializers
from .models import Conversions,Banner,OrderSettings

class ConversionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversions
        fields = ['referral_reward_points', 'point_to_cash_conversion_rate']
# settings/serializers.py
from rest_framework import serializers

class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = ['id', 'banner_type', 'image', 'redirect_url']
class OrderSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderSettings
        fields = ['cod_enabled', 'wallet_enabled', 'razorpay_enabled']