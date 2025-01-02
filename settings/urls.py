from django.urls import path
from .views import ConversionsListView,BannersByTypeView,OrderSettingsView

urlpatterns = [
    path('settings/conversions/', ConversionsListView.as_view(), name='conversions-list'),
    path('settings/banners/<int:banner_type>/', BannersByTypeView.as_view(), name='banners-by-type'),
    path('settings/order-options/', OrderSettingsView.as_view(), name='order-options'),
]
