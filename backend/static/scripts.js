function initMenu() {
  const menuToggle = document.getElementById("menuToggle");
  const dropdownMenu = document.getElementById("dropdownMenu");
  if (menuToggle && dropdownMenu) {
    menuToggle.addEventListener("click", () => {
      dropdownMenu.classList.toggle("show");
    });
    window.addEventListener("click", (e) => {
      if (!menuToggle.contains(e.target) && !dropdownMenu.contains(e.target)) {
        dropdownMenu.classList.remove("show");
      }
    });
  }
  if (dropdownMenu) {
    const token = localStorage.getItem("pyToken");
    if (token) {
      try {
        const b64 = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
        const padded = b64 + "=".repeat((4 - b64.length % 4) % 4);
        const role = JSON.parse(atob(padded)).role;
        if (role !== "teacher" && role !== "admin") {
          dropdownMenu.querySelectorAll(".teacher-link").forEach(el => {
            el.style.display = "none";
          });
        }
      } catch (e) {
        /* ignore invalid token */
      }
    }
  }
}

if (document.readyState !== "loading") {
  initMenu();
} else {
  document.addEventListener("DOMContentLoaded", initMenu);
}
