document.addEventListener("DOMContentLoaded", () => {
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
        const role = JSON.parse(atob(token.split(".")[1])).role;
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
});
