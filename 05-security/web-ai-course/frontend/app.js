const output = document.querySelector('#result');
async function show(response) { output.textContent = `${response.status}\n${await response.text()}`; }
document.querySelector('#login').onclick = async () => show(await fetch("/login"));
document.querySelector('#mine').onclick = async () => show(await fetch("/orders?id=1"));
document.querySelector('#other').onclick = async () => show(await fetch("/orders?id=2"));
document.querySelector('#lazy').onclick = async () => { const module = await import('./lazy.js'); output.textContent = module.note; };
const text = decodeURIComponent(location.hash.slice(1));
const sink = document.querySelector('#sink');
if (new URLSearchParams(location.search).get('mode') === 'vulnerable') { sink.innerHTML = text; }
else { sink.textContent = text; }
// sourceMappingURL=app.js.map
