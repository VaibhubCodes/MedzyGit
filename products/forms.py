# products/forms.py

from django import forms

class SubCategoryCSVUploadForm(forms.Form):
    csv_file = forms.FileField(label='Upload CSV File')
class ProductCSVUploadForm(forms.Form):
    csv_file = forms.FileField(label='Upload Product CSV File')