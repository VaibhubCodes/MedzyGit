from rest_framework import serializers
from .models import Prescription, PrescriptionItem, PrescriptionOrder
from products.models import Product
from users.serializers import AddressSerializer
from users.models import Address
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

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            'id', 'address_type', 'street_address', 'city', 'state', 
            'postal_code', 'country'
        ]

class PrescriptionSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    items = PrescriptionItemSerializer(many=True, read_only=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    payment_status = serializers.CharField(read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)
    mobile_number = serializers.CharField(source='user.phone_number', read_only=True)
    address = serializers.SerializerMethodField()
    order = serializers.SerializerMethodField()

    class Meta:
        model = Prescription
        fields = ['id', 'user', 'image','user_name','mobile_number', 'address', 'status', 'items', 'created_at', 'total_amount', 'payment_status', 'order']
        read_only_fields = ['status', 'created_at', 'total_amount', 'payment_status', 'mobile_number']

    
    def get_order(self, obj):
        try:
            # Get the related order object if it exists
            order = obj.order
            return PrescriptionOrderSerializer(order).data
        except PrescriptionOrder.DoesNotExist:
            return None
    def get_address(self, obj):
        # Fetch the default address for the user
        user = obj.user
        address = user.addresses.first()  # Assuming the first address is the default
        if address:
            return AddressSerializer(address).data
        return None

class PrescriptionOrderSerializer(serializers.ModelSerializer):
    prescription_items = PrescriptionItemSerializer(source='prescription.items', many=True, read_only=True)

    class Meta:
        model = PrescriptionOrder
        fields = ['id', 'total_amount', 'payment_status', 'payment_method', 'razorpay_order_id', 'prescription_items']

