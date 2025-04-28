from django.urls import path
from .views import UserListView,WalletView,WalletTopUpView,WalletTopUpConfirmView, UserRegisterView, UserProfileView, LogoutView, AddressListView, AddressUpdateView, ReferralView, ConvertPointsView, LoginView

urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='user-register'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('convert-points/', ConvertPointsView.as_view(), name='convert-points'),
    path('addresses/', AddressListView.as_view(), name='address-list'),
    path('addresses/<int:id>/', AddressUpdateView.as_view(), name='address-update'),
    path('referrals/', ReferralView.as_view(), name='user-referrals'),
    path('login/', LoginView.as_view(), name='user-login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('wallet/', WalletView.as_view(), name='wallet'),
    path('wallet/topup/', WalletTopUpView.as_view(), name='wallet-topup'),
    path('wallet/topup/confirm/', WalletTopUpConfirmView.as_view(), name='wallet-topup-confirm'),
]
