import os
import time
import zipfile
import requests
import subprocess
import cv2
import numpy as np

def create_plain_png(source_path, dest_path):
    """Load image and save as a plain PNG to strip any EXIF or alpha channels."""
    img = cv2.imread(source_path, cv2.IMREAD_COLOR)
    cv2.imwrite(dest_path, img)

def main():
    print("Starting real Uvicorn server on port 8011...")
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    server = subprocess.Popen(
        ["venv\\Scripts\\python.exe", "-m", "uvicorn", "src.api.main:app", "--port", "8011"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(5)
    
    try:
        if server.poll() is not None:
            out, err = server.communicate()
            print("Server failed to start:")
            print(err.decode())
            return

        print("Preparing JPEG test image...")
        orig_path = os.path.abspath("sample_images/mri/1 no.jpeg")
        scratch_dir = os.path.abspath("tests/scratch")
        os.makedirs(scratch_dir, exist_ok=True)
        
        # Load the EXACT baseline image that is being uploaded
        orig_bgr = cv2.imread(orig_path)
        
        print("1. Calling real /api/images/encrypt via HTTP...")
        url_encrypt = "http://127.0.0.1:8011/api/images/encrypt"
        with open(orig_path, "rb") as f:
            files = {"image": ("1 no.jpeg", f, "image/jpeg")}
            data = {"passphrase": "real_http_secret"}
            resp = requests.post(url_encrypt, files=files, data=data)
        
        if resp.status_code != 200:
            print(f"Encrypt failed: {resp.status_code} - {resp.text}")
            return
        
        print("2. Saving ZIP to disk exactly as browser does...")
        zip_path = os.path.join(scratch_dir, "downloaded.zip")
        with open(zip_path, "wb") as f:
            f.write(resp.content)
            
        print("3. Unzipping to disk...")
        extract_dir = os.path.join(scratch_dir, "extracted")
        os.makedirs(extract_dir, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(extract_dir)
            
        enc_png_path = os.path.join(extract_dir, "encrypted.png")
        meta_json_path = os.path.join(extract_dir, "metadata.json")
        
        print("4. Calling real /api/images/decrypt via HTTP with multipart re-upload...")
        url_decrypt = "http://127.0.0.1:8011/api/images/decrypt"
        with open(enc_png_path, "rb") as f_img, open(meta_json_path, "rb") as f_meta:
            files_dec = {
                "encrypted_image": ("encrypted.png", f_img, "image/png"),
                "metadata_file": ("metadata.json", f_meta, "application/json")
            }
            data_dec = {"passphrase": "real_http_secret"}
            resp_dec = requests.post(url_decrypt, files=files_dec, data=data_dec)
            
        if resp_dec.status_code != 200:
            print(f"Decrypt failed: {resp_dec.status_code} - {resp_dec.text}")
            return
            
        print("5. Saving decrypted image to disk and comparing...")
        dec_png_path = os.path.join(scratch_dir, "decrypted.png")
        with open(dec_png_path, "wb") as f:
            f.write(resp_dec.content)
            
        # Load the final downloaded image
        dec_bgr = cv2.imread(dec_png_path)
        
        is_exact = np.array_equal(orig_bgr, dec_bgr)
        print(f"Real HTTP Roundtrip Pixel-perfect match? {is_exact}")
        
        if not is_exact:
            print("HTTP layer test FAILED. There is a bug in the HTTP encoding/decoding!")
            diff = np.abs(orig_bgr.astype(int) - dec_bgr.astype(int))
            print(f"Max difference between pixels: {np.max(diff)}")
            
            # Print shapes to see if they were resized
            print(f"Original shape: {orig_bgr.shape}")
            print(f"Decrypted shape: {dec_bgr.shape}")
        else:
            print("HTTP layer test PASSED perfectly. The API routes and encoding are flawless.")
            
    finally:
        print("Shutting down server...")
        server.terminate()

if __name__ == "__main__":
    main()
