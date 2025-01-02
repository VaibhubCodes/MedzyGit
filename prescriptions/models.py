from django.db import models
from django.conf import settings
from products.models import Product
from django.utils import timezone
from coupons.models import Coupon
class Prescription(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Dispatched', 'Dispatched'),
        ('Completed', 'Completed'),
        ('Rejected', 'Rejected')
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='prescriptions/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    payment_status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Completed', 'Completed')], default='Pending')

    def __str__(self):
        return f"Prescription by {self.user.email} - {self.status}"


class PrescriptionItem(models.Model):
    prescription = models.ForeignKey(Prescription, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"Item: {self.product.name} - {self.quantity}"

    @property
    def total_price(self):
        return self.product.price * self.quantity  # Total price for the item based on quantity



class PrescriptionOrder(models.Model):
    prescription = models.OneToOneField(Prescription, on_delete=models.CASCADE, related_name='order')  # Link to Prescription
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Completed', 'Completed')], default='Pending')
    payment_method = models.CharField(max_length=20, choices=[('Wallet', 'Wallet'), ('Razorpay', 'Razorpay')], blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    razorpay_order_id = models.CharField(max_length=255, blank=True, null=True)  # Add this field
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)  # Add this line
    def __str__(self):
        return f"Order for {self.prescription.user.email} - {self.payment_status}"

