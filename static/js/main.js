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

// Mobile Sidebar Toggle
function toggleSidebar(event) {
    event.stopPropagation();
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        sidebar.classList.toggle('active');
    }
}

// Close sidebar on click outside
document.addEventListener('click', function(event) {
    const sidebar = document.querySelector('.sidebar');
    const toggleBtn = document.querySelector('.mobile-toggle');
    if (sidebar && sidebar.classList.contains('active')) {
        if (!sidebar.contains(event.target) && (!toggleBtn || !toggleBtn.contains(event.target))) {
            sidebar.classList.remove('active');
        }
    }
});
