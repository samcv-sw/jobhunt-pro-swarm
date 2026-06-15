from playwright.sync_api import sync_playwright
import os

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        file_path = os.path.abspath('web/test_upload_cv.html')
        print(f"Loading file:///{file_path.replace('\\\\', '/')}")
        page.goto(f"file:///{file_path.replace('\\\\', '/')}")
        
        page.screenshot(path="test_upload_cv.png")
        print("Saved test_upload_cv.png")
        
        browser.close()

if __name__ == "__main__":
    run()
