import hmac
import hashlib
import razorpay
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Cart, CartItem, Order, OrderItem, OrderStatus,Address,Payment
from .serializers import CartSerializer, CartItemSerializer, OrderSerializer, OrderStatusSerializer
from products.models import Product, ProductAttribute
from settings.models import OrderSettings
from decimal import Decimal
from coupons.models import Coupon
from rest_framework.views import APIView
from notifications.models import Notification
from notifications.utils import send_push_notification
import logging

logger = logging.getLogger(__name__)
# --- Updated Cart View ---
class CartView(generics.RetrieveUpdateAPIView):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart

    def cart_view(self, request):
        cart = Cart.objects.filter(user=request.user).prefetch_related(
            'items__product', 'items__selected_attribute'
        ).first()

        if not cart:
            return Response({"message": "Cart not found"}, status=404)
        
        serializer = CartSerializer(cart)
        return Response(serializer.data)

# --- Updated Cart Item Add View ---
class CartItemAddView(generics.CreateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        product_id = self.request.data.get('product')
        product = get_object_or_404(Product, id=product_id)

        selected_attribute_id = self.request.data.get('selected_attribute')
        selected_attribute = None
        if selected_attribute_id:
            selected_attribute = get_object_or_404(ProductAttribute, id=selected_attribute_id)

        serializer.save(cart=cart, product=product, selected_attribute=selected_attribute)


class CartItemUpdateView(generics.UpdateAPIView):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only allow updates to items in the authenticated user's cart
        return CartItem.objects.filter(cart__user=self.request.user)

# --- Updated Cart Item Delete View ---
class CartItemDeleteView(generics.DestroyAPIView):
    queryset = CartItem.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)

# --- Updated Order Placement View ---
from django.shortcuts import get_object_or_404
from coupons.models import Coupon

