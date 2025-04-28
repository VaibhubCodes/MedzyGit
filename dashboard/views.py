from rest_framework.decorators import api_view
from rest_framework.response import Response
from products.models import Product
from orders.models import Order
from products.serializers import ProductSerializer
from django.db.models import Sum

@api_view(['GET'])
def dashboard_data(request):
    total_products = Product.objects.count()

    new_orders = Order.objects.filter(latest_status__status="Pending").count()

    total_revenue = Order.objects.filter(latest_status__status="Completed").aggregate(
        Sum("total_amount")
    )["total_amount__sum"] or 0

    # Dynamically calculate popular products
    popular_products = Product.objects.annotate(
        total_sales=Sum('orderitem__quantity')
    ).order_by('-total_sales')[:5]

    serialized_popular_products = ProductSerializer(popular_products, many=True).data

    return Response({
        "totalProducts": total_products,
        "newOrders": new_orders,
        "totalRevenue": total_revenue,
        "popularProducts": serialized_popular_products,
    })
