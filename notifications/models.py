# notifications/models.py

from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
import os
from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from .utils import send_push_notification
import logging

logger = logging.getLogger(__name__)
User = get_user_model()
User = get_user_model()

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    image = models.ImageField(upload_to='notification_images/', null=True, blank=True)
    launch_url = models.URLField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.user.username}"

    def get_image_url(self):
        # Construct the full URL for the image if it exists
        if self.image:
            return f"{settings.MEDIA_URL}{self.image}"
        return None

@receiver(post_save, sender=Notification)
def order_status_update_notification(sender, instance, created, **kwargs):
    if not created:
        # Prepare notification details
        title = instance.title
        message = instance.message
        image_url = instance.image.url if instance.image else None
        launch_url = instance.launch_url
        
        try:
            # Send push notification when the order status updates
            send_push_notification(title=title, message=message, image_url=image_url, launch_url=launch_url)
            logger.info(f"Push notification '{title}' sent successfully.")
        except Exception as e:
            logger.error(f"Failed to send push notification: {str(e)}")