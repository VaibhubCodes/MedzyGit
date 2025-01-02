from django.contrib import admin
from django.http import HttpResponse
from reportlab.pdfgen import canvas
import qrcode
import io
from .models import Cart, CartItem, Order, OrderItem, OrderStatus, Payment
from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
import io
import qrcode
from PIL import Image
from django.conf import settings
import os

# Inlined OrderItem model to display items in the Order admin
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price', 'get_selected_attribute')

    # Custom method to display selected product attribute in the order item
    def get_selected_attribute(self, obj):
        if obj.selected_attribute:
            return f'{obj.selected_attribute.name}: {obj.selected_attribute.value} (+₹{obj.selected_attribute.additional_price})'
        return "No attributes"
    
    get_selected_attribute.short_description = 'Selected Product Attributes'


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ('payment_method', 'payment_status', 'payment_id', 'amount', 'created_at')


class OrderStatusInline(admin.TabularInline):
    model = OrderStatus
    extra = 0
    readonly_fields = ('updated_at',)
    fields = ('status', 'updated_at')  # Expose the status and updated_at field

def generate_pdf_with_qrcode(order):
    # Create a BytesIO buffer to hold the PDF data
    buffer = io.BytesIO()

    # Generate a QR code
    qr_data = f"Order ID: {order.id}, User: {order.user.username}, Amount: {order.total_amount}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill='black', back_color='white')
    
    # Create a BytesIO buffer for the QR code image
    qr_buffer = io.BytesIO()
    
    # Save the QR code image to the buffer
    img.save(qr_buffer, format="PNG")  # Specify the image format explicitly
    qr_buffer.seek(0)  # Move to the start of the BytesIO object
    
    # Create the PDF using ReportLab
    pdf = canvas.Canvas(buffer)
    pdf.drawString(100, 750, "Order Slip")
    pdf.drawString(100, 730, f"Order ID: {order.id}")
    pdf.drawString(100, 710, f"User: {order.user.username}")
    pdf.drawString(100, 690, f"Total Amount: {order.total_amount}")
    
    # Insert the QR code into the PDF
    pdf.drawInlineImage(qr_buffer, 100, 600, width=100, height=100)

    # Close and save the PDF
    pdf.showPage()
    pdf.save()

    # Return a response with the PDF
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')
# Custom method to generate a PDF order slip
def print_order_slip(modeladmin, request, queryset):
    for order in queryset:
        # Create a PDF in memory
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Set a font
        p.setFont("Helvetica", 10)

        # Create the section boxes and lines

        # Sender's Address (From Section)
        p.drawString(50, 730, "From:")
        p.setFont("Helvetica-Bold", 10)
        p.drawString(50, 715, "Near Airport")
        p.drawString(50, 700, "Shivaji Terminal")
        p.drawString(50, 685, "Air Strip Number 32")
        p.drawString(50, 670, "Mumbai - 400001, India")

        # Logo on the right side
        p.setFont("Helvetica", 10)
        logo_path = f"{settings.MEDIA_ROOT}/logo_files/Medzy_BW.jpg"
        try:
            p.drawImage(logo_path, 400, 680, width=1.5 * inch, height=1.5 * inch, preserveAspectRatio=True)
        except Exception as e:
            p.drawString(400, 720, "Logo not found")
        
        # Customer Information (To Section)
        p.setFont("Helvetica-Bold", 10)
        p.drawString(50, 640, "To:")
        p.setFont("Helvetica", 10)
        p.drawString(50, 625, f"{order.user.name}")
        p.drawString(50, 610, f"{order.delivery_address.street_address}")
        p.drawString(50, 595, f"{order.delivery_address.city}, {order.delivery_address.postal_code}")
        p.drawString(50, 580, f"{order.user.phone_number}")

        # QR Code (On the right side of To)
        qr_data = f"Order ID: {order.id}, Total Amount: ₹{order.total_amount}, Customer: {order.user.username}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')

        # Convert the PIL image to an ImageReader object for ReportLab
        qr_buffer = io.BytesIO()
        img.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)
        qr_img = ImageReader(qr_buffer)
        p.drawImage(qr_img, 400, 580, width=100, height=100)

        # Draw Border between sections
        p.line(50, 570, width - 50, 570)  # Separator line

        # Ordered Items Section (Full Width)
        p.setFont("Helvetica-Bold", 10)
        p.drawString(50, 555, "Ordered Items:")
        y_position = 540
        for item in order.items.all():
            item_details = f"{item.quantity}x {item.product.name} ({item.selected_attribute.value if item.selected_attribute else 'No Attribute'})"
            p.drawString(50, y_position, item_details)
            y_position -= 15
        
        # Draw border around Ordered Items Section
        p.line(50, 570, 50, y_position)  # Left line
        p.line(width - 50, 570, width - 50, y_position)  # Right line
        p.line(50, y_position, width - 50, y_position)  # Bottom line
        
        # Order Summary Section (Full Width)
        p.setFont("Helvetica-Bold", 10)
        p.drawString(50, y_position - 20, "Order Summary:")
        p.setFont("Helvetica", 10)
        p.drawString(50, y_position - 35, f"Order ID: {order.id}")
        p.drawString(50, y_position - 50, f"Total Amount: ₹{order.total_amount}")
        p.drawString(50, y_position - 65, f"Payment Method: {order.payment.payment_method}")
        
        # Draw border around the Order Summary
        p.line(50, y_position - 20, width - 50, y_position - 20)  # Top line
        p.line(50, y_position - 85, width - 50, y_position - 85)  # Bottom line
        p.line(50, y_position - 20, 50, y_position - 85)  # Left line
        p.line(width - 50, y_position - 20, width - 50, y_position - 85)  # Right line

        # Finalize and save the PDF
        p.showPage()
        p.save()
        
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Order_{order.id}_Slip.pdf"'
        return response


