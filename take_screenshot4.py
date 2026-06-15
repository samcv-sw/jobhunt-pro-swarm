from playwright.sync_api import sync_playwright
import os

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        file_path = f"file:///{os.path.abspath('web/test_shell.html').replace(chr(92), '/')}"
        print(f"Loading {file_path}")
        page.goto(file_path)
        
        page.screenshot(path='test_shell.png', full_page=True)
        browser.close()

if __name__ == '__main__':
    run()
