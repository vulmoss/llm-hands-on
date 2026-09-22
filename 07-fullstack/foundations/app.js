const key = "fullstack-foundations-tasks";
const list = document.querySelector("#tasks");
const message = document.querySelector("#message");
let tasks = [];
try {
  const stored = JSON.parse(localStorage.getItem(key) || "[]");
  if (!Array.isArray(stored) || stored.some((task) => !task || typeof task.id !== "string" || typeof task.title !== "string" || typeof task.done !== "boolean")) throw new Error("Invalid saved data");
  tasks = stored;
} catch { message.textContent = "暂时无法读取保存的任务。当前可以继续练习。"; }
function render() {
  list.replaceChildren();
  for (const task of tasks) {
    const item = document.createElement("li");
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox"; checkbox.id = task.id; checkbox.checked = task.done;
    const label = document.createElement("label"); label.htmlFor = task.id; label.textContent = task.title;
    checkbox.addEventListener("change", () => { task.done = checkbox.checked; save(); });
    const remove = document.createElement("button"); remove.textContent = "删除";
    remove.setAttribute("aria-label", `删除 ${task.title}`);
    remove.addEventListener("click", () => { tasks = tasks.filter((item) => item.id !== task.id); save(); });
    item.append(checkbox, label, remove); list.append(item);
  }
  document.querySelector("#summary").textContent = `已完成 ${tasks.filter((task) => task.done).length} / ${tasks.length} 项`;
}
function save() {
  try { localStorage.setItem(key, JSON.stringify(tasks)); message.textContent = "已保存到当前浏览器"; }
  catch { message.textContent = "浏览器存储不可用，刷新后此次更改可能丢失。"; }
  render();
}
document.querySelector("#task-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const input = document.querySelector("#title");
  const title = input.value.trim();
  if (!title) { message.textContent = "请输入任务标题"; return; }
  tasks.push({ id: crypto.randomUUID(), title, done: false });
  input.value = ""; save(); input.focus();
});
render();
