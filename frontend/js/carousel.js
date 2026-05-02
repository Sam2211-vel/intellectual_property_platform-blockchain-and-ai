document.addEventListener("DOMContentLoaded", () => {
  const slides = document.querySelectorAll(".carousel-img");
  let current = 0;

  if (slides.length === 0) return;

  setInterval(() => {
    slides[current].classList.add("hidden");
    current = (current + 1) % slides.length;
    slides[current].classList.remove("hidden");
  }, 5000); // change every 5 seconds
});
