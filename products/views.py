import csv
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import Category, SubCategory, Brand, Product, ProductAttribute
from .serializers import (
    CategorySerializer,
    SubCategorySerializer,
    BrandSerializer,
    ProductSerializer
)

# --- Category Views ---
class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all().order_by("id")
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


# --- SubCategory Views ---
class SubCategoryListCreateView(generics.ListCreateAPIView):
    queryset = SubCategory.objects.all().order_by("id")
    serializer_class = SubCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class SubCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SubCategory.objects.all()
    serializer_class = SubCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


# --- Brand Views ---
class BrandListCreateView(generics.ListCreateAPIView):
    queryset = Brand.objects.all().order_by("id")
    serializer_class = BrandSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class BrandDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


# --- Product Views ---
class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.all().order_by("id")
    serializer_class = ProductSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def create(self, request, *args, **kwargs):
        attributes = request.data.get("attributes")
        if attributes and isinstance(attributes, str):
            try:
                parsed_attributes = json.loads(attributes)
                request.data["attributes"] = parsed_attributes
            except json.JSONDecodeError:
                return Response({"error": "Invalid JSON format for attributes."}, status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def update(self, request, *args, **kwargs):
        attributes = request.data.get("attributes")
        if attributes and isinstance(attributes, str):
            try:
                attributes = json.loads(attributes)
            except json.JSONDecodeError:
                return Response({"error": "Invalid JSON format for attributes."}, status=status.HTTP_400_BAD_REQUEST)

        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        if attributes is not None:
            instance.attributes.all().delete()
            for attr in attributes:
                ProductAttribute.objects.create(product=instance, **attr)

        return Response(serializer.data)


# --- Bulk Upload Products ---
class BulkUploadProductsView(APIView):
    """
    Handle bulk uploading of products via CSV file.
    """
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, *args, **kwargs):
        if "file" not in request.FILES:
            return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES["file"]
        decoded_file = file.read().decode("utf-8").splitlines()
        reader = csv.DictReader(decoded_file)

        errors = []
        success_count = 0

        for row in reader:
            try:
                # Fetch related objects by name
                category = Category.objects.get(name=row["Category"].strip())
                subcategory = SubCategory.objects.get(name=row["Subcategory"].strip(), category=category)
                brand = Brand.objects.get(name=row["Brand"].strip())

                # Create product
                product = Product.objects.create(
                    name=row["Name"].strip(),
                    description=row.get("Description", "").strip(),
                    price=float(row["Price"]),
                    stock=int(row["Stock"]),
                    category=category,
                    subcategory=subcategory,
                    brand=brand,
                )

                # Add attributes if present
                if "Attributes" in row and row["Attributes"]:
                    attributes = json.loads(row["Attributes"])
                    for attr in attributes:
                        ProductAttribute.objects.create(
                            product=product,
                            name=attr["name"],
                            value=attr["value"],
                            additional_price=float(attr.get("additional_price", 0)),
                        )

                success_count += 1

            except Exception as e:
                errors.append({"row": row, "error": str(e)})

        response_data = {
            "success_count": success_count,
            "errors": errors,
        }

        if errors:
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        return Response(response_data, status=status.HTTP_201_CREATED)
