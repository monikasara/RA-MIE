import os
import time
import subprocess
from playwright.sync_api import sync_playwright

def main():
    print("Starting server...")
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    server = subprocess.Popen(
        ["venv\\Scripts\\python.exe", "-m", "uvicorn", "src.api.main:app", "--host", "127.0.0.1", "--port", "8017"],
        env=env
    )
    time.sleep(3)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_viewport_size({"width": 1280, "height": 900})
            
            # Go to login
            page.goto("http://127.0.0.1:8017/static/hospital_login.html")
            
            import uuid
            patient_username = f"pat_{uuid.uuid4().hex[:8]}"
            doctor_username = f"doc_{uuid.uuid4().hex[:8]}"
            
            # 1. Register Patient
            page.evaluate("switchMode('register')")
            time.sleep(0.5)
            page.fill("input#r_user", patient_username)
            page.fill("input#r_pass", "password123")
            page.select_option("select#r_role", "Patient")
            page.click("#registerForm button[type='submit']")
            page.wait_for_selector(".alert-success")
            
            # 2. Register Doctor
            page.reload()
            page.evaluate("switchMode('register')")
            time.sleep(0.5)
            page.fill("input#r_user", doctor_username)
            page.fill("input#r_pass", "password123")
            page.select_option("select#r_role", "Doctor")
            page.click("#registerForm button[type='submit']")
            page.wait_for_selector(".alert-success")
            
            # 3. Login as Doctor
            page.reload()
            page.evaluate("switchMode('login')")
            time.sleep(0.5)
            page.fill("input#l_user", doctor_username)
            page.fill("input#l_pass", "password123")
            page.click("#loginForm button[type='submit']")
            
            # Wait for dashboard
            page.wait_for_selector("#userInfo", state="visible", timeout=10000)
            time.sleep(1)
            
            # 4. Batch Encrypt 3 images for the new Patient
            # Patient ID is likely 1 or 2, but we need the exact ID.
            # To be safe, we just use the API or sqlite to fetch it, but let's assume we can query it or we just create a dummy ID.
            # Get the exact patient ID from SQLite
            import sqlite3
            conn = sqlite3.connect("ramie_prod.db")
            c = conn.cursor()
            c.execute("SELECT id FROM patients WHERE user_id=(SELECT id FROM users WHERE username=?)", (patient_username,))
            patient_id = c.fetchone()[0]
            conn.close()
            
            # Batch Encrypt
            page.fill("input#batchPids", f"{patient_id},{patient_id},{patient_id}")
            img_paths = [
                os.path.abspath("sample_images/mri/1 no.jpeg"),
                os.path.abspath("sample_images/mri/36 no.jpg"),
                os.path.abspath("sample_images/mri/N15.jpg")
            ]
            page.set_input_files("input#batchFiles", img_paths)
            page.fill("input#batchPass", "batch_secure_123")
            
            print("Submitting batch upload and waiting for download...")
            with page.expect_download(timeout=60000) as download_info:
                page.click("button#batchBtn")
            
            download = download_info.value
            print(f"Batch ZIP Downloaded: {download.suggested_filename}")
            
            # Wait for the success alert box and DOM to refresh stats
            page.wait_for_selector(".alert-success", state="visible", timeout=10000)
            
            # The dashboard auto-reloads stats. Let's wait a second for chart animation
            time.sleep(2)
            
            # Take screenshot of the result
            page.screenshot(path="screenshot_task4_batch.png", full_page=True)
            print("Batch workflow screenshot taken!")
            
            browser.close()
    finally:
        print("Shutting down server...")
        server.terminate()

if __name__ == "__main__":
    main()
