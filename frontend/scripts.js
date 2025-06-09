document.addEventListener("DOMContentLoaded", () => {
  /* === Burger‑menu toggle (works on every page) === */
  const menuToggle = document.getElementById("menuToggle");
  const dropdownMenu = document.getElementById("dropdownMenu");

  if (menuToggle && dropdownMenu) {
    menuToggle.onclick = () => dropdownMenu.classList.toggle("show");
    window.onclick = (e) => {
      if (
        !e.target.matches("#menuToggle") &&
        !dropdownMenu.contains(e.target)
      ) {
        dropdownMenu.classList.remove("show");
      }
    };
  }

  /* === Radio buttons visual selection === */
  document.querySelectorAll(".input-field").forEach((field) => {
    field.addEventListener("click", () => {
      const question = field.closest(".question");
      if (!question) return;

      // 1. снять выделение со всех
      question
        .querySelectorAll(".input-field")
        .forEach((f) => f.classList.remove("selected"));

      // 2. выделить текущий
      field.classList.add("selected");

      // 👉 3. отметить radio как выбранный
      const input = field.querySelector('input[type="radio"]');
      if (input) input.checked = true; // <-- ЭТО ДОБАВЛЯЕМ
    });
  });

  /* === Quiz checking === */
  const checkBtn = document.getElementById("checkAnswersBtn");
  if (checkBtn) {
    const isFinalTest = document.body.dataset.final === "true";

    checkBtn.addEventListener("click", () => {
      let correctCount = 0;
      document.querySelectorAll(".question").forEach((q) => {
        const correct = q.dataset.correctAnswer;
        q.querySelectorAll(".input-field").forEach((f) => {
          const input = f.querySelector('input[type="radio"]');
          f.classList.remove("selected", "correct", "incorrect");

          if (input.checked) {
            /* считаем балл всегда */
            if (input.value === correct) correctCount += 1;

            /* подсвечиваем ТОЛЬКО если это не контрольная */
            if (!isFinalTest) {
              f.classList.add(
                input.value === correct ? "correct" : "incorrect"
              );
            }
          }
        });
      });

      /* выводим результат (работает везде) */
      const res = document.getElementById("result");
      if (res) res.textContent = `Ваш результат: ${correctCount}`;
    });
  }
});

/* === отправка результата в API === */
function saveResultApi(slug,score,total){
  const t=localStorage.getItem('pyToken'); if(!t) return;
  fetch('/api/test-result',{
    method:'POST',
    headers:{'Content-Type':'application/json','Authorization':`Bearer ${t}`},
    body:JSON.stringify({slug,score,total})
  });
}
