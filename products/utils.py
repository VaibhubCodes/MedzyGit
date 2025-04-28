import json
from .models import ProductAttribute

def create_product_attributes(product, attributes_data):
    """
    Parse and create ProductAttribute instances for a given product.

    :param product: The product instance
    :param attributes_data: A JSON string or a list of attribute dictionaries
    """
    # Ensure attributes_data is a list
    if isinstance(attributes_data, str):
        try:
            attributes_data = json.loads(attributes_data)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format for attributes.")

    if not isinstance(attributes_data, list):
        raise ValueError("Attributes must be a list of dictionaries.")

    # Loop through the attributes and create ProductAttribute instances
    for attr in attributes_data:
        ProductAttribute.objects.create(
            product=product,
            name=attr.get('name', ''),
            value=attr.get('value', ''),
            additional_price=attr.get('additional_price', 0.00)
        )
