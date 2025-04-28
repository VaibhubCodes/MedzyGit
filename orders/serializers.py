# orders/serializers.py
from users.models import User
from users.serializers import UserSerializer
from rest_framework import serializers
from .models import Cart, CartItem, Order, OrderItem, OrderStatus, Product, ProductAttribute, Payment, Address

class ProductAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductAttribute
        fields = ['id', 'value', 'additional_price']

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'image', 'description', 'price']

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    selected_attribute = ProductAttributeSerializer(read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'selected_attribute']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items']

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['street_address', 'city', 'state', 'postal_code', 'country']

class OrderItemSerializer(serializers.ModelSerializer):
    selected_attribute = ProductAttributeSerializer(read_only=True)
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price', 'selected_attribute']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        product_price = float(instance.product.price)
        attribute_price = float(instance.selected_attribute.additional_price) if instance.selected_attribute else 0
        total_price = (product_price + attribute_price) * instance.quantity
        representation['total_price'] = total_price
        return representation

class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatus
        fields = ['id', 'order', 'status', 'updated_at']

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['payment_method', 'payment_status', 'payment_id', 'amount']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    payment_details = serializers.SerializerMethodField()
    latest_status = serializers.SerializerMethodField()
    delivery_address = AddressSerializer(read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)  # Format date and time
    user = serializers.SerializerMethodField()  # Use a custom field for user details

    class Meta:
        model = Order
        fields = ['id', 'user', 'total_amount', 'delivery_address', 'items', 'payment_details', 'latest_status','created_at']

    def get_user(self, obj):
        # Fetch the full user details
        user = User.objects.filter(id=obj.user.id).first()
        if user:
            return {"id": user.id, "name": user.name, "email": user.email}
        return None

    def get_payment_details(self, obj):
        payment = Payment.objects.filter(order=obj).first()
        if payment:
            return PaymentSerializer(payment).data
        return None

    def get_latest_status(self, obj):
        latest_status = OrderStatus.objects.filter(order=obj).order_by('-updated_at').first()
        if latest_status:
            return OrderStatusSerializer(latest_status).data
        return None
