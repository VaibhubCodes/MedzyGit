from rest_framework import serializers
from .models import User, Address, Referral
from settings.models import Conversions  # Import Conversions

class UserSerializer(serializers.ModelSerializer):
    referral_code = serializers.CharField(write_only=True, required=False)
    password = serializers.CharField(write_only=True, required=True)
    profile_photo = serializers.ImageField(required=False)  # Add profile photo field

    class Meta:
        model = User
        fields = [
            'id', 'username', 'name', 'email', 'phone_number', 'wallet_balance',
            'reward_points', 'referral_code', 'password', 'profile_photo'
        ]
        read_only_fields = ['username', 'wallet_balance', 'reward_points']

    def create(self, validated_data):
        referral_code = validated_data.pop('referral_code', None)
        password = validated_data.pop('password')
        profile_photo = validated_data.pop('profile_photo', None)

        # Derive the username from the email
        email = validated_data.get('email')
        username = email.split('@')[0]
        validated_data['username'] = username

        # Create the user and set the password
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        
        # Handle profile photo if provided
        if profile_photo:
            user.profile_photo = profile_photo

        user.save()

        # Referral logic
        if referral_code:
            try:
                referring_user = User.objects.get(username=referral_code)
                conversion_settings = Conversions.get_conversion_settings()
                referring_user.reward_points += conversion_settings.referral_reward_points
                referring_user.save()
                Referral.objects.create(
                    user=referring_user, 
                    referred_user=user, 
                    reward_points=conversion_settings.referral_reward_points
                )
            except User.DoesNotExist:
                raise serializers.ValidationError("Invalid referral code.")
        
        return user
    def update(self, instance, validated_data):
        # Update name and phone_number only
        instance.name = validated_data.get('name', instance.name)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        
        instance.save()
        return instance

    def update(self, instance, validated_data):
        # Handle password update
        if 'password' in validated_data:
            instance.set_password(validated_data.pop('password'))

        # Update profile photo if provided
        profile_photo = validated_data.pop('profile_photo', None)
        if profile_photo:
            instance.profile_photo = profile_photo

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance




class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'address_type', 'street_address', 'city', 'state', 'postal_code', 'country']

class ReferralSerializer(serializers.ModelSerializer):
    class Meta:
        model = Referral
        fields = ['id', 'user', 'referred_user', 'reward_points']
