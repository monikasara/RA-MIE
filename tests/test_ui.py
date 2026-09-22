import asyncio
import os
import subprocess
import time
import base64
from playwright.async_api import async_playwright

async def run_tests():
    print("Starting Uvicorn Server...")
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    server = subprocess.Popen(
        ["venv\\Scripts\\python.exe", "-m", "uvicorn", "src.api.main:app", "--port", "8007"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(5)
    
    if server.poll() is not None:
        out, err = server.communicate()
        print("SERVER FAILED TO START")
        print(err.decode())
        return

    img_path = os.path.abspath("sample_images/mri/1 no.jpeg")
    with open(img_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()

    print("Server started. Launching Playwright...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()
        
        print("\n--- 1. Testing Personal Page (File Upload & Preview) ---")
        await page.goto("http://127.0.0.1:8007/static/personal.html")
        print("Loaded personal.html")
        
        print("Uploading file using Playwright proper method...")
        await page.set_input_files("input#encImg", img_path)
        
        await page.wait_for_timeout(500) # Give preview time to load
        src = await page.locator("#encPreview").get_attribute("src")
        print(f"Preview image src populated successfully: {src.startswith('data:image/jpeg;base64,')}")
        
        print("\n--- 2. Testing Loading State & Encryption Success ---")
        await page.fill("#encPass", "secret123")
        
        # Route to delay the response to test loading state
        async def delay_route(route):
            await asyncio.sleep(1.0)
            await route.continue_()
        await page.route("**/api/images/encrypt", delay_route)
        
        print("Clicking Encrypt... checking immediate UI state.")
        await page.locator("#encBtn").click()
        await asyncio.sleep(0.1) # Small tick for DOM to update
        
        spinner_display = await page.locator("#encLoader").evaluate("el => window.getComputedStyle(el).display")
        btn_disabled = await page.locator("#encBtn").is_disabled()
        print(f"Loading spinner is visible: {spinner_display == 'block'}")
        print(f"Submit button is disabled: {btn_disabled}")
        
        print("Waiting for JSZip preview and Download button to appear...")
        await page.wait_for_selector("#downloadZipBtn", state="visible", timeout=15000)
        
        print("Clicking manual Download ZIP button...")
        async with page.expect_download() as download_info:
            await page.locator("#downloadZipBtn").click()
        
        download = await download_info.value
        print(f"Download triggered successfully! Suggested filename: {download.suggested_filename}")
        await page.unroute("**/api/images/encrypt")
        
        print("Checking Risk Badges...")
        await page.wait_for_selector("#riskResult", state="visible")
        low = await page.locator("#rlLow").inner_text()
        print(f"Risk Badge (Low) populated: {low}")
        
        print("\n--- 3. Testing Hospital Login & Patient RBAC ---")
        await page.goto("http://127.0.0.1:8007/static/hospital_login.html")
        
        ts = int(time.time())
        doc_user = f"doc_{ts}"
        pat_user = f"pat_{ts}"
        
        # Register a patient
        await page.locator(".tab-btn:has-text('Register')").click()
        await page.fill("#r_user", pat_user)
        await page.fill("#r_pass", "securepass123")
        await page.select_option("#r_role", "Patient")
        await page.locator("#registerForm button[type='submit']").click()
        await page.wait_for_selector("#alertBox.alert-success", state="visible")
        print(f"Registered dummy patient: {pat_user}")
        
        print("Logging in as the Patient...")
        await page.locator(".tab-btn:has-text('Login')").click()
        await page.fill("#l_user", pat_user)
        await page.fill("#l_pass", "securepass123")
        await page.locator("#loginForm button[type='submit']").click()
        await page.wait_for_url("**/hospital_dashboard.html*")
        
        print("Verifying Batch Encrypt section is HIDDEN for Patient (RBAC)...")
        await page.wait_for_selector("#userInfo", state="visible")
        # Ensure #batchSection is not block
        batch_display = await page.locator("#batchSection").evaluate("el => window.getComputedStyle(el).display")
        print(f"Batch Section is hidden (display: none): {batch_display == 'none'}")
        
        print("\n--- 4. Testing Logout & Token Clearing ---")
        await page.locator("button:has-text('Logout')").click()
        await page.wait_for_url("**/hospital_login.html*")
        token = await page.evaluate("localStorage.getItem('hospital_token')")
        print(f"Token cleared from localStorage: {token is None}")
        
        print("\n--- 5. Testing Audit Log Render as Doctor ---")
        # Register the doctor
        await page.locator(".tab-btn:has-text('Register')").click()
        await page.fill("#r_user", doc_user)
        await page.fill("#r_pass", "securepass123")
        await page.select_option("#r_role", "Doctor")
        await page.locator("#registerForm button[type='submit']").click()
        await page.wait_for_selector("#alertBox.alert-success", state="visible")
        print(f"Registered unique doctor: {doc_user}")
        
        print("Logging in as the Doctor...")
        await page.locator(".tab-btn:has-text('Login')").click()
        await page.fill("#l_user", doc_user)
        await page.fill("#l_pass", "securepass123")
        await page.locator("#loginForm button[type='submit']").click()
        await page.wait_for_url("**/hospital_dashboard.html*")
        
        await page.wait_for_selector("#auditTable tr", state="attached")
        row_count = await page.locator("#auditTable tr").count()
        first_row = await page.locator("#auditTable tr").first.inner_text()
        print(f"Audit log row rendered successfully: count > 0? {row_count > 0}")
        print(f"First Audit Log Entry: {first_row.strip()}")
        
        print("\nClosing browser and stopping server...")
        await browser.close()
    
    server.terminate()
    print("Test script finished completely.")

if __name__ == "__main__":
    asyncio.run(run_tests())
