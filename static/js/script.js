document.addEventListener('DOMContentLoaded', function() {
    // Flash Messages
    var alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        alert.classList.remove('hidden');
    });
    setTimeout(function() {
        alerts.forEach(function(alert) {
            alert.classList.add('hidden');
        });
    }, 3000); 

    // Side menu
    const allSideMenu = document.querySelectorAll('#sidebar .side-menu.top li a');
    if (allSideMenu.length > 0) {
        allSideMenu.forEach(item => {
            const li = item.parentElement;
            item.addEventListener('click', function () {
                allSideMenu.forEach(i => {
                    i.parentElement.classList.remove('active');
                });
                li.classList.add('active');
            });
        });
    }

    // Toggle sidebar
    const menuBar = document.querySelector('#content nav .bx.bx-menu');
    const sidebar = document.getElementById('sidebar');
    if (menuBar && sidebar) {
        menuBar.addEventListener('click', function () {
            sidebar.classList.toggle('hide');
        });
    }
    
});