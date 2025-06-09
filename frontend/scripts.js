document.addEventListener("DOMContentLoaded", () => {
  const menuToggle = document.getElementById("menuToggle");
  const dropdownMenu = document.getElementById("dropdownMenu");
  if (menuToggle && dropdownMenu) {
    menuToggle.onclick = () => dropdownMenu.classList.toggle("show");
    window.onclick = (e) => {
      if (!e.target.matches("#menuToggle") && !dropdownMenu.contains(e.target)) {
        dropdownMenu.classList.remove("show");
      }
    };
  }
});
