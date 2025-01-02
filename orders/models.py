# orders/models.py

from django.db import models
from django.contrib.auth import get_user_model
from products.models import Product,ProductAttribute
from users.models import Address
from coupons.models import Coupon
from django.db.models.signals import post_save
from django.dispatch import receiver
from notifications.models import Notification
from notifications.utils import send_push_notification
import logging


logger = logging.getLogger(__name__)

User = get_user_model()

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart - {self.user.username}"

# orders/models.py

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    selected_attribute = models.ForeignKey(ProductAttribute, on_delete=models.SET_NULL, null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)  # Add this field

    def __str__(self):
        return f"{self.quantity} of {self.product.name} in {self.cart.user.username}'s cart"

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} - {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE,default=1)
    selected_attribute = models.ForeignKey(ProductAttribute, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

class OrderStatus(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('On Route', 'On Route'),
        ('Completed', 'Completed')
    ]
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_updates')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.order.id} - {self.status}"


@receiver(post_save, sender='orders.OrderStatus')
def send_order_status_update_notification(sender, instance, created, **kwargs):
        if not created:  # only for updates
            user = instance.order.user
            title = "Order Status Update"
            message = f"Your order #{instance.order.id} status has been updated to {instance.status}."
            

            # Create in-app notification
            Notification.objects.create(
                user=user,
                title=title,
                message=message,
                
            )
            
            # Send push notification
            send_push_notification(title=title, message=message)
class Payment(models.Model):
    PAYMENT_METHODS = [
        ('COD', 'Cash on Delivery'),
        ('Wallet', 'Wallet'),
        ('Razorpay', 'Razorpay Payment Gateway'),
    ]

    PAYMENT_STATUS = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    order = models.OneToOneField('Order', on_delete=models.CASCADE, related_name='payment')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='Pending')
    payment_id = models.CharField(max_length=100, blank=True, null=True)  # Razorpay or other gateway payment ID
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for Order {self.order.id} - {self.payment_status}"