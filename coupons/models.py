# models.py

from django.db import models
from django.utils import timezone

DISCOUNT_TYPE_CHOICES = (
    ('flat', 'Flat Discount'),
    ('percentage', 'Percentage Discount'),
)

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES, default='flat')
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    expiry_date = models.DateField()
    usage_limit = models.IntegerField(default=1)
    times_used = models.IntegerField(default=0)

    def is_valid(self):
        # Check if the coupon is still valid based on expiry and usage limits
        return self.expiry_date >= timezone.now().date() and self.times_used < self.usage_limit

    def apply_discount(self, total_amount):
        """
        Calculate the discount based on the coupon's type.
        If percentage, calculate as a percentage of the total amount.
        If flat, simply subtract the flat discount from the total.
        """
        if not self.is_valid():
            raise ValueError("Coupon is not valid")
        
        if self.discount_type == 'percentage':
            # Apply percentage discount
            discount = total_amount * (self.discount_amount / 100)
        else:
            # Apply flat discount
            discount = self.discount_amount
        
        # Ensure the discount does not exceed the total amount
        return min(discount, total_amount)

    def __str__(self):
        return f"{self.code} ({self.get_discount_type_display()} - {self.discount_amount})"
