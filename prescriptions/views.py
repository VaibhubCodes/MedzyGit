from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Prescription, PrescriptionItem, PrescriptionOrder
from .serializers import PrescriptionSerializer, PrescriptionOrderSerializer
from products.models import Product
from coupons.models import Coupon
from decimal import Decimal
from dal import autocomplete
import hmac
import hashlib
import razorpay
from django.conf import settings


import logging
logger = logging.getLogger(__name__)

class PrescriptionViewSet(viewsets.ModelViewSet):
    queryset = Prescription.objects.all()
    serializer_class = PrescriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        image = self.request.data.get('image')
        if not image:
            return Response({"detail": "Image is required."}, status=status.HTTP_400_BAD_REQUEST)
        serializer.save(user=self.request.user, image=image)

    def get_queryset(self):
        return Prescription.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='items', permission_classes=[permissions.IsAdminUser])
    def items(self, request, pk=None):
        """
        Add an item to a prescription.
        """
        try:
            prescription = self.get_object()
            product_id = request.data.get('product_id')
            quantity = int(request.data.get('quantity', 1))

            if not product_id:
                return Response({"detail": "Product ID is required."}, status=status.HTTP_400_BAD_REQUEST)

            product = Product.objects.get(id=product_id)
            PrescriptionItem.objects.create(
                prescription=prescription,
                product=product,
                quantity=quantity
            )
            return Response({"detail": "Product added to prescription."}, status=status.HTTP_201_CREATED)

        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'], url_path='update-status', permission_classes=[permissions.IsAdminUser])
    def update_status(self, request, pk=None):
            """
            Update the status of a prescription.
            """
            logger.info(f"Updating status for prescription ID: {pk}")
            try:
                prescription = self.get_object()
                new_status = request.data.get('status')

                if not new_status:
                    return Response({"detail": "New status is required."}, status=status.HTTP_400_BAD_REQUEST)

                if new_status not in ['Pending', 'Approved', 'Rejected', 'Completed']:
                    return Response({"detail": "Invalid status value."}, status=status.HTTP_400_BAD_REQUEST)

                prescription.status = new_status
                prescription.save()

                return Response({"detail": "Prescription status updated successfully.", "new_status": prescription.status}, status=status.HTTP_200_OK)

            except Exception as e:
                logger.error(f"Error updating status: {e}")
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def approve(self, request, pk=None):
        prescription = self.get_object()
        if prescription.status != 'Pending':
            return Response({'detail': 'Prescription has already been processed'}, status=status.HTTP_400_BAD_REQUEST)

        if not prescription.items.exists():
            return Response({'detail': 'No items found in the prescription.'}, status=status.HTTP_400_BAD_REQUEST)

        # Approve the prescription
        prescription.status = 'Approved'
        total_amount = sum(item.product.price * item.quantity for item in prescription.items.all())
        prescription.total_amount = total_amount
        prescription.payment_status = 'Pending'
        prescription.save()

        # Create PrescriptionOrder with calculated total amount
        order = PrescriptionOrder.objects.create(
            prescription=prescription,
            total_amount=total_amount,
            payment_status='Pending'
        )

        return Response({
            'status': 'Prescription Approved and Order Created. Total Amount Calculated',
            'order_id': order.id
        }, status=status.HTTP_200_OK)

    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def reject(self, request, pk=None):
        prescription = self.get_object()
        if prescription.status != 'Pending':
            return Response({'detail': 'Prescription has already been processed'}, status=status.HTTP_400_BAD_REQUEST)

        prescription.status = 'Rejected'
        prescription.save()
        return Response({'status': 'Prescription Rejected'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def complete_payment(self, request, pk=None):
        prescription = self.get_object()
        if prescription.payment_status == 'Completed':
            return Response({'detail': 'Payment has already been completed'}, status=status.HTTP_400_BAD_REQUEST)

        payment_method = request.data.get('payment_method')
        if not payment_method:
            return Response({'detail': 'Payment method is required.'}, status=status.HTTP_400_BAD_REQUEST)

        if payment_method == 'Wallet':
            user = request.user
            if user.wallet_balance < prescription.total_amount:
                return Response({'detail': 'Insufficient wallet balance.'}, status=status.HTTP_400_BAD_REQUEST)

            user.wallet_balance -= Decimal(prescription.total_amount)
            user.save()

            prescription.payment_status = 'Completed'
            prescription.save()

            return Response({'status': 'Payment completed via Wallet.'}, status=status.HTTP_200_OK)

        elif payment_method == 'Razorpay':
            # Create Razorpay client
            client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET))

            # Convert the total amount from rupees to paise
            amount_in_paise = int(prescription.total_amount * 100)

            # Create an order on Razorpay
            razorpay_order = client.order.create({
                'amount': amount_in_paise,  # Razorpay expects amount in paise
                'currency': 'INR',
                'payment_capture': '1'
            })

            # Save the Razorpay order ID and other details in PrescriptionOrder
            PrescriptionOrder.objects.create(
                prescription=prescription,
                total_amount=prescription.total_amount,
                payment_status='Pending',
                payment_method='Razorpay',
                razorpay_order_id=razorpay_order['id']
            )

            # Return the order details for the frontend
            return Response({
                'status': 'Razorpay order created.',
                'order_id': razorpay_order['id'],
                'amount': prescription.total_amount,  # Send the amount in rupees for display
                'currency': razorpay_order['currency'],
            }, status=status.HTTP_200_OK)

        return Response({'detail': 'Invalid payment method.'}, status=status.HTTP_400_BAD_REQUEST)





