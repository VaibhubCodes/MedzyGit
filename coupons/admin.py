# admin.py

from django.contrib import admin
from .models import Coupon

class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_amount', 'expiry_date', 'usage_limit', 'times_used', 'is_valid')
    search_fields = ('code',)
    list_filter = ('expiry_date', 'discount_type', 'usage_limit')

    def is_valid(self, obj):
        return obj.is_valid()
    is_valid.boolean = True
    is_valid.short_description = 'Valid'

admin.site.register(Coupon, CouponAdmin)
