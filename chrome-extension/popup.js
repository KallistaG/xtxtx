const verseText = document.querySelector('#verseText');
const reference = document.querySelector('#reference');
const status = document.querySelector('#status');
let verse;

async function chooseVerse() {
  const verses = await (await fetch(chrome.runtime.getURL('verses.json'))).json();
  verse = verses[Math.floor(Math.random() * verses.length)];
  verseText.textContent = `“${verse.text}”`;
  reference.textContent = `${verse.reference} · KJV`;
  status.textContent = 'Ready to create a verse image in Flow.';
}

document.querySelector('#another').addEventListener('click', chooseVerse);
document.querySelector('#send').addEventListener('click', async () => {
  if (!verse) return;
  const prompt = `Create a square 1:1 inspirational Bible verse poster. Use a peaceful sunrise landscape, gentle natural light, elegant minimal composition, warm cream and muted gold. Include this exact text clearly and legibly, with no extra text or watermark:\n“${verse.text}”\n— ${verse.reference} (KJV)`;
  await chrome.storage.local.set({ pendingFlowPrompt: prompt, pendingFlowCreatedAt: Date.now() });
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab?.url?.startsWith('https://labs.google/fx/tools/flow')) {
    try {
      const result = await chrome.tabs.sendMessage(tab.id, { type: 'CREATE_VERSE_IMAGE', prompt });
      await chrome.storage.local.remove(['pendingFlowPrompt', 'pendingFlowCreatedAt']);
      status.textContent = result?.message || 'Sent to Flow.';
    } catch {
      status.textContent = 'Reload the Flow tab, then click Create image in Flow again.';
    }
  } else {
    await chrome.tabs.create({ url: 'https://labs.google/fx/tools/flow' });
    status.textContent = 'Flow opened. Sign in if prompted; the prompt will be filled when the page is ready.';
  }
});

chooseVerse().catch(() => { status.textContent = 'Could not load the verse list.'; });
