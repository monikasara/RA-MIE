import os
import time
import subprocess
from playwright.sync_api import sync_playwright

def main():
    print("Starting server...")
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    server = subprocess.Popen(
        ["venv\\Scripts\\python.exe", "-m", "uvicorn", "src.api.main:app", "--host", "127.0.0.1", "--port", "8015"],
        env=env
    )
    time.sleep(3)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            
            # Desktop
            page_d = browser.new_page()
            page_d.set_viewport_size({"width": 1280, "height": 800})
            page_d.goto("http://127.0.0.1:8015/static/hospital_login.html")
            # Create a doctor via test or register (we will just register)
            page_d.click("button[onclick*=\"switchMode('register'\"]")
            import uuid
            username = f"doc_{uuid.uuid4().hex[:8]}"
            page_d.fill("input#r_user", username)
            page_d.fill("input#r_pass", "password123")
            page_d.select_option("select#r_role", "Doctor")
            page_d.click("#registerForm button[type='submit']")
            time.sleep(1) # wait for alert
            
            # login
            page_d.click("button[onclick*=\"switchMode('login'\"]")
            page_d.fill("input#l_user", username)
            page_d.fill("input#l_pass", "password123")
            page_d.click("#loginForm button[type='submit']")
            
            # Wait for dashboard to load
            page_d.wait_for_selector("#riskChart", state="visible", timeout=10000)
            time.sleep(1)
            page_d.screenshot(path="screenshot_dashboard_desktop.png", full_page=True)
            
            # Mobile
            page_m = browser.new_page()
            page_m.set_viewport_size({"width": 375, "height": 812}) # iPhone X
            page_m.goto("http://127.0.0.1:8015/static/hospital_login.html")
            page_m.fill("input#l_user", username)
            page_m.fill("input#l_pass", "password123")
            page_m.click("#loginForm button[type='submit']")
            page_m.wait_for_selector("#riskChart", state="visible", timeout=5000)
            time.sleep(1)
            page_m.screenshot(path="screenshot_dashboard_mobile.png", full_page=True)
            
            browser.close()
    finally:
        print("Shutting down server...")
        server.terminate()

if __name__ == "__main__":
    main()
