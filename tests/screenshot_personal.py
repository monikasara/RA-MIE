import os
import time
import subprocess
from playwright.sync_api import sync_playwright

def main():
    print("Starting server...")
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    server = subprocess.Popen(
        ["venv\\Scripts\\python.exe", "-m", "uvicorn", "src.api.main:app", "--host", "127.0.0.1", "--port", "8012"],
        env=env
    )
    time.sleep(3)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            # Set viewport to something wide enough for side-by-side
            page.set_viewport_size({"width": 1280, "height": 800})
            
            page.goto("http://127.0.0.1:8012/static/personal.html")
            
            # Take before screenshot
            page.screenshot(path="screenshot_before.png", full_page=True)
            
            # Upload and encrypt
            img_path = os.path.abspath("sample_images/mri/1 no.jpeg")
            page.set_input_files("input#encImg", img_path)
            page.fill("input#encPass", "secret")
            
            page.click("button#encBtn")
            
            # Wait for result container to be visible
            page.wait_for_selector("#encResultContainer", state="visible", timeout=15000)
            
            # Wait a little for image to load and canvas to draw
            time.sleep(2) 
            
            page.screenshot(path="screenshot_after_encrypt.png", full_page=True)
            print("Screenshots taken.")
            
            browser.close()
    finally:
        print("Shutting down server...")
        server.terminate()

if __name__ == "__main__":
    main()
