from django.contrib import admin
from .models import Conversions,Banner,OrderSettings

class ConversionsAdmin(admin.ModelAdmin):
    list_display = ('referral_reward_points', 'point_to_cash_conversion_rate')

class BannerAdmin(admin.ModelAdmin):
    list_display = ('id', 'banner_type', 'image', 'created_at')
    list_filter = ('banner_type',)
    search_fields = ('banner_type',)
class OrderSettingsAdmin(admin.ModelAdmin):
    list_display = ('cod_enabled', 'wallet_enabled', 'razorpay_enabled')

admin.site.register(Conversions, ConversionsAdmin)
admin.site.register(Banner, BannerAdmin)
admin.site.register(OrderSettings, OrderSettingsAdmin)