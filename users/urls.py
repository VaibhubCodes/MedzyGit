from django.urls import path
from .views import UserRegisterView, UserProfileView, AddressListView,AddressUpdateView, ReferralView, ConvertPointsView,LoginView

urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='user-register'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('convert-points/', ConvertPointsView.as_view(), name='convert-points'),
    path('addresses/', AddressListView.as_view(), name='address-list'),
    path('addresses/<int:id>/', AddressUpdateView.as_view(), name='address-update'),
    path('referrals/', ReferralView.as_view(), name='user-referrals'),  # Added ReferralView here
    path('login/', LoginView.as_view(), name='user-login'),
]
