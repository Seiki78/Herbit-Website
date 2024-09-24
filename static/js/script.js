document.addEventListener('DOMContentLoaded', function() {
	// เอา 'hidden' ออก เพื่อให้ alert แสดง
	var alerts = document.querySelectorAll('.alert');
	alerts.forEach(function(alert) {
		alert.classList.remove('hidden');
	});

	// ตั้งเวลาซ่อนหลังแสดง
	setTimeout(function() {
		alerts.forEach(function(alert) {
			alert.classList.add('hidden');
		});
	}, 3000); // ปิด flash messages หลัง 3 วินาที
});

//sidebar
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

// TOGGLE SIDEBAR
const menuBar = document.querySelector('#content nav .bx.bx-menu');
const sidebar = document.getElementById('sidebar');

if (menuBar && sidebar) {  // ตรวจสอบว่า element มีอยู่จริงก่อนเรียกใช้งาน
    menuBar.addEventListener('click', function () {
        sidebar.classList.toggle('hide');
    });
}


//ค้นหา
const searchButton = document.querySelector('#content nav form .form-input button');
const searchButtonIcon = document.querySelector('#content nav form .form-input button .bx');
const searchForm = document.querySelector('#content nav form');

searchButton.addEventListener('click', function (e) {
	if(window.innerWidth < 576) {
		e.preventDefault();
		searchForm.classList.toggle('show');
		if(searchForm.classList.contains('show')) {
			searchButtonIcon.classList.replace('bx-search', 'bx-x');
		} else {
			searchButtonIcon.classList.replace('bx-x', 'bx-search');
		}
	}
})

if(window.innerWidth < 768) {
	sidebar.classList.add('hide');
} else if(window.innerWidth > 576) {
	searchButtonIcon.classList.replace('bx-x', 'bx-search');
	searchForm.classList.remove('show');
}

window.addEventListener('resize', function () {
	if(this.innerWidth > 576) {
		searchButtonIcon.classList.replace('bx-x', 'bx-search');
		searchForm.classList.remove('show');
	}
})

//โหมดสว่าง-มืด
const switchMode = document.getElementById('switch-mode');
switchMode.addEventListener('change', function () {
	if(this.checked) {
		document.body.classList.add('dark');
	} else {
		document.body.classList.remove('dark');
	}
})
