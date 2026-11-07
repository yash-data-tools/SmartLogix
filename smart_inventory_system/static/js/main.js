/**
 * Smart Inventory & Logistics Management System - Core Frontend JS
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Initialize Bootstrap Tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // 2. Modern Floating Toast Lifecycle Handler
    const toasts = document.querySelectorAll('.toast-modern');
    toasts.forEach(function (toast) {
        let dismissTimer = setTimeout(function () {
            dismissToast(toast);
        }, 4500);

        // Pause timer on hover, resume on mouse leave
        toast.addEventListener('mouseenter', function () {
            clearTimeout(dismissTimer);
            const progress = toast.querySelector('.toast-progress');
            if (progress) progress.style.animationPlayState = 'paused';
        });

        toast.addEventListener('mouseleave', function () {
            const progress = toast.querySelector('.toast-progress');
            if (progress) progress.style.animationPlayState = 'running';
            dismissTimer = setTimeout(function () {
                dismissToast(toast);
            }, 2500);
        });
    });

    function dismissToast(toast) {
        if (!toast || toast.classList.contains('toast-closing')) return;
        toast.classList.add('toast-closing');
        setTimeout(function () {
            if (toast.parentNode) toast.parentNode.removeChild(toast);
        }, 320);
    }

    // 3. Theme Toggle (Light / Dark Mode)
    const themeToggleBtn = document.getElementById('themeToggle');
    function updateThemeIcon(theme) {
        if (!themeToggleBtn) return;
        const icon = themeToggleBtn.querySelector('i');
        if (!icon) return;
        if (theme === 'dark') {
            icon.className = 'fa-solid fa-sun';
            themeToggleBtn.setAttribute('title', 'Switch to Light Mode');
            themeToggleBtn.style.color = '#fbbf24';
        } else {
            icon.className = 'fa-solid fa-moon';
            themeToggleBtn.setAttribute('title', 'Switch to Dark Mode');
            themeToggleBtn.style.color = '';
        }
    }

    const currentTheme = document.documentElement.getAttribute('data-bs-theme') || 'light';
    updateThemeIcon(currentTheme);

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', function () {
            const activeTheme = document.documentElement.getAttribute('data-bs-theme') === 'dark' ? 'dark' : 'light';
            const newTheme = activeTheme === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-bs-theme', newTheme);
            document.documentElement.setAttribute('data-theme', newTheme);
            try {
                localStorage.setItem('smartlogix-theme', newTheme);
            } catch (e) {}
            updateThemeIcon(newTheme);
            window.dispatchEvent(new CustomEvent('smartlogix-theme-changed', { detail: { theme: newTheme } }));
        });
    }

    // 4. Responsive Mobile Sidebar Drawer Toggle & Overlay
    const sidebarToggleBtn = document.getElementById('sidebarToggle');
    const sidebarCloseBtn = document.getElementById('sidebarClose');
    const sidebarBackdrop = document.getElementById('sidebarBackdrop');
    const sidebar = document.getElementById('sidebar');

    function openMobileSidebar() {
        if (sidebar) sidebar.classList.add('show');
        if (sidebarBackdrop) sidebarBackdrop.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeMobileSidebar() {
        if (sidebar) sidebar.classList.remove('show');
        if (sidebarBackdrop) sidebarBackdrop.classList.remove('active');
        document.body.style.overflow = '';
    }

    if (sidebarToggleBtn) {
        sidebarToggleBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            if (sidebar && sidebar.classList.contains('show')) {
                closeMobileSidebar();
            } else {
                openMobileSidebar();
            }
        });
    }

    if (sidebarCloseBtn) {
        sidebarCloseBtn.addEventListener('click', closeMobileSidebar);
    }

    if (sidebarBackdrop) {
        sidebarBackdrop.addEventListener('click', closeMobileSidebar);
    }

    // Auto-close mobile drawer when navigation links are clicked
    if (sidebar) {
        const navLinks = sidebar.querySelectorAll('.nav-link');
        navLinks.forEach(function (link) {
            link.addEventListener('click', function () {
                if (window.innerWidth < 992) {
                    closeMobileSidebar();
                }
            });
        });
    }

    // 4. Generic Delete Confirmation Modal Handler
    const deleteModalEl = document.getElementById('deleteConfirmModal');
    if (deleteModalEl) {
        deleteModalEl.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            const actionUrl = button.getAttribute('data-action-url');
            const itemName = button.getAttribute('data-item-name') || 'this item';
            
            const form = deleteModalEl.querySelector('#deleteConfirmForm');
            const namePlaceholder = deleteModalEl.querySelector('#deleteItemName');
            
            if (form) form.action = actionUrl;
            if (namePlaceholder) namePlaceholder.textContent = itemName;
        });
    }

    // 5. Quick Location Reassignment Modal Handler
    const relocateModalEl = document.getElementById('relocateModal');
    if (relocateModalEl) {
        relocateModalEl.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            const productId = button.getAttribute('data-product-id');
            const productName = button.getAttribute('data-product-name');
            const currentLocationId = button.getAttribute('data-current-location-id');
            
            const prodIdInput = relocateModalEl.querySelector('#relocateProductId');
            const prodNameSpan = relocateModalEl.querySelector('#relocateProductName');
            const locationSelect = relocateModalEl.querySelector('#relocateLocationSelect');
            
            if (prodIdInput) prodIdInput.value = productId;
            if (prodNameSpan) prodNameSpan.textContent = productName;
            if (locationSelect && currentLocationId) locationSelect.value = currentLocationId;
        });
    }

    // 6. Quick Jump Spotlight Command Palette (Ctrl + K)
    const spotlightModalEl = document.getElementById('spotlightModal');
    const spotlightInput = document.getElementById('spotlightInput');
    const spotlightResults = document.getElementById('spotlightResults');

    if (spotlightModalEl && spotlightInput) {
        // Global Keyboard Shortcut: Ctrl + K or Cmd + K
        document.addEventListener('keydown', function (e) {
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
                e.preventDefault();
                const modal = bootstrap.Modal.getOrCreateInstance(spotlightModalEl);
                modal.show();
            }
        });

        // Autofocus input when modal opens
        spotlightModalEl.addEventListener('shown.bs.modal', function () {
            spotlightInput.value = '';
            filterSpotlightItems('');
            spotlightInput.focus();
        });

        // Filter items on input
        spotlightInput.addEventListener('input', function () {
            filterSpotlightItems(spotlightInput.value.trim().toLowerCase());
        });

        function filterSpotlightItems(query) {
            if (!spotlightResults) return;
            const items = spotlightResults.querySelectorAll('.spotlight-item');
            const categories = spotlightResults.querySelectorAll('.spotlight-category-title');
            
            let visibleCount = 0;
            items.forEach(function (item) {
                const title = (item.querySelector('.spotlight-item-title')?.textContent || '').toLowerCase();
                const desc = (item.querySelector('.spotlight-item-desc')?.textContent || '').toLowerCase();
                if (!query || title.includes(query) || desc.includes(query)) {
                    item.style.display = 'flex';
                    visibleCount++;
                } else {
                    item.style.display = 'none';
                }
            });

            // Toggle category titles
            categories.forEach(function (cat) {
                cat.style.display = query ? 'none' : 'block';
            });
        }
    }
});
