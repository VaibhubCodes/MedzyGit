from rest_framework import generics, permissions
from .models import Conversions,OrderSettings # Make sure this matches the actual model name
from .serializers import ConversionsSerializer,BannerSerializer,OrderSettingsSerializer
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Banner


class ConversionsListView(generics.ListAPIView):
    queryset = Conversions.objects.all()
    serializer_class = ConversionsSerializer
    permission_classes = [permissions.IsAdminUser]  # Restrict access to admins

class BannersByTypeView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request, banner_type):
        banners = Banner.objects.filter(banner_type=banner_type)
        serializer = BannerSerializer(banners, many=True)
        return Response(serializer.data)
class OrderSettingsView(APIView):
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        settings = OrderSettings.get_order_settings()
        serializer = OrderSettingsSerializer(settings)
        return Response(serializer.data)

    def patch(self, request):
        settings = OrderSettings.get_order_settings()
        serializer = OrderSettingsSerializer(settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)