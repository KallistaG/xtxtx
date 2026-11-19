(() => {
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  let busy = false;
  let statusBox;

  function showStatus(text, error = false) {
    if (!statusBox) {
      statusBox = document.createElement('div');
      statusBox.id = 'bible-flow-helper-status';
      Object.assign(statusBox.style, {
        position: 'fixed', zIndex: '2147483647', right: '18px', bottom: '18px',
        maxWidth: '360px', padding: '12px 16px', borderRadius: '10px',
        color: '#fff', background: '#294936', font: '14px/1.4 system-ui,sans-serif',
        boxShadow: '0 4px 18px #0004'
      });
      document.documentElement.appendChild(statusBox);
    }
    statusBox.style.background = error ? '#8b332c' : '#294936';
    statusBox.textContent = `Bible Verse to Flow: ${text}`;
  }

  function findPromptBox() {
    const selectors = ['textarea', '[contenteditable="true"]', 'input[placeholder*="prompt" i]', '[role="textbox"]'];
    for (const selector of selectors) {
      const candidates = [...document.querySelectorAll(selector)].filter((el) => {
        const rect = el.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0 && !el.disabled;
      });
      if (candidates.length) return candidates[candidates.length - 1];
    }
    return null;
  }

  function visibleButtons() {
    return [...document.querySelectorAll('button,[role="button"]')].filter((el) => {
      const rect = el.getBoundingClientRect();
      return rect.width > 0 && rect.height > 0 && !el.disabled;
    });
  }

  function clickNewProjectIfAvailable() {
    const startLabels = /^(new project|create project|start project|new flow|create new project)$/i;
    const button = visibleButtons().find((el) => startLabels.test(
      `${el.innerText || ''} ${el.getAttribute('aria-label') || ''}`.trim()
    ));
    if (button) {
      button.click();
      showStatus('Starting a new Flow project…');
      return true;
    }
    return false;
  }

  function setText(element, value) {
    element.focus();
    if (element.isContentEditable) {
      element.textContent = value;
      element.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: value }));
    } else {
      const prototype = element.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
      const setter = Object.getOwnPropertyDescriptor(prototype, 'value')?.set;
      if (setter) setter.call(element, value); else element.value = value;
      element.dispatchEvent(new Event('input', { bubbles: true }));
      element.dispatchEvent(new Event('change', { bubbles: true }));
    }
  }

  function findGenerateButton() {
    const labelPattern = /^(generate|create|run|make|send)(\s|$)/i;
    return visibleButtons().reverse().find((el) => labelPattern.test(
      `${el.innerText || ''} ${el.getAttribute('aria-label') || ''}`.trim()
    ));
  }

  async function run(prompt) {
    if (busy) return { ok: false, message: 'Flow automation is already running.' };
    busy = true;
    try {
      showStatus('Looking for the Flow project and prompt controls…');
      let field = findPromptBox();
      if (!field) clickNewProjectIfAvailable();
      // Flow can take a while to load or transition into the project editor.
      for (let attempt = 0; attempt < 120; attempt++) {
        field = findPromptBox();
        if (field) break;
        if (attempt === 30) clickNewProjectIfAvailable();
        await sleep(1000);
      }
      if (!field) {
        const message = 'Could not find the prompt field. Sign in and open a Flow project, then click the extension again.';
        showStatus(message, true);
        return { ok: false, message };
      }
      showStatus('Entering your verse prompt…');
      setText(field, prompt);
      await sleep(800);
      const button = findGenerateButton();
      if (!button) {
        const message = 'Prompt entered. Click Flow’s Generate/Create button to start.';
        showStatus(message, true);
        return { ok: false, message };
      }
      button.click();
      const message = 'Generation started in Flow. Wait for the result, then review and download it.';
      showStatus(message);
      return { ok: true, message };
    } catch (error) {
      const message = `Automation failed: ${error?.message || error}`;
      showStatus(message, true);
      return { ok: false, message };
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
