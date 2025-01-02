from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PrescriptionViewSet, PrescriptionOrderViewSet,ProductAutocomplete,RazorpayPaymentVerificationView

router = DefaultRouter()
router.register(r'prescriptions', PrescriptionViewSet, basename='prescription')
router.register(r'orders', PrescriptionOrderViewSet, basename='prescription-order')

urlpatterns = [
    path('', include(router.urls)),
    path('product-autocomplete/', ProductAutocomplete.as_view(), name='product-autocomplete'),
    path('orders/payment/verify/', RazorpayPaymentVerificationView.as_view({'post': 'verify_payment'}), name='verify-payment'),

]
