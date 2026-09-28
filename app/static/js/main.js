/**
 * Fancy Store - Master Frontend JavaScript Controller
 * Handles Theme Toggling, Live Search AJAX Auto-Suggestions, and Wishlist Toggles
 */

document.addEventListener('DOMContentLoaded', () => {
    initThemeSwitcher();
    initLiveSearch();
    initWishlistButtons();
    initFlashToasts();
});

/* ================= 1. Theme Switcher ================= */
function initThemeSwitcher() {
    const themeBtn = document.getElementById('theme-toggle-btn');
    const themeIcon = document.getElementById('theme-toggle-icon');
    if (!themeBtn) return;

    const savedTheme = localStorage.getItem('fancy_theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme, themeIcon);

    themeBtn.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('fancy_theme', newTheme);
        updateThemeIcon(newTheme, themeIcon);
        showToast(`Switched to ${newTheme.toUpperCase()} Mode`, 'info');
    });
}

function updateThemeIcon(theme, iconEl) {
    if (!iconEl) return;
    if (theme === 'dark') {
        iconEl.className = 'fas fa-sun';
    } else {
        iconEl.className = 'fas fa-moon';
    }
}

/* ================= 2. Live Search Auto-Suggestions ================= */
function initLiveSearch() {
    const searchInput = document.getElementById('live-search-input');
    const suggestionsBox = document.getElementById('search-suggestions-box');
    if (!searchInput || !suggestionsBox) return;

    let debounceTimer;

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.trim();
        clearTimeout(debounceTimer);

        if (query.length < 2) {
            suggestionsBox.style.display = 'none';
            suggestionsBox.innerHTML = '';
            return;
        }

        debounceTimer = setTimeout(() => {
            fetch(`/api/search/suggestions?q=${encodeURIComponent(query)}`, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'success' && data.suggestions.length > 0) {
                        renderSuggestions(data.suggestions, suggestionsBox);
                    } else {
                        suggestionsBox.innerHTML = `<div class="p-3 text-muted text-center font-sm">No matching products found for "${query}"</div>`;
                        suggestionsBox.style.display = 'block';
                    }
                })
                .catch(err => {
                    console.error("Live search error:", err);
                });
        }, 300);
    });

    // Close suggestions on outside click
    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !suggestionsBox.contains(e.target)) {
            suggestionsBox.style.display = 'none';
        }
    });
}

function renderSuggestions(items, boxEl) {
    let html = '';
    items.forEach(item => {
        html += `
            <a href="${item.url}" class="suggestion-item">
                <img src="${item.thumbnail}" alt="${item.name}" class="suggestion-thumb" onerror="this.src='https://placehold.co/100x100?text=No+Img'">
                <div>
                    <div class="fw-bold font-sm text-primary">${item.brand}</div>
                    <div class="font-sm text-truncate" style="max-width: 350px;">${item.name}</div>
                    <div class="fw-bold text-success font-sm">${item.price_formatted}</div>
                </div>
            </a>
        `;
    });
    boxEl.innerHTML = html;
    boxEl.style.display = 'block';
}

/* ================= 3. Wishlist AJAX Toggles ================= */
function initWishlistButtons() {
    document.body.addEventListener('click', (e) => {
        const btn = e.target.closest('.btn-wishlist-toggle');
        if (!btn) return;
        e.preventDefault();

        const productId = btn.getAttribute('data-product-id');
        if (!productId) return;

        const csrfToken = getCsrfToken();

        fetch('/api/wishlist/toggle', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ product_id: productId })
        })
            .then(res => {
                if (res.status === 401 || res.status === 403) {
                    showToast("Please log in to save items to your wishlist.", "warning");
                    setTimeout(() => window.location.href = '/auth/login', 1500);
                    return null;
                }
                return res.json();
            })
            .then(data => {
                if (!data) return;
                if (data.status === 'success') {
                    btn.classList.toggle('active', data.in_wishlist);
                    const icon = btn.querySelector('i');
                    if (icon) {
                        icon.className = data.in_wishlist ? 'fas fa-heart text-danger' : 'far fa-heart';
                    }
                    updateBadgeCount('wishlist-badge', data.wishlist_count);
                    showToast(data.message, 'success');
                } else {
                    showToast(data.message || "Error updating wishlist", 'danger');
                }
            })
            .catch(err => {
                console.error("Wishlist toggle error:", err);
                showToast("Network error. Please try again.", 'danger');
            });
    });
}

function updateBadgeCount(badgeId, count) {
    const badgeEl = document.getElementById(badgeId);
    if (!badgeEl) return;
    badgeEl.textContent = count;
    badgeEl.style.display = count > 0 ? 'inline-block' : 'none';
}

function getCsrfToken() {
    const metaToken = document.querySelector('meta[name="csrf-token"]');
    if (metaToken) return metaToken.getAttribute('content');
    const inputToken = document.querySelector('input[name="csrf_token"]');
    if (inputToken) return inputToken.value;
    return '';
}

/* ================= 4. Toast Notifications ================= */
function showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }

    const toastId = 'toast-' + Math.random().toString(36).substr(2, 9);
    const borderColor = type === 'success' ? '#10b981' : (type === 'danger' ? '#ef4444' : (type === 'warning' ? '#f59e0b' : '#2563eb'));

    const toastHtml = `
        <div id="${toastId}" class="toast-fancy" style="border-left-color: ${borderColor};">
            <div class="d-flex align-items-center gap-2">
                <i class="fas ${type === 'success' ? 'fa-check-circle text-success' : (type === 'danger' ? 'fa-exclamation-circle text-danger' : 'fa-info-circle text-primary')}"></i>
                <span class="font-sm fw-medium">${message}</span>
            </div>
            <button type="button" class="btn-close ms-2" onclick="document.getElementById('${toastId}').remove()"></button>
        </div>
    `;

    container.insertAdjacentHTML('beforeend', toastHtml);

    setTimeout(() => {
        const el = document.getElementById(toastId);
        if (el) el.remove();
    }, 4000);
}

function initFlashToasts() {
    const flashes = document.querySelectorAll('.server-flash-msg');
    flashes.forEach(el => {
        const msg = el.getAttribute('data-msg');
        const type = el.getAttribute('data-type') || 'info';
        if (msg) showToast(msg, type);
    });
}
