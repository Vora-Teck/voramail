// DOM Elements
var dashboardSidebar = document.getElementById("dashboardSidebar");
var userMenu = document.getElementById("userMenu");
var userMenuTrigger = document.getElementById("user-menu-trigger");
var userMenuDropdown = document.querySelector("#user-menu-dropdown");
var themeToggle = document.getElementById("theme-toggle");
var dashboardViews = document.querySelectorAll(".dashboard-view");
var dashboardTitle = document.getElementById("dashboardTitle");
var dashboardSidebarOverlay = document.getElementById("dashboardSidebarOverlay");
var searchContainer = document.getElementById("searchContainer");
var searchInput = document.getElementById("searchInput");
var searchClose = document.getElementById("searchClose");
var mobileSearchBtn = document.getElementById("mobileSearchBtn");

// State
var sidebarCollapsed = false;

// ===================================
// INITIALIZATION
// ===================================

initTheme();
initThemeToggle();
initSidebar();
initUserMenu();
initSearch();

// ===================================
// SIDEBAR FUNCTIONALITY
// ===================================

function initSidebar() {
  // Load saved sidebar state
  sidebarCollapsed = localStorage.getItem("dashboard-sidebar-collapsed") === "true";
  dashboardSidebar.classList.toggle("collapsed", sidebarCollapsed);

  // Sidebar toggle functionality
  document.querySelectorAll(".dashboard-sidebar-toggle").forEach((toggle) => {
    toggle.addEventListener("click", toggleSidebar);
  });

  // Sidebar overlay functionality
  dashboardSidebarOverlay?.addEventListener("click", closeSidebar);
}

function toggleSidebar() {
  sidebarCollapsed = !sidebarCollapsed;
  const isMobile = window.innerWidth <= 1024;

  if (isMobile) {
    // Mobile behavior - toggle sidebar and overlay together
    const isOpen = dashboardSidebar.classList.contains("collapsed");
    dashboardSidebar.classList.toggle("collapsed", !isOpen);
    dashboardSidebarOverlay?.classList.toggle("active", !isOpen);
  } else {
    // Desktop behavior
    dashboardSidebar.classList.toggle("collapsed", sidebarCollapsed);
  }

  localStorage.setItem("dashboard-sidebar-collapsed", sidebarCollapsed.toString());
}

function closeSidebar() {
  if (window.innerWidth <= 1024) {
    dashboardSidebar.classList.remove("collapsed");
    dashboardSidebarOverlay?.classList.remove("active");
  }
}

// ===================================
// USER MENU FUNCTIONALITY
// ===================================

function initUserMenu() {
  if (!userMenuTrigger || !userMenu) return;

  userMenuTrigger.addEventListener("click", (e) => {
    e.stopPropagation();
    userMenu.classList.toggle("active");
  });

  // Close menu when clicking outside or pressing escape
  document.addEventListener("click", (e) => {
    if (!userMenu.contains(e.target)) {
      userMenu.classList.remove("active");
    }
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && userMenu.classList.contains("active")) {
      userMenu.classList.remove("active");
    }
  });
}

// ===================================
// THEME FUNCTIONALITY
// ===================================

function initTheme() {
  // Load saved theme
  const savedTheme = localStorage.getItem("dashboard-theme") || "dark";
  document.documentElement.setAttribute("data-theme", savedTheme);

  // Update theme toggle UI
  updateThemeToggleUI(savedTheme);
}

function initThemeToggle() {
  if (!themeToggle) return;

  themeToggle.querySelectorAll(".theme-option").forEach((option) => {
    option.addEventListener("click", (e) => {
      e.stopPropagation();
      setTheme(option.getAttribute("data-theme"));
    });
  });
}

function setTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem("dashboard-theme", theme);
  updateThemeToggleUI(theme);
}

function updateThemeToggleUI(theme) {
  if (!themeToggle) return;

  themeToggle.querySelectorAll(".theme-option").forEach((option) => {
    option.classList.toggle("active", option.getAttribute("data-theme") === theme);
  });
}

// ===================================
// SEARCH FUNCTIONALITY
// ===================================

function initSearch() {
  mobileSearchBtn?.addEventListener("click", () => {
    searchContainer.classList.add("mobile-active");
    searchInput.focus();
  });

  searchClose?.addEventListener("click", () => {
    searchContainer.classList.remove("mobile-active");
    searchInput.value = "";
  });
}

// ===================================
// CHART INITIALIZATION
// ===================================

function initCharts() {
  initProgressChart();
  initCategoryChart();
}

var linkItems = document.querySelectorAll(".link-item");

linkItems.forEach((linkItem, index) => {
    linkItem.addEventListener("click", (e) => {
      e.preventDefault()
        document.querySelector(".link-item.active").classList.remove("active");
        linkItem.classList.add("active");
        let attr = linkItem.getAttribute('href')
        console.log(attr)

        const indicator = document.querySelector(".indicator");

        indicator.style.left = `${index * 95 + 48}px`;
    })
})


