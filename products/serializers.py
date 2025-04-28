# products/serializers.py
import json
from rest_framework import serializers
from .models import Category, SubCategory, Brand, Product, ProductAttribute

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']

class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        fields = ['id', 'name', 'category', 'description', 'image']

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'description', 'image']

class ProductAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductAttribute
        fields = ['id', 'name', 'value', 'additional_price']

class ProductSerializer(serializers.ModelSerializer):
    attributes = ProductAttributeSerializer(many=True, required=False)

    class Meta:
        model = Product
        fields = ['id', 'category', 'subcategory', 'brand', 'name', 'description', 'price', 'stock', 'image', 'attributes']

    def create(self, validated_data):
        # Extract attributes data
        attributes_data = validated_data.pop('attributes', [])
        
        # Create the Product instance
        product = Product.objects.create(**validated_data)

        # Add attributes if provided
        if attributes_data:
            for attr in attributes_data:
                if isinstance(attr, str):  # Parse JSON string if necessary
                    attr = json.loads(attr)
                ProductAttribute.objects.create(product=product, **attr)

        return product

    def update(self, instance, validated_data):
        # Extract attributes data
        attributes_data = validated_data.pop('attributes', None)

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Handle attributes
        if attributes_data is not None:
            if isinstance(attributes_data, str):  # Parse JSON string if necessary
                try:
                    attributes_data = json.loads(attributes_data)
                except json.JSONDecodeError:
                    raise serializers.ValidationError("Invalid JSON format for attributes.")

            # Clear existing attributes and add new ones
            instance.attributes.all().delete()
            for attr in attributes_data:
                ProductAttribute.objects.create(product=instance, **attr)

        instance.save()
        return instance
