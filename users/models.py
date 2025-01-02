from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.core.validators import RegexValidator
from settings.models import Conversions  # Import from settings app

class User(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15, validators=[RegexValidator(r'^\+?1?\d{9,15}$')])
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    reward_points = models.PositiveIntegerField(default=0)
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)  # Add profile photo field
    groups = models.ManyToManyField(Group, related_name="custom_user_groups", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="custom_user_permissions", blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'name', 'phone_number']

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email.split('@')[0]
        super(User, self).save(*args, **kwargs)

    def __str__(self):
        return self.email

    def convert_points_to_cash(self, points):
        conversion_settings = Conversions.get_conversion_settings()
        cash_amount = points * conversion_settings.point_to_cash_conversion_rate
        self.wallet_balance += cash_amount
        self.reward_points -= points  # Deduct only the specified points
        self.save()


class Address(models.Model):
    user = models.ForeignKey(User, related_name='addresses', on_delete=models.CASCADE)
    address_type = models.CharField(max_length=20, choices=(('home', 'Home'), ('office', 'Office'), ('other', 'Other')))
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.user.name} - {self.address_type}"

class Referral(models.Model):
    user = models.ForeignKey(User, related_name='referrals', on_delete=models.CASCADE)
    referred_user = models.ForeignKey(User, related_name='referred_by', on_delete=models.CASCADE)
    reward_points = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} referred {self.referred_user.username}"
