# orders/urls.py

from django.urls import path
from .views import (
    CartView,
    CartItemAddView,
    CartItemDeleteView,
    OrderPlacementView,
    OrderStatusUpdateView,
    OrderStatusListView,
    CartItemUpdateView,
    RazorpayPaymentVerificationView,
    ApplyCouponView,
    OrderListView
)

urlpatterns = [
    path('cart/', CartView.as_view(), name='cart'),                        # Get or update cart
    path('cart/item/add/', CartItemAddView.as_view(), name='cart-item-add'),  # Add item to cart
    path('cart/item/delete/<int:pk>/', CartItemDeleteView.as_view(), name='cart-item-delete'),  # Delete item from cart
    path('order/place/', OrderPlacementView.as_view(), name='order-place'),  # Place an order
    path('order/status/update/<int:pk>/', OrderStatusUpdateView.as_view(), name='order-status-update'),
    path('cart/item/update/<int:pk>/', CartItemUpdateView.as_view(), name='cart-item-update'),  # Update order status
    path('order/status/', OrderStatusListView.as_view(), name='order-status-list'),  # List order statuses for the user
    path('payment/verify/', RazorpayPaymentVerificationView.as_view(), name='payment-verify'),
    path('cart/apply_coupon/', ApplyCouponView.as_view(), name='apply-coupon'),
    path('order/list/', OrderListView.as_view(), name='order-list'),  # New endpoint for listing orders

]
