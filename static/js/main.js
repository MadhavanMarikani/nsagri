// Main Application JS

function showLogoutModal() {
    document.getElementById('logoutModal').style.display = 'flex';
}

function hideLogoutModal() {
    document.getElementById('logoutModal').style.display = 'none';
}

function openAddCropModal() {
    const modal = document.getElementById('addCropModal');
    if (modal) modal.style.display = 'flex';
}

function closeAddCropModal() {
    const modal = document.getElementById('addCropModal');
    if (modal) modal.style.display = 'none';
}

function openAddTransModal() {
    const modal = document.getElementById('addTransModal');
    if (modal) modal.style.display = 'flex';
}

function closeAddTransModal() {
    const modal = document.getElementById('addTransModal');
    if (modal) modal.style.display = 'none';
}

// Close modals when clicking outside
window.onclick = function(event) {
    const logoutModal = document.getElementById('logoutModal');
    const cropModal = document.getElementById('addCropModal');
    const transModal = document.getElementById('addTransModal');
    if (event.target === logoutModal) hideLogoutModal();
    if (event.target === cropModal) closeAddCropModal();
    if (event.target === transModal) closeAddTransModal();
};
