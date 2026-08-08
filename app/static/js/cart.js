/**
 * Fancy Store - Shopping Cart & Checkout Gateway Simulator JS
 */

document.addEventListener('DOMContentLoaded', () => {
    initCartQtyControls();
    initCouponForm();
});

/* ================= 1. AJAX Cart Quantity Controls ================= */
function initCartQtyControls() {
    document.body.addEventListener('click', (e) => {
        const btn = e.target.closest('.btn-cart-qty');
        if (!btn) return;
        
        const productId = btn.getAttribute('data-id');
        const variant = btn.getAttribute('data-variant') || null;
        const delta = parseInt(btn.getAttribute('data-delta')) || 0;
        
        const inputEl = document.querySelector(`.qty-input-item[data-id="${productId}"]`);
        if (!inputEl) return;
        
        let newQty = parseInt(inputEl.value) + delta;
        if (newQty < 1) newQty = 1;
        
        updateCartItemQty(productId, newQty, variant, inputEl);
    });
    
    document.body.addEventListener('change', (e) => {
        if (e.target.classList.contains('qty-input-item')) {
            const productId = e.target.getAttribute('data-id');
            const variant = e.target.getAttribute('data-variant') || null;
            let newQty = parseInt(e.target.value) || 1;
            if (newQty < 1) newQty = 1;
            updateCartItemQty(productId, newQty, variant, e.target);
        }
    });
}

function updateCartItemQty(productId, qty, variant, inputEl) {
    const csrfToken = getCsrfToken();
    
    fetch('/cart/update', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ product_id: productId, quantity: qty, variant: variant })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            inputEl.value = qty;
            updateCartSummaryDOM(data.summary);
            showToast("Cart quantity updated", "info");
        } else {
            showToast(data.message || "Failed to update quantity", "danger");
        }
    })
    .catch(err => {
        console.error("Cart update error:", err);
        showToast("Network error while updating cart", "danger");
    });
}

function updateCartSummaryDOM(summary) {
    if (!summary) return;
    
    const subtotalEl = document.getElementById('summary-subtotal');
    const shippingEl = document.getElementById('summary-shipping');
    const discountEl = document.getElementById('summary-discount');
    const taxEl = document.getElementById('summary-tax');
    const grandEl = document.getElementById('summary-grand');
    const badgeEl = document.getElementById('cart-badge');
    
    if (subtotalEl) subtotalEl.textContent = summary.subtotal;
    if (shippingEl) shippingEl.textContent = summary.shipping_charge;
    if (discountEl) discountEl.textContent = summary.discount_amount;
    if (taxEl) taxEl.textContent = summary.tax_amount;
    if (grandEl) grandEl.textContent = summary.grand_total;
    
    if (badgeEl) {
        badgeEl.textContent = summary.item_count;
        badgeEl.style.display = summary.item_count > 0 ? 'inline-block' : 'none';
    }
}

/* ================= 2. AJAX Coupon Form ================= */
function initCouponForm() {
    const form = document.getElementById('ajax-coupon-form');
    if (!form) return;
    
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        const input = document.getElementById('coupon-code-input');
        const code = input ? input.value.trim() : '';
        if (!code) {
            showToast("Please enter a coupon code", "warning");
            return;
        }
        
        const csrfToken = getCsrfToken();
        
        fetch('/cart/coupon/apply', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ coupon_code: code })
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                showToast(data.message, "success");
                setTimeout(() => window.location.reload(), 800);
            } else {
                showToast(data.message || "Invalid coupon code", "danger");
            }
        })
        .catch(err => {
            console.error("Coupon error:", err);
            showToast("Error applying coupon", "danger");
        });
    });
}