class PrescriptionOrderViewSet(viewsets.ModelViewSet):
    queryset = PrescriptionOrder.objects.all()
    serializer_class = PrescriptionOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PrescriptionOrder.objects.filter(prescription__user=self.request.user)
    

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def items(self, request, pk=None):
        logger.info(f"Adding item to prescription ID: {pk}")
        logger.info(f"Request data: {request.data}")

        try:
            prescription = self.get_object()
            logger.info(f"Prescription found: {prescription}")
            product_id = request.data.get('product_id')
            quantity = int(request.data.get('quantity', 1))

            if not product_id:
                logger.error("Product ID is missing.")
                return Response({"detail": "Product ID is required."}, status=status.HTTP_400_BAD_REQUEST)

            product = Product.objects.get(id=product_id)
            logger.info(f"Product found: {product}")
            PrescriptionItem.objects.create(
                prescription=prescription,
                product=product,
                quantity=quantity
            )
            logger.info("Product added to prescription successfully.")
            return Response({"detail": "Product added to prescription."}, status=status.HTTP_201_CREATED)

        except Product.DoesNotExist:
            logger.error("Product not found.")
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error adding item to prescription: {str(e)}")
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAdminUser])
    def update_payment_status(self, request, pk=None):
        """
        Update the payment status of a prescription order.
        """
        try:
            order = self.get_object()
            new_payment_status = request.data.get('payment_status')

            if not new_payment_status:
                return Response({"detail": "New payment status is required."}, status=status.HTTP_400_BAD_REQUEST)

            if new_payment_status not in ['Pending', 'Completed', 'Failed']:
                return Response({"detail": "Invalid payment status value."}, status=status.HTTP_400_BAD_REQUEST)

            order.payment_status = new_payment_status
            order.save()

            return Response({"detail": "Payment status updated successfully.", "new_payment_status": order.payment_status}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def apply_coupon(self, request, pk=None):
        """
        Apply a coupon to a prescription order and calculate the final discounted total.
        """
        order = self.get_object()
        coupon_code = request.data.get('coupon_code')

        # Check if a coupon is already applied
        if order.coupon:
            return Response({
                'detail': 'A coupon has already been applied to this order.'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not coupon_code:
            return Response({'detail': 'Coupon code is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            coupon = Coupon.objects.get(code=coupon_code)
            if not coupon.is_valid():
                return Response({'detail': 'Coupon is invalid or expired.'}, status=status.HTTP_400_BAD_REQUEST)

            # Ensure the total amount is a valid Decimal
            total_amount = Decimal(order.total_amount)

            # Calculate discount based on the coupon type
            if coupon.discount_type == 'percentage':
                discount = (total_amount * Decimal(coupon.discount_amount) / 100)
            elif coupon.discount_type == 'flat':
                discount = Decimal(coupon.discount_amount)
            else:
                return Response({'detail': 'Invalid discount type.'}, status=status.HTTP_400_BAD_REQUEST)

            # Ensure the discount does not exceed the total amount
            discount = min(discount, total_amount)
            order.discount_amount = discount  # Store the discount amount in the order
            order.total_amount = total_amount - discount  # Reduce the total amount by the discount
            order.coupon = coupon  # Link the coupon to the order
            order.save()

            return Response({
                'status': 'Coupon applied successfully.',
                'discount': float(discount),
                'new_total': float(order.total_amount),
            }, status=status.HTTP_200_OK)

        except Coupon.DoesNotExist:
            return Response({'detail': 'Invalid coupon code.'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def pay(self, request, pk=None):
        order = self.get_object()
        if order.payment_status == 'Completed':
            return Response({'detail': 'Payment has already been completed.'}, status=status.HTTP_400_BAD_REQUEST)

        payment_method = request.data.get('payment_method')
        if not payment_method:
            return Response({'detail': 'Payment method is required.'}, status=status.HTTP_400_BAD_REQUEST)

        if payment_method == 'Wallet':
            user = request.user
            if user.wallet_balance < order.total_amount:
                return Response({'detail': 'Insufficient wallet balance.'}, status=status.HTTP_400_BAD_REQUEST)

            # Deduct from wallet and mark payment as completed
            user.wallet_balance -= Decimal(order.total_amount)
            user.save()

            order.payment_status = 'Completed'
            order.save()
            order.prescription.payment_status = 'Completed'
            order.prescription.save()

            return Response({'status': 'Payment completed via Wallet.', 'final_amount': order.total_amount}, status=status.HTTP_200_OK)

        elif payment_method == 'Razorpay':
            client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET))
            amount_in_paise = int(order.total_amount * 100)
            razorpay_order = client.order.create({
                'amount': amount_in_paise,
                'currency': 'INR',
                'payment_capture': '1'
            })

            order.razorpay_order_id = razorpay_order['id']
            order.payment_method = 'Razorpay'
            order.save()

            return Response({
                'status': 'Razorpay order created.',
                'order_id': razorpay_order['id'],
                'amount': order.total_amount,
                'currency': razorpay_order['currency'],
            }, status=status.HTTP_200_OK)

        return Response({'detail': 'Invalid payment method.'}, status=status.HTTP_400_BAD_REQUEST)


class RazorpayPaymentVerificationView(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def verify_payment(self, request):
        razorpay_payment_id = request.data.get('razorpay_payment_id')
        razorpay_order_id = request.data.get('razorpay_order_id')
        razorpay_signature = request.data.get('razorpay_signature')

        if not (razorpay_payment_id and razorpay_order_id and razorpay_signature):
            return Response({'detail': 'Missing Razorpay details.'}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch the prescription order associated with this Razorpay order
        try:
            prescription_order = PrescriptionOrder.objects.get(razorpay_order_id=razorpay_order_id)
        except PrescriptionOrder.DoesNotExist:
            return Response({'detail': 'Prescription order not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Verify the Razorpay signature
        generated_signature = hmac.new(
            settings.RAZORPAY_API_SECRET.encode('utf-8'),
            f'{razorpay_order_id}|{razorpay_payment_id}'.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        if generated_signature == razorpay_signature:
            # Mark the payment as completed if signature is valid
            prescription_order.payment_status = 'Completed'
            prescription_order.save()

            # Update the related prescription's payment status
            prescription_order.prescription.payment_status = 'Completed'
            prescription_order.prescription.save()

            return Response({'status': 'Payment verified successfully.'}, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'Invalid payment signature.'}, status=status.HTTP_400_BAD_REQUEST)

class ProductAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Product.objects.none()

        qs = Product.objects.all()

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs
