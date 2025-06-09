// Простые заглушки для демонстрации работы интерфейса
const SAMPLE_TASKS = [
  // "assignee" uses numeric identifiers to mirror real API data
  {id: 1, name: 'Обновление календаря', effort: 4, deadline: '2025-06-20', assignee: 2, status: 'в процессе', progress: 40, priority: 'A'}, // alice
  {id: 2, name: 'Написать отчёт', effort: 2, deadline: '2025-06-18', assignee: 3, status: 'выполнено', progress: 100, priority: 'B'}, // bob
  {id: 3, name: 'Обсудить требования', effort: 1, deadline: '2025-06-22', assignee: null, status: 'открыта', progress: 0, priority: 'C'}
];

const SAMPLE_RISKS = [
  {date: '2025-06-15', task: 'Обновление календаря', message: 'Просрочено на 1 день'},
  {date: '2025-06-14', task: 'Написать отчёт', message: 'Отчёт ещё не загружен'}
];

const SAMPLE_SLOTS = [
  {day: 1, hour: 10},
  {day: 1, hour: 11},
  {day: 2, hour: 14},
  {day: 4, hour: 9}
];

