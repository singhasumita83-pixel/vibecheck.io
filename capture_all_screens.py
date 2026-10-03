import time
from playwright.sync_api import sync_playwright

def capture_screens():
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    artifact_dir = r"C:\Users\HP V2192TX\.gemini\antigravity-ide\brain\82416806-c53c-48c2-bfb9-8927835a2136"

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=chrome_path,
            headless=True,
            args=["--no-sandbox", "--disable-gpu"]
        )
        context = browser.new_context(viewport={"width": 1280, "height": 920})
        page = context.new_page()

        # 1. Capture Landing Screen (Light & Dark)
        print("Capturing Landing Screen...")
        page.goto("http://127.0.0.1:5000/")
        page.wait_for_selector("#upload-screen")
        page.screenshot(path=f"{artifact_dir}/01_landing_screen.png")

        # 2. Trigger "⚡ Try Demo" and capture the Analyzing screen
        print("Capturing Analyzing Screen...")
        page.click("#btn-try-demo")
        page.wait_for_selector("#analyzing-screen:not(.hidden)", timeout=3000)
        page.screenshot(path=f"{artifact_dir}/02_analyzing_screen.png")

        # 3. Wait for Report Screen to render
        print("Capturing Report Screen...")
        page.wait_for_selector("#report-screen:not(.hidden)", timeout=10000)
        page.wait_for_timeout(800)
        page.screenshot(path=f"{artifact_dir}/03_report_screen.png")

        # 4. Click Marker 1 to show card sync & bounding box
        print("Capturing Marker 1 Selection...")
        marker1 = page.locator(".marker-pin").first
        if marker1.is_visible():
            marker1.click()
            page.wait_for_timeout(500)
            page.screenshot(path=f"{artifact_dir}/04_marker_selected.png")

        # 5. Capture the Refactored Demo App
        print("Capturing Demo App (/demo)...")
        page.goto("http://127.0.0.1:5000/demo")
        page.wait_for_timeout(500)
        page.screenshot(path=f"{artifact_dir}/05_demo_app.png")

        # 6. Capture Repo Mode Input Screen
        print("Capturing Repo Mode Input Screen...")
        page.goto("http://127.0.0.1:5000/")
        page.wait_for_selector("#tab-mode-repo")
        page.click("#tab-mode-repo")
        page.wait_for_timeout(400)
        page.screenshot(path=f"{artifact_dir}/07_repo_mode_input.png")

        # 7. Capture Repo Mode Report Screen (File Tree & Diffs)
        print("Capturing Repo Mode Report Screen...")
        page.click("#btn-try-repo-demo")
        page.wait_for_selector("#report-screen:not(.hidden)", timeout=10000)
        page.wait_for_timeout(800)
        page.screenshot(path=f"{artifact_dir}/08_repo_report_screen.png")

        # 8. Scroll into card 1 diff detail
        print("Capturing Card 1 Diff Detail...")
        card1 = page.locator("#card-r1")
        card1.scroll_into_view_if_needed()
        page.wait_for_timeout(400)
        page.screenshot(path=f"{artifact_dir}/10_repo_card1_diff_detail.png")

        browser.close()
        print("All screen captures including Repo Mode saved successfully!")

if __name__ == "__main__":
    capture_screens()



