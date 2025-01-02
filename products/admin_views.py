# products/admin_views.py

import csv
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import path
from .models import Category, SubCategory,Product,Brand
from .forms import SubCategoryCSVUploadForm,ProductCSVUploadForm
import traceback

def upload_subcategories_csv(request):
    if request.method == 'POST':
        form = SubCategoryCSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            try:
                # Try reading with UTF-8 encoding first
                try:
                    csv_file.seek(0)  # Reset file pointer
                    decoded_file = csv_file.read().decode('utf-8')
                except UnicodeDecodeError as e:
                    print(f"Unicode decode error encountered with UTF-8: {e}")
                    csv_file.seek(0)  # Reset file pointer for retry
                    decoded_file = csv_file.read().decode('ISO-8859-1', errors='ignore')
                    print("Retried with ISO-8859-1 encoding")

                # Process the CSV content
                reader = csv.reader(decoded_file.splitlines())
                header = next(reader, None)  # Skip header row if exists

                if header is None:
                    raise ValueError("The CSV file is empty or improperly formatted.")

                for row in reader:
                    if len(row) >= 3:
                        category_name, subcategory_name, description = row[:3]
                        category, created = Category.objects.get_or_create(name=category_name)
                        SubCategory.objects.update_or_create(
                            name=subcategory_name,
                            defaults={'category': category, 'description': description}
                        )

                messages.success(request, "Sub-categories uploaded successfully!")
            except Exception as e:
                print(traceback.format_exc())  # Print full traceback for debugging
                messages.error(request, f"Error processing file: {str(e)}")
            return redirect('admin:products_subcategory_changelist')
    else:
        form = SubCategoryCSVUploadForm()
    return render(request, 'admin/products/upload_csv.html', {'form': form})
def upload_products_csv(request):
    if request.method == 'POST':
        form = ProductCSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            for row in reader:
                category, _ = Category.objects.get_or_create(name=row['Category'])
                subcategory = None
                brand = None
                if row.get('SubCategory'):
                    subcategory, _ = SubCategory.objects.get_or_create(name=row['SubCategory'], category=category)
                if row.get('Brand'):
                    brand, _ = Brand.objects.get_or_create(name=row['Brand'])
                
                # Handle optional fields
                attributes = row.get('Attributes', '{}')  # JSON-like string in the CSV
                image_path = row.get('Image')
                
                product, created = Product.objects.update_or_create(
                    name=row['Name'],
                    defaults={
                        'category': category,
                        'subcategory': subcategory,
                        'brand': brand,
                        'description': row.get('Description', ''),
                        'price': row.get('Price', 0),
                        'stock': row.get('Stock', 0),
                        'attributes': attributes,
                    }
                )
            messages.success(request, "Products uploaded successfully!")
            return redirect('admin:products_product_changelist')
    else:
        form = ProductCSVUploadForm()
    return render(request, 'admin/products/upload_products_csv.html', {'form': form})