from django.db import models

class Conversions(models.Model):
    referral_reward_points = models.PositiveIntegerField(default=10, help_text="Points awarded per referral")
    point_to_cash_conversion_rate = models.DecimalField(max_digits=10, decimal_places=2, default=1.0, help_text="Conversion rate from points to wallet cash")

    @classmethod
    def get_conversion_settings(cls):
        # Ensures only one record exists and fetches it
        conversion, created = cls.objects.get_or_create(id=1)
        return conversion

    def __str__(self):
        return f"Referral Points: {self.referral_reward_points}, Conversion Rate: {self.point_to_cash_conversion_rate}"
class Banner(models.Model):
    BANNER_TYPES = [
        (1, 'Offer Banner'),
        (2, 'Main Banner'),
        (3, 'Secondary Banner'),
    ]

    banner_type = models.IntegerField(choices=BANNER_TYPES, help_text="Type of banner")
    image = models.ImageField(upload_to='banners/images/', blank=True, null=True, help_text="Image for the banner")
    redirect_url = models.URLField(blank=True, null=True, help_text="Optional URL to redirect when banner is clicked")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Banner ID: {self.id}, Type: {self.get_banner_type_display()}"
class OrderSettings(models.Model):
    cod_enabled = models.BooleanField(default=True, help_text="Enable Cash on Delivery")
    wallet_enabled = models.BooleanField(default=True, help_text="Enable payment via Wallet Balance")
    razorpay_enabled = models.BooleanField(default=True, help_text="Enable Razorpay Payment Gateway")

    @classmethod
    def get_order_settings(cls):
        settings, created = cls.objects.get_or_create(id=1)
        return settings

    def __str__(self):
        return f"COD: {self.cod_enabled}, Wallet: {self.wallet_enabled}, Razorpay: {self.razorpay_enabled}"