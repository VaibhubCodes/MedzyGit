from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, Address, Referral

class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('username', 'name', 'phone_number', 'wallet_balance', 'reward_points', 'profile_photo')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'username', 'name', 'phone_number', 'profile_photo'),
        }),
    )
    list_display = ('email', 'username', 'name', 'is_staff', 'wallet_balance', 'reward_points', 'profile_photo_thumbnail')
    search_fields = ('email', 'username', 'name')
    ordering = ('email',)

    def profile_photo_thumbnail(self, obj):
        if obj.profile_photo:
            return format_html('<img src="{}" width="30" height="30" style="border-radius: 50%;" />', obj.profile_photo.url)
        return "No Photo"
    profile_photo_thumbnail.short_description = 'Profile Photo'

admin.site.register(User, UserAdmin)
admin.site.register(Address)
admin.site.register(Referral)
