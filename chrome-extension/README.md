# Bible Verse to Flow Chrome extension

This extension picks a verse from the included KJV list, opens Google Flow, tries to start a new project if needed, waits up to two minutes for Flow's prompt box, enters a square-poster prompt, and attempts to click the generation button. A status message appears on the Flow page while it works. It runs entirely in your browser and does not need a Gemini API key.

## Install in Chrome

1. Download or clone the repository and unzip it if needed.
2. In Chrome, open `chrome://extensions`.
3. Turn on **Developer mode**.
4. Choose **Load unpacked** and select this `chrome-extension` folder.
5. Pin **Bible Verse to Flow** in the Extensions menu.
6. Click its icon, choose a verse if desired, then click **Create image in Flow**.
7. Sign in to Google if asked and allow Flow to load. The extension will try to fill the prompt and start generation. Review the result yourself.

If Flow is already open, the extension works in that tab. If it opens a new tab, the prompt is sent after the Flow page loads. If it cannot identify the prompt field or generation control, open a Flow project and try again; Flow's UI may change over time.

## Privacy and limitations

The extension requests storage for the pending prompt and host access to the Flow page only. It does not collect or transmit your verse or credentials. Google sign-in remains in the browser. It does not auto-publish to Facebook: Facebook Page tokens must not be embedded in a client-side extension, because anyone with access to the extension could extract them. Review/download the image and publish it through an approved secure service or Facebook's official tools.
