# notifications/utils.py

import requests
from django.conf import settings

def send_push_notification(title, message, image_url=None, launch_url=None):
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Basic {settings.ONESIGNAL_API_KEY}",
    }

    payload = {
        "app_id": settings.ONESIGNAL_APP_ID,
        "included_segments": ["All"],
        "headings": {"en": title},
        "contents": {"en": message},
    }

    # Add big picture for image preview on mobile notification
    if image_url:
        payload["big_picture"] = image_url

    if launch_url:
        payload["url"] = launch_url

    response = requests.post("https://onesignal.com/api/v1/notifications", json=payload, headers=headers)
    
    if response.status_code == 200:
        print("Push notification sent successfully.")
    else:
        print(f"Failed to send push notification: {response.status_code}, {response.text}")
