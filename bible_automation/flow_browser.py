"""Best-effort interactive automation for Google Flow's web UI.

Flow is a consumer UI and its controls change. Authentication stays in the user's
visible browser; this module never reads cookies or attempts to bypass access checks.
"""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from .core import Verse

FLOW_URL = "https://labs.google/fx/tools/flow"


def create_with_flow(verse: Verse, output_path: Path) -> Path:
    """Open Flow, let the user sign in, submit a prompt, then save generated image.

    Google Flow UI changes often; if the prompt/control cannot be identified, the
    browser is left open so the user can finish manually rather than guessing.
    """
    prompt = (
        "Create a single square 1:1 inspirational Bible verse poster image. "
        "Use a peaceful sunrise landscape, gentle natural light, elegant minimal "
        "composition, warm cream and muted gold. Include the following exact text "
        "clearly and legibly, with no other text or watermark:\n"
        f'“{verse.text}”\n— {verse.reference} (KJV)'
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch_persistent_context(
            user_data_dir=str(Path(".flow-profile").resolve()),
            headless=False,
            accept_downloads=True,
            viewport={"width": 1440, "height": 1000},
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        page.goto(FLOW_URL, wait_until="domcontentloaded")
        print("Flow opened in a visible browser. Sign in if prompted and open your Flow project.")
        input("When Flow is ready for a prompt, press Enter here... ")

        # Flow's UI varies; try common editable prompt controls.
        prompt_box = None
        for selector in [
            'textarea',
            '[contenteditable="true"]',
            'input[placeholder*="prompt" i]',
            '[role="textbox"]',
        ]:
            try:
                candidate = page.locator(selector).last
                candidate.wait_for(state="visible", timeout=2500)
                prompt_box = candidate
                break
            except PlaywrightTimeoutError:
                continue
        submitted = False
        if prompt_box is None:
            print("Couldn't identify the prompt field. Flow's current controls are listed in output/flow-debug.txt.")
        else:
            prompt_box.fill(prompt)
            for label in ["Generate", "Create", "Run", "Make", "Send"]:
                button = page.get_by_role("button", name=label, exact=False)
                try:
                    for index in range(button.count() - 1, -1, -1):
                        candidate = button.nth(index)
                        if candidate.is_visible() and candidate.is_enabled():
                            candidate.click(timeout=3000)
                            submitted = True
                            break
                    if submitted:
                        break
                except Exception:
                    continue
            if not submitted:
                print("Prompt is ready, but Flow's generate control was not recognized.")
        if not submitted:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(output_path.parent / "flow-debug.png"), full_page=True)
            buttons = page.get_by_role("button").all_text_contents()
            (output_path.parent / "flow-debug.txt").write_text(
                "Page: " + page.url + "\nVisible button labels:\n" + "\n".join(buttons),
                encoding="utf-8",
            )
            print("The browser stays open. Complete generation in Flow, then return here.")
            input("After the image is generated, press Enter to try saving it... ")
        else:
            print("Generation started automatically. Waiting for Flow's result...")

        # Give Flow time to finish; users may need to select/download manually if its UI changes.
        try:
            page.locator("img").last.wait_for(state="visible", timeout=180000)
            images = page.locator("img")
            for index in range(images.count() - 1, -1, -1):
                image = images.nth(index)
                try:
                    box = image.bounding_box() if image.is_visible() else None
                    if box and box["width"] >= 300 and box["height"] >= 200:
                        image.screenshot(path=str(output_path), timeout=15000)
                        print(f"Saved a screenshot of Flow's generated image to {output_path}")
                        input("Press Enter to close the Flow browser... ")
                        browser.close()
                        return output_path
                except Exception:
                    pass
        except PlaywrightTimeoutError:
            pass

        print("Could not automatically capture the result. Use Flow's download button, then save to:")
        print(output_path.resolve())
        input("Press Enter to close the Flow browser... ")
        browser.close()
    return output_path
