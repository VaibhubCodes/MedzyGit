from rest_framework import generics, permissions, views, status,serializers
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from .models import User, Address, Referral,WalletTransaction
from .serializers import UserSerializer, AddressSerializer, ReferralSerializer,WalletTransactionSerializer
from settings.models import Conversions
from rest_framework.views import APIView
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework.permissions import AllowAny
import logging
from decimal import Decimal
class UserRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        referral_code = self.request.data.get('referral_code', None)
        user = serializer.save()
        Address.objects.create(
            user=user,
            address_type='home',  # Default type
            street_address='',
            city='',
            state='',
            postal_code='',
            country=''
        )

        

from rest_framework_simplejwt.tokens import RefreshToken

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'error': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            if not user.check_password(password):
                logging.error(f"Password check failed for user with email: {email}")
                return Response({'error': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                }
            })

        except User.DoesNotExist:
            logging.error(f"User with email {email} not found.")
            return Response({'error': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)


class UserProfileView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)  # Allow partial updates
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        # Log the incoming request data for debugging
        logging.debug(f"Incoming data for profile update: {request.data}")

        # Validate the serializer
        if not serializer.is_valid():
            logging.error(f"Validation errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Perform update
        self.perform_update(serializer)
        logging.debug(f"Profile updated successfully for user {instance.username}")
        
        return Response(serializer.data)


class AddressListView(generics.ListCreateAPIView):
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AddressUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'  # The field to look up the address by, in this case, 'id'

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

class ReferralView(generics.ListAPIView):
    serializer_class = ReferralSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Referral.objects.filter(user=self.request.user)

class ConvertPointsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        points = request.data.get('points', 0)  # Get points from request data
        points = int(points)  # Ensure points are an integer

        if points <= 0 or points > request.user.reward_points:
            return Response({"error": "Invalid number of points specified for conversion."}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        user.convert_points_to_cash(points)
        
        return Response({
            "message": f"{points} points converted to wallet cash successfully",
            "wallet_balance": user.wallet_balance,
            "reward_points": user.reward_points  # Return updated reward points
        })
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            # Blacklist all tokens for the user
            tokens = OutstandingToken.objects.filter(user=request.user)
            for token in tokens:
                BlacklistedToken.objects.get_or_create(token=token)

            return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            logging.error(f"Logout failed for user {request.user.username}: {str(e)}")
            return Response({"error": "Logout failed. Please try again."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class UserListView(generics.ListAPIView):
    """
    View to list all users in the system.
    Accessible to admin or staff users only.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser] 

# users/views.py

class WalletView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        transactions = WalletTransaction.objects.filter(user=user).order_by('-timestamp')
        serializer = WalletTransactionSerializer(transactions, many=True)
        return Response({
            "wallet_balance": user.wallet_balance,
            "transactions": serializer.data
        })
import razorpay
from django.conf import settings

class WalletTopUpView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        amount = request.data.get('amount')
        
        if not amount or float(amount) <= 0:
            return Response({"error": "Invalid amount"}, status=status.HTTP_400_BAD_REQUEST)

        client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET))
        razorpay_order = client.order.create({
            "amount": int(float(amount) * 100),  # Amount in paise
            "currency": "INR",
            "payment_capture": 1
        })

        return Response({
            "order_id": razorpay_order["id"],
            "amount": razorpay_order["amount"],
            "currency": razorpay_order["currency"],
        })
class WalletTopUpConfirmView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        amount = request.data.get('amount')
        if not amount:
            return Response({'error': 'Amount is required.'}, status=400)

        user = request.user
        user.wallet_balance += Decimal(str(amount))  # ✅ Fix here
        user.save()

        return Response({'message': 'Wallet balance updated successfully!'})

        WalletTransaction.objects.create(
            user=user,
            transaction_type='credit',
            amount=amount,
            description="Wallet Top-up via Razorpay"
        )

        return Response({"message": "Wallet balance updated successfully", "wallet_balance": user.wallet_balance})
