document.querySelector('#inspect').onclick = async () => {
  const out = document.querySelector('#out');
  try {
    const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
    const url = new URL(tab.url);
    if (url.hostname !== '127.0.0.1' || url.port !== '8787') { out.textContent = '仅用于 http://127.0.0.1:8787 本地课程。'; return; }
    const results = await chrome.scripting.executeScript({target: {tabId: tab.id}, func: () => Array.from(document.scripts, script => script.src).filter(Boolean)});
    out.textContent = JSON.stringify(results[0].result, null, 2);
  } catch (error) { out.textContent = String(error); }
};