print_order_slip.short_description = "Print Order Slip"



@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'get_current_status',
        'total_amount',
        'get_payment_method',
        'get_payment_status',
        'get_payment_id',
        'created_at'
    )
    search_fields = ('user__username', 'user__email')
    ordering = ('-created_at',)
    list_filter = ('created_at',)
    
    actions = [print_order_slip]  # Add the custom action

    # Display the latest order status
    def get_current_status(self, obj):
        latest_status = obj.status_updates.order_by('-updated_at').first()
        return latest_status.status if latest_status else 'No Status'
    get_current_status.short_description = 'Status'

    # Custom method to display payment method
    def get_payment_method(self, obj):
        payment = Payment.objects.filter(order=obj).first()
        return payment.payment_method if payment else 'N/A'
    get_payment_method.short_description = 'Payment Method'

    # Custom method to display payment status
    def get_payment_status(self, obj):
        payment = Payment.objects.filter(order=obj).first()
        return payment.payment_status if payment else 'N/A'
    get_payment_status.short_description = 'Payment Status'

    # Custom method to display payment ID
    def get_payment_id(self, obj):
        payment = Payment.objects.filter(order=obj).first()
        return payment.payment_id if payment else 'N/A'
    get_payment_id.short_description = 'Payment ID'

    # Custom method to show ordered items
    def get_ordered_items(self, obj):
        items = obj.items.all()
        return ', '.join([f'{item.quantity}x {item.product.name} ({item.selected_attribute.value if item.selected_attribute else "No Attribute"})' for item in items])
    get_ordered_items.short_description = 'Ordered Items'

    readonly_fields = ['created_at', 'get_ordered_items', 'get_current_status', 'get_payment_method', 'get_payment_status', 'get_payment_id']

    # Organize the fields in the detail view of the order
    fieldsets = (
        (None, {
            'fields': (
                'user',
                'total_amount',
                'get_ordered_items',
                'get_payment_method',
                'get_payment_status',
                'get_payment_id',
                'get_current_status',
                'created_at',
            )
        }),
    )

    inlines = [OrderItemInline, PaymentInline, OrderStatusInline]  # Add OrderStatusInline to allow status change


# Register other models
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at')
    search_fields = ('user__username', 'user__email')
    list_filter = ('created_at',)
    ordering = ('-created_at',)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'quantity', 'price')
    search_fields = ('product__name', 'order__user__username')
    ordering = ('order',)


@admin.register(OrderStatus)
class OrderStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'status', 'updated_at')
    search_fields = ('order__user__username', 'status')
    list_filter = ('status', 'updated_at')
    ordering = ('-updated_at',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'order',
        'user',
        'payment_method',
        'payment_status',
        'payment_id',
        'amount',
        'created_at'
    )
    search_fields = ('order__user__username', 'payment_id', 'user__email')
    list_filter = ('payment_method', 'payment_status', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('payment_id', 'created_at')

    fieldsets = (
        (None, {
            'fields': ('order', 'user', 'payment_method', 'amount')
        }),
        ('Payment Details', {
            'fields': ('payment_status', 'payment_id', 'created_at'),
        }),
    )
