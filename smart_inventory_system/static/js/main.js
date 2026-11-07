/**
 * Smart Inventory & Logistics Management System - Core Frontend JS
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Initialize Bootstrap Tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // 2. Auto-dismiss alerts after 5 seconds
    setTimeout(function () {
        const alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(function (alert) {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        });
    }, 5500);

    // 3. Mobile Sidebar Toggle
    const sidebarToggleBtn = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    if (sidebarToggleBtn && sidebar) {
        sidebarToggleBtn.addEventListener('click', function () {
            sidebar.classList.toggle('d-none');
            sidebar.classList.toggle('d-flex');
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
});
