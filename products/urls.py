# products/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('categories/', views.CategoryListCreateView.as_view(), name='category-list-create'),
    path('subcategories/', views.SubCategoryListCreateView.as_view(), name='subcategory-list-create'),
    path('brands/', views.BrandListCreateView.as_view(), name='brand-list-create'),
    path('products/', views.ProductListCreateView.as_view(), name='product-list-create'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
]
