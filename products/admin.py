# products/admin.py

from django.contrib import admin
from django.urls import path
from .models import Category, SubCategory, Brand, Product, ProductAttribute
from .admin_views import upload_subcategories_csv, upload_products_csv

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description')
    search_fields = ('name',)
    ordering = ('id',)

class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'description')
    search_fields = ('name', 'category__name')
    list_filter = ('category',)
    ordering = ('id',)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('upload-csv/', self.admin_site.admin_view(upload_subcategories_csv), name='upload_subcategories_csv')
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['upload_csv_url'] = 'upload-csv/'
        extra_context['add_subcategory_url'] = '../add/'
        return super().changelist_view(request, extra_context=extra_context)

admin.site.register(SubCategory, SubCategoryAdmin)

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description')
    search_fields = ('name',)
    ordering = ('id',)

class ProductAttributeInline(admin.TabularInline):
    model = ProductAttribute
    extra = 1  # Number of empty fields to display for adding new attributes
    fields = ('name', 'value', 'additional_price')
    search_fields = ('value')
    readonly_fields = ('id',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'subcategory', 'brand', 'price', 'stock', 'created_at')
    search_fields = ('name', 'category__name', 'subcategory__name', 'brand__name')
    list_filter = ('category', 'subcategory', 'brand')
    ordering = ('id',)
    inlines = [ProductAttributeInline]  # Inline attributes

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('upload-csv/', self.admin_site.admin_view(upload_products_csv), name='upload_products_csv'),
        ]
        return custom_urls + urls

    change_list_template = "admin/products/product_changelist.html"

# Registering ProductAttribute model is optional here, as it's included inline with Product
