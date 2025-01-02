# notifications/admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import Notification
from .utils import send_push_notification

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at', 'is_read', 'image_preview')
    list_filter = ('is_read', 'created_at')
    search_fields = ('title', 'message', 'user__username')
    
    actions = ['send_notification', 'send_push_notification']

    # Display thumbnail of image in admin
    def image_preview(self, obj):
        if obj.image:
            return format_html(f'<img src="{obj.image.url}" width="50" height="50" />')
        return "-"
    image_preview.short_description = "Image Preview"

    # Action to send an in-app notification
    def send_notification(self, request, queryset):
        notifications_sent = 0
        already_sent = 0

        for notification in queryset:
            if not notification.is_read:
                notification.is_read = True
                notification.save()
                notifications_sent += 1
            else:
                already_sent += 1

        self.message_user(request, f"{notifications_sent} in-app notification(s) sent successfully.")
        if already_sent:
            self.message_user(request, f"{already_sent} notification(s) were already sent.", level="warning")

    send_notification.short_description = "Send selected in-app notifications"

    # Action to send push notifications
    def send_push_notification(self, request, queryset):
        notifications_sent = 0
        failed_notifications = 0

        for notification in queryset:
            try:
                # Customize push notification details
                title = notification.title
                message = notification.message
                image_url = request.build_absolute_uri(notification.image.url) if notification.image else None
                launch_url = notification.launch_url

                # Send push notification to all active devices
                send_push_notification(title=title, message=message, image_url=image_url, launch_url=launch_url)
                notifications_sent += 1
            except Exception as e:
                failed_notifications += 1
                self.message_user(
                    request, f"Failed to send push notification '{notification.title}': {str(e)}", level="error"
                )

        self.message_user(request, f"{notifications_sent} push notification(s) sent successfully.")
        if failed_notifications:
            self.message_user(request, f"{failed_notifications} push notification(s) failed.", level="error")

    send_push_notification.short_description = "Send selected push notifications to all devices"

    # Automatically send a push notification on save if it's a new notification
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        
        if not change:  # Only send push notification on creation, not update
            image_url = request.build_absolute_uri(obj.image.url) if obj.image else None
            launch_url = obj.launch_url
            try:
                send_push_notification(obj.title, obj.message, image_url=image_url, launch_url=launch_url)
                self.message_user(request, f"Push notification '{obj.title}' sent successfully on creation.")
            except Exception as e:
                self.message_user(request, f"Failed to send push notification '{obj.title}': {str(e)}", level="error")

admin.site.register(Notification, NotificationAdmin)
