const root = document.documentElement;
const themeToggle = document.querySelector("[data-theme-toggle]");
const themeLabel = document.querySelector("[data-theme-label]");

function applyTheme(theme) {
  root.dataset.theme = theme;
  if (themeLabel) themeLabel.textContent = theme === "dark" ? "Light mode" : "Dark mode";
  localStorage.setItem("equi-track-theme", theme);
}

applyTheme(localStorage.getItem("equi-track-theme") || "dark");
themeToggle?.addEventListener("click", () => {
  applyTheme(root.dataset.theme === "dark" ? "light" : "dark");
});