(() => {
  const root = document.documentElement;
  const savedTheme = localStorage.getItem("reyminder-theme");
  if (savedTheme === "dark" || savedTheme === "light") root.dataset.theme = savedTheme;

  function updateThemeButtons() {
    const dark = root.dataset.theme === "dark";
    document.querySelectorAll("[data-theme-icon]").forEach(el => el.textContent = dark ? "☀" : "☾");
    document.querySelectorAll("[data-theme-label]").forEach(el => el.textContent = dark ? "Light mode" : "Dark mode");
    document.querySelectorAll("[data-theme-toggle]").forEach(el => el.setAttribute("aria-label", dark ? "Switch to light mode" : "Switch to dark mode"));
  }
  document.querySelectorAll("[data-theme-toggle]").forEach(button => {
    button.addEventListener("click", () => {
      root.dataset.theme = root.dataset.theme === "dark" ? "light" : "dark";
      localStorage.setItem("reyminder-theme", root.dataset.theme);
      updateThemeButtons();
    });
  });
  updateThemeButtons();

  document.querySelectorAll("[data-password-toggle]").forEach(button => {
    button.addEventListener("click", () => {
      const input = document.getElementById(button.dataset.passwordToggle);
      if (!input) return;
      const showing = input.type === "password";
      input.type = showing ? "text" : "password";
      button.textContent = showing ? "◎" : "◉";
      button.setAttribute("aria-label", showing ? "Hide password" : "Show password");
    });
  });

  // Calendar on the dashboard. Reminder dates are rendered from the backend.
  const daysEl = document.getElementById("calendar-days");
  const monthLabel = document.getElementById("calendar-month");
  if (!daysEl || !monthLabel) return;

  let shown = new Date();
  shown = new Date(shown.getFullYear(), shown.getMonth(), 1);
  let selectedDate = new Date();
  const dataEl = document.getElementById("reminder-data");
  let reminders = [];
  try { reminders = JSON.parse(dataEl?.textContent || "[]"); } catch (_) {}

  const dateKey = date => `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,"0")}-${String(date.getDate()).padStart(2,"0")}`;

  function showSelectedDay() {
    const key = dateKey(selectedDate);
    const label = document.getElementById("selected-date-label");
    const list = document.getElementById("selected-date-items");
    label.textContent = selectedDate.toLocaleDateString(undefined, {weekday:"short", month:"long", day:"numeric", year:"numeric"});
    const matches = reminders.filter(item => item.due_at?.slice(0,10) === key);
    if (!matches.length) {
      list.textContent = "No reminders scheduled for this day.";
      return;
    }
    list.innerHTML = "";
    matches.forEach(item => {
      const line = document.createElement("div");
      line.className = "calendar-reminder-line";
      const dot = document.createElement("span");
      dot.className = "legend-dot legend-reminder";
      const title = document.createElement("span");
      title.textContent = item.title + (item.completed ? " · Completed" : "");
      line.append(dot, title);
      list.appendChild(line);
    });
  }

  function renderCalendar() {
    monthLabel.textContent = shown.toLocaleDateString(undefined, {month:"long", year:"numeric"});
    daysEl.innerHTML = "";
    const firstWeekday = new Date(shown.getFullYear(), shown.getMonth(), 1).getDay();
    const daysInMonth = new Date(shown.getFullYear(), shown.getMonth()+1, 0).getDate();
    const todayKey = dateKey(new Date());
    for (let i=0; i<firstWeekday; i++) {
      const blank = document.createElement("span");
      blank.className = "calendar-blank";
      daysEl.appendChild(blank);
    }
    for (let day=1; day<=daysInMonth; day++) {
      const date = new Date(shown.getFullYear(), shown.getMonth(), day);
      const key = dateKey(date);
      const button = document.createElement("button");
      button.type = "button";
      button.className = "calendar-day";
      button.textContent = day;
      if (key === todayKey) button.classList.add("is-today");
      if (key === dateKey(selectedDate)) button.classList.add("is-selected");
      if (reminders.some(item => item.due_at?.slice(0,10) === key)) button.classList.add("has-reminder");
      button.setAttribute("aria-label", date.toLocaleDateString());
      button.addEventListener("click", () => {
        selectedDate = date;
        renderCalendar();
        showSelectedDay();
      });
      daysEl.appendChild(button);
    }
  }
  document.getElementById("prev-month")?.addEventListener("click", () => { shown = new Date(shown.getFullYear(), shown.getMonth()-1, 1); renderCalendar(); });
  document.getElementById("next-month")?.addEventListener("click", () => { shown = new Date(shown.getFullYear(), shown.getMonth()+1, 1); renderCalendar(); });
  renderCalendar();
  showSelectedDay();

  // Set a useful default for the new reminder field: one hour from now.
  const dueInput = document.getElementById("due_at");
  if (dueInput && !dueInput.value) {
    const later = new Date(Date.now() + 60*60*1000);
    later.setMinutes(Math.ceil(later.getMinutes()/5)*5, 0, 0);
    const local = new Date(later.getTime() - later.getTimezoneOffset()*60000);
    dueInput.value = local.toISOString().slice(0,16);
  }
})();
