(() => {
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  let busy = false;

  function findPromptBox() {
    const selectors = [
      'textarea',
      '[contenteditable="true"]',
      'input[placeholder*="prompt" i]',
      '[role="textbox"]',
    ];
    for (const selector of selectors) {
      const candidates = [...document.querySelectorAll(selector)].filter((el) => {
        const rect = el.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0 && !el.disabled;
      });
      if (candidates.length) return candidates[candidates.length - 1];
    }
    return null;
  }

  function setText(element, value) {
    element.focus();
    if (element.isContentEditable) {
      element.textContent = value;
      element.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: value }));
      return;
    }
    const prototype = element.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(prototype, 'value')?.set;
    if (setter) setter.call(element, value); else element.value = value;
    element.dispatchEvent(new Event('input', { bubbles: true }));
    element.dispatchEvent(new Event('change', { bubbles: true }));
  }

  function findGenerateButton() {
    const labels = /^(generate|create|run|make|send)(\s|$)/i;
    return [...document.querySelectorAll('button,[role="button"]')].reverse().find((button) => {
      const rect = button.getBoundingClientRect();
      const label = `${button.innerText || ''} ${button.getAttribute('aria-label') || ''}`.trim();
      return rect.width > 0 && rect.height > 0 && !button.disabled && labels.test(label);
    });
  }

  async function run(prompt) {
    if (busy) return { ok: false, message: 'Flow automation is already running.' };
    busy = true;
    try {
      let field;
      for (let attempt = 0; attempt < 30; attempt++) {
        field = findPromptBox();
        if (field) break;
        await sleep(1000);
      }
      if (!field) return { ok: false, message: 'Could not find Flow prompt box. Open a Flow project and retry.' };
      setText(field, prompt);
      await sleep(600);
      const button = findGenerateButton();
      if (!button) return { ok: false, message: 'Prompt filled; click Generate/Create in Flow to continue.' };
      button.click();
      return { ok: true, message: 'Prompt sent; Flow generation started.' };
    } finally {
      busy = false;
    }
  }

  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (message?.type === 'CREATE_VERSE_IMAGE') {
      run(message.prompt).then(sendResponse);
      return true;
    }
  });

  // A newly opened Flow tab picks up a prompt saved by the extension popup.
  (async () => {
    const { pendingFlowPrompt, pendingFlowCreatedAt } = await chrome.storage.local.get([
      'pendingFlowPrompt', 'pendingFlowCreatedAt'
    ]);
    if (!pendingFlowPrompt || !pendingFlowCreatedAt || Date.now() - pendingFlowCreatedAt > 10 * 60 * 1000) return;
    await chrome.storage.local.remove(['pendingFlowPrompt', 'pendingFlowCreatedAt']);
    const result = await run(pendingFlowPrompt);
    if (!result.ok) console.info('[Bible Verse to Flow]', result.message);
  })();
})();
