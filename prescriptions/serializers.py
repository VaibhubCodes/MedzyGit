from rest_framework import serializers
from .models import Prescription, PrescriptionItem, PrescriptionOrder
from products.models import Product

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'image'] 

class PrescriptionItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = PrescriptionItem
        fields = ['product', 'quantity', 'total_price']


class PrescriptionSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    items = PrescriptionItemSerializer(many=True, read_only=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    payment_status = serializers.CharField(read_only=True)
    
    # We'll define `PrescriptionOrderSerializer` inline to avoid circular import
    order = serializers.SerializerMethodField()

    class Meta:
        model = Prescription
        fields = ['id', 'user', 'image', 'status', 'items', 'created_at', 'total_amount', 'payment_status', 'order']
        read_only_fields = ['status', 'created_at', 'total_amount', 'payment_status']

    def get_order(self, obj):
        try:
            # Get the related order object if it exists
            order = obj.order
            return PrescriptionOrderSerializer(order).data
        except PrescriptionOrder.DoesNotExist:
            return None


class PrescriptionOrderSerializer(serializers.ModelSerializer):
    prescription_items = PrescriptionItemSerializer(source='prescription.items', many=True, read_only=True)

    class Meta:
        model = PrescriptionOrder
        fields = ['id', 'total_amount', 'payment_status', 'payment_method', 'razorpay_order_id', 'prescription_items']

