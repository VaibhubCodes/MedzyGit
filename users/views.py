from rest_framework import generics, permissions, views, status,serializers
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from .models import User, Address, Referral
from .serializers import UserSerializer, AddressSerializer, ReferralSerializer
from settings.models import Conversions
from rest_framework.views import APIView


import logging

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

            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user_id': user.pk,
                'email': user.email,
                'username': user.username
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
