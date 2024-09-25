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
    
    // Search form
    const searchButton = document.querySelector('#content nav form .form-input button');
    const searchButtonIcon = document.querySelector('#content nav form .form-input button .bx');
    const searchForm = document.querySelector('#content nav form');
    if (searchButton && searchForm && searchButtonIcon) {
        searchButton.addEventListener('click', function (e) {
            if (window.innerWidth < 576) {
                e.preventDefault();
                searchForm.classList.toggle('show');
                if (searchForm.classList.contains('show')) {
                    searchButtonIcon.classList.replace('bx-search', 'bx-x');
                } else {
                    searchButtonIcon.classList.replace('bx-x', 'bx-search');
                }
            }
        });
    }

    // Resize event for sidebar
    window.addEventListener('resize', function () {
        if (window.innerWidth > 576) {
            searchButtonIcon.classList.replace('bx-x', 'bx-search');
            searchForm.classList.remove('show');
        }
    });
});
