document.addEventListener('DOMContentLoaded', function() {
    const productSelectors = document.querySelectorAll('select[name$="product"]');
    const quantitySelectors = document.querySelectorAll('input[name$="quantity"]');

    // Function to update total price when product or quantity changes
    function updateTotalPrice() {
        let totalPrice = 0;

        productSelectors.forEach((productSelector, index) => {
            const productId = productSelector.value;
            const quantityInput = quantitySelectors[index];
            const quantity = parseInt(quantityInput.value) || 0;

            // Fetch product details using Django API or Admin AJAX
            if (productId) {
                fetch(`/admin/products/product/${productId}/change/`)
                    .then(response => response.json())
                    .then(data => {
                        const price = data.price;
                        totalPrice += price * quantity;
                        document.querySelector('#id_total_amount').value = totalPrice.toFixed(2);  // Update total amount
                    });
            }
        });
    }

    // Add event listeners to product and quantity fields
    productSelectors.forEach((productSelector) => {
        productSelector.addEventListener('change', updateTotalPrice);
    });
    quantitySelectors.forEach((quantitySelector) => {
        quantitySelector.addEventListener('input', updateTotalPrice);
    });
});
