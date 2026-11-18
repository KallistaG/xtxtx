# Bible Page Automation

A small Python app for creating a Bible-verse graphic and publishing it to a Facebook Page. It uses a bundled set of public-domain KJV verses and Meta's official Graph API for Page photo posts. Image generation can use either Gemini's API or an experimental visible-browser workflow for Google Flow.

> **Flow browser mode:** `--image-provider flow` opens a real Chromium browser at Flow. You sign in and confirm the page is ready; the script enters the verse prompt and attempts to click Generate/Create automatically. If its controls are not recognized, it saves `output/flow-debug.png` and `output/flow-debug.txt` and leaves the browser available for you to finish. Flow is a consumer UI that changes frequently, so result capture may still need manual help. It does not bypass login, CAPTCHAs, or Google access restrictions. Keep the browser visible and follow Google's terms. The Gemini API remains the more reliable unattended option.

## Windows executable

A Windows build is produced by the GitHub Actions workflow `Build Windows app`. Download the `BiblePageAutomation-Windows` artifact from its successful workflow run, extract the whole folder, copy `.env.example` to `.env`, add your credentials, and launch `Start-Bible-Page-Automation.bat`. Example:

```bat
Start-Bible-Page-Automation.bat create --image-provider flow
```

Keep the whole extracted folder together: it includes the executable and the browser runtime required for Flow. The console window is intentional because the Flow workflow asks you to confirm when the browser is ready. For a one-file executable without the included browser, use the source setup below.

## Quick start (from source)

1. Install Python 3.11+ and dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
   pip install -e .
   ```

2. Copy `.env.example` to `.env` and fill in `GEMINI_API_KEY`. Facebook posting additionally requires `FACEBOOK_PAGE_ID` and a Page access token with the relevant publishing permissions. Keep `.env` private; it is git-ignored.

3. Create an image and preview without publishing:

   ```bash
   bible-post create
   # Or use the visible Flow browser (first install its browser runtime below):
   playwright install chromium
   bible-post create --image-provider flow
   ```

   Output is saved under `output/`. Add `--post` only when you explicitly want to publish.

4. To schedule a daily post, configure `POST_TIME` and `TIMEZONE`, then run:

   ```bash
   bible-post schedule
   ```

   Scheduled mode is **dry-run by default**. Set `ENABLE_AUTO_POST=true` only after validating generated content and credentials. It should run continuously on an always-on host.

## Commands

- `bible-post create` — choose a verse, generate a square image, save a caption and image locally.
- `bible-post create --post` — generate, then publish the image and caption to the configured Page.
- `bible-post schedule` — generate one post daily at `POST_TIME`; only publishes when `ENABLE_AUTO_POST=true`.

Each run prints the generated verse and output path. Review the image before enabling unattended publishing. Verse selection is random from `bible_automation/verses.json`; edit that file to curate the page's content.

## Facebook setup and limitations

Create a Meta developer app, give it the necessary Page publishing permission, authorize a Page, and obtain a **Page access token**. The Page/user and permissions may require app review depending on the account and use case. This app never automates Facebook login or browser clicks; it calls the official Graph API. Meta API versions and permission requirements change, so configure `FACEBOOK_GRAPH_VERSION` to a supported version. Facebook's API may reject posts if the token lacks permission or the app is not approved.

## Safety / cost

Image generation is a paid or quota-limited external API. Do not commit API keys or Page tokens. Generated text in this starter is a known verse list (KJV) rather than AI-invented scripture, to avoid fabricated quotations. Verify verse and translation before posting. There is no claim that this app is affiliated with Google, Meta, or Facebook.