class OrderPlacementView(generics.CreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # Retrieve the user's cart
        cart = Cart.objects.filter(user=request.user).first()
        if not cart or not cart.items.exists():
            return Response({"detail": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        # Get payment method, address ID, and optional coupon code from request data
        payment_method = request.data.get("payment_method")
        address_id = request.data.get("address_id")
        coupon_code = request.data.get("coupon_code")

        if not payment_method:
            return Response({"detail": "Payment method is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not address_id:
            return Response({"detail": "Delivery address is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch the address instance using the address_id
        address = get_object_or_404(Address, id=address_id, user=request.user)

        # Retrieve order settings (ensure OrderSettings is properly defined)
        settings_obj = OrderSettings.get_order_settings()

        # Calculate total amount based on products in the cart
        total_amount = sum(
            (float(item.product.price) + (float(item.selected_attribute.additional_price) if item.selected_attribute else 0)) * item.quantity
            for item in cart.items.all()
        )

        # Apply coupon discount if a valid coupon code is provided
        discount = Decimal(0)
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code)
                if coupon.is_valid():
                    if coupon.discount_type == 'percentage':
                        discount = (Decimal(total_amount) * Decimal(coupon.discount_amount) / 100).quantize(Decimal('0.01'))
                    elif coupon.discount_type == 'flat':
                        discount = Decimal(coupon.discount_amount)
                    discount = min(discount, total_amount)  # Ensure discount doesn't exceed total amount
                    total_amount -= discount  # Apply the discount
                else:
                    return Response({"detail": "Coupon is invalid or expired"}, status=status.HTTP_400_BAD_REQUEST)
            except Coupon.DoesNotExist:
                return Response({"detail": "Invalid coupon code"}, status=status.HTTP_400_BAD_REQUEST)

        # Create the order with the discounted total amount
        order = Order.objects.create(
            user=request.user,
            total_amount=total_amount,
            delivery_address=address
        )

        # Create the initial order status as "Pending"
        OrderStatus.objects.create(
            order=order,
            status="Pending"
        )

        # Handle payment processing based on the selected method
        if payment_method == "COD":
            return self.handle_cod_payment(order, cart, settings_obj, total_amount)
        elif payment_method == "Wallet":
            return self.handle_wallet_payment(order, cart, settings_obj, total_amount, request.user)
        elif payment_method == "Razorpay":
            return self.handle_razorpay_payment(order, cart, total_amount)

        return Response({"detail": "Invalid payment method"}, status=status.HTTP_400_BAD_REQUEST)

    # Helper methods for handling payments remain unchanged...
    # Helper method for Cash on Delivery (COD) payment
    def handle_cod_payment(self, order, cart, settings_obj, total_amount):
        if not settings_obj.cod_enabled:
            return Response({"detail": "Cash on Delivery is disabled"}, status=status.HTTP_400_BAD_REQUEST)

        Payment.objects.create(
            user=order.user,
            order=order,
            payment_method="COD",
            payment_status="Pending",
            amount=total_amount
        )

        self.create_order_items(order, cart)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    # Helper method for Wallet payment
    def handle_wallet_payment(self, order, cart, settings_obj, total_amount, user):
        if not settings_obj.wallet_enabled:
            return Response({"detail": "Wallet payment is disabled"}, status=status.HTTP_400_BAD_REQUEST)
        if user.wallet_balance < total_amount:
            return Response({"detail": "Insufficient wallet balance"}, status=status.HTTP_400_BAD_REQUEST)

        user.wallet_balance -= Decimal(total_amount)
        user.save()

        Payment.objects.create(
            user=user,
            order=order,
            payment_method="Wallet",
            payment_status="Completed",
            amount=total_amount
        )

        self.create_order_items(order, cart)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    # Helper method for Razorpay payment
    def handle_razorpay_payment(self, order, cart, total_amount):
        try:
            client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET))
            razorpay_order = client.order.create({
                "amount": int(total_amount * 100),  # Convert to paise
                "currency": "INR",
                "payment_capture": 1
            })
        except razorpay.errors.BadRequestError as e:
            return Response({"detail": "Razorpay order creation failed", "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        Payment.objects.create(
            user=order.user,
            order=order,
            payment_method="Razorpay",
            payment_status="Pending",
            amount=total_amount,
            payment_id=razorpay_order["id"]
        )

        self.create_order_items(order, cart)
        return Response({
            "order_id": razorpay_order["id"],
            "amount": razorpay_order["amount"],
            "currency": razorpay_order["currency"],
            "order_db_id": order.id
        }, status=status.HTTP_201_CREATED)

    # Helper method to create order items and clear cart
    def create_order_items(self, order, cart):
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=float(item.product.price),
                selected_attribute=item.selected_attribute
            )
        cart.items.all().delete()


class ApplyCouponView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        coupon_code = request.data.get('coupon_code')
        
        # Retrieve or create the cart for the authenticated user
        cart, created = Cart.objects.get_or_create(user=request.user)

        # Check if the cart is empty
        if not cart.items.exists():
            return Response({"detail": "Cart is empty, cannot apply coupon."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if coupon code is provided
        if not coupon_code:
            return Response({"detail": "Coupon code is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Retrieve the coupon and check if it's valid
            coupon = Coupon.objects.get(code=coupon_code)
            if not coupon.is_valid():
                return Response({"detail": "Coupon is invalid or expired."}, status=status.HTTP_400_BAD_REQUEST)

            # Calculate the cart total
            total_amount = sum(
                (Decimal(item.product.price) + (Decimal(item.selected_attribute.additional_price) if item.selected_attribute else 0)) * item.quantity
                for item in cart.items.all()
            )

            # Calculate discount based on coupon type
            if coupon.discount_type == 'percentage':
                discount = (total_amount * Decimal(coupon.discount_amount) / 100).quantize(Decimal('0.01'))
            elif coupon.discount_type == 'flat':
                discount = Decimal(coupon.discount_amount)
            else:
                return Response({"detail": "Invalid discount type."}, status=status.HTTP_400_BAD_REQUEST)

            # Ensure discount doesn't exceed total amount
            discount = min(discount, total_amount)
            discounted_total = total_amount - discount

            return Response({
                "status": "Coupon applied successfully.",
                "discount": float(discount),
                "new_total": float(discounted_total)
            }, status=status.HTTP_200_OK)

        except Coupon.DoesNotExist:
            return Response({"detail": "Invalid coupon code."}, status=status.HTTP_400_BAD_REQUEST)




# --- Razorpay Payment Verification View ---
class RazorpayPaymentVerificationView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Retrieve the Razorpay payment details from the request
        razorpay_payment_id = request.data.get('razorpay_payment_id')
        razorpay_order_id = request.data.get('razorpay_order_id')
        razorpay_signature = request.data.get('razorpay_signature')
        order_db_id = request.data.get('order_db_id')

        # Get the order from the database
        order = get_object_or_404(Order, id=order_db_id, user=request.user)

        # Fetch the payment linked to this order
        payment = get_object_or_404(Payment, order=order, payment_id=razorpay_order_id)

        # Verify the signature using Razorpay's secret key
        key_secret = settings.RAZORPAY_API_SECRET.encode('utf-8')
        generated_signature = hmac.new(
            key_secret,
            (razorpay_order_id + "|" + razorpay_payment_id).encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # If the signature matches, update the order and payment status
        if generated_signature == razorpay_signature:
            # Update the order status to 'Completed'
            order.status = "Completed"
            order.save()

            # Update the payment status to 'Completed'
            payment.payment_status = "Completed"
            payment.save()

            return Response({"detail": "Payment verified successfully"}, status=status.HTTP_200_OK)
        else:
            # If signature verification fails, mark the payment as failed
            payment.payment_status = "Failed"
            payment.save()

            return Response({"detail": "Payment verification failed"}, status=status.HTTP_400_BAD_REQUEST)
        
# --- Order Status Update View ---
# orders/views.py

class OrderStatusUpdateView(generics.UpdateAPIView):
    queryset = OrderStatus.objects.all()
    serializer_class = OrderStatusSerializer
    permission_classes = [permissions.IsAdminUser]

    
    def perform_update(self, serializer):
        # Save the updated instance
        instance = serializer.save()

        # Log to check if perform_update is triggered
        logger.info(f"perform_update called for OrderStatus ID {instance.id}.")

        # Get the related order and user
        order = instance.order
        user = order.user

        # Create an in-app notification
        try:
            Notification.objects.create(
                user=user,
                title="Order Status Update",
                message=f"Your order #{order.id} status has been updated to {instance.status}."
            )
            logger.info(f"Notification created for user {user.username} on order #{order.id}.")
        except Exception as e:
            logger.error(f"Failed to create in-app notification: {e}")

        # Send a push notification
        try:
            notification_sent = send_push_notification(
                user_id=user.id,
                title="Order Status Update",
                message=f"Your order #{order.id} status is now {instance.status}."
            )
            logger.info(f"Push notification sent for order #{order.id}: {notification_sent}")
        except Exception as e:
            logger.error(f"Failed to send push notification: {e}")


# --- Order Status List View ---
class OrderStatusListView(generics.ListAPIView):
    serializer_class = OrderStatusSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return OrderStatus.objects.filter(order__user=self.request.user)
class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')