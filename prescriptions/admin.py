from django.contrib import admin
from django import forms
from .models import Prescription, PrescriptionItem, PrescriptionOrder
from products.models import Product
from dal import autocomplete


class PrescriptionItemForm(forms.ModelForm):
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        widget=autocomplete.ModelSelect2(url='product-autocomplete')  # Using Autocomplete
    )

    class Meta:
        model = PrescriptionItem
        fields = ['product', 'quantity']


class PrescriptionItemInline(admin.TabularInline):
    model = PrescriptionItem
    form = PrescriptionItemForm
    extra = 1
    can_delete = True


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'total_amount', 'payment_status', 'created_at']
    list_filter = ['status', 'created_at', 'payment_status']
    search_fields = ['user__email', 'status']
    readonly_fields = ['total_amount', 'payment_status', 'created_at', 'updated_at']
    inlines = [PrescriptionItemInline]
    actions = ['approve_prescription', 'reject_prescription']

    def approve_prescription(self, request, queryset):
        for prescription in queryset:
            if prescription.status == 'Pending':
                prescription.status = 'Approved'
                prescription.save()

                # Ensure prescription items are available
                if not prescription.items.exists():
                    self.message_user(request, "No items found for this prescription.", level='error')
                    return

                # Calculate total amount for approved prescription
                total_amount = sum(item.product.price * item.quantity for item in prescription.items.all())
                prescription.total_amount = total_amount
                prescription.save()

                # Create a PrescriptionOrder after approval
                PrescriptionOrder.objects.create(
                    prescription=prescription,
                    total_amount=total_amount,
                    payment_status='Pending'
                )
        self.message_user(request, "Selected prescriptions have been approved and orders created.")

    approve_prescription.short_description = "Approve selected prescriptions and create orders"

    def reject_prescription(self, request, queryset):
        queryset.update(status='Rejected')
        self.message_user(request, "Selected prescriptions have been rejected.")

    reject_prescription.short_description = "Reject selected prescriptions"


@admin.register(PrescriptionOrder)
class PrescriptionOrderAdmin(admin.ModelAdmin):
    list_display = ['prescription', 'total_amount', 'payment_status', 'payment_method']
    list_filter = ['payment_status', 'payment_method']
    search_fields = ['prescription__user__email']
    readonly_fields = ['total_amount', 'payment_status', 'created_at', 'updated_at']

    def has_add_permission(self, request):
        return False  # Prevent manual creation of orders from the admin panel
