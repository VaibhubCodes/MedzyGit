# views.py

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Coupon
from .serializers import CouponSerializer
from orders.models import Order  # Assuming you have an Order model linked to the coupon

class CouponViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer

    @action(detail=False, methods=['post'])
    def validate_coupon(self, request):
        code = request.data.get('code', '')
        total_amount = request.data.get('total_amount', 0)
        try:
            coupon = Coupon.objects.get(code=code)
            if coupon.is_valid():
                # Calculate the discount based on coupon type
                discount = coupon.apply_discount(total_amount)
                return Response({'valid': True, 'discount': discount, 'message': 'Coupon is valid'})
            return Response({'valid': False, 'message': 'Coupon has expired or usage limit reached'}, status=status.HTTP_400_BAD_REQUEST)
        except Coupon.DoesNotExist:
            return Response({'valid': False, 'message': 'Invalid coupon code'}, status=status.HTTP_400_BAD_REQUEST)

    