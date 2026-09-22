import os
import shutil
import zipfile
import io
import cv2
import numpy as np
import hashlib
import time
import json
from src.adaptive_encryption import encrypt_adaptive, decrypt_adaptive
from src.api.routers.images import serialize_metadata, deserialize_metadata
from src.key_generation import generate_keys
from src.preprocessing import preprocess_image

def test_priority1():
    print("\n" + "="*50)
    print("PRIORITY 1: CLEAN ENCRYPT -> DECRYPT ISOLATION TEST")
    print("="*50)
    orig_path = "sample_images/mri/1 no.jpeg"
    img = cv2.imread(orig_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_rgb = preprocess_image(img_rgb, target_size=(512, 512))
    
    passphrase = "strict_test_password_123"
    print(f"Encrypting {orig_path} (preprocessed)...")
    enc_img, metadata = encrypt_adaptive(img_rgb, passphrase, (4,4))
    
    out_dir = os.path.abspath("tests/scratch/priority1_clean")
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)
    
    enc_bgr = cv2.cvtColor(enc_img, cv2.COLOR_RGB2BGR)
    cv2.imwrite(f"{out_dir}/encrypted.png", enc_bgr)
    with open(f"{out_dir}/metadata.json", "w") as f:
        json.dump(serialize_metadata(metadata), f)
        
    print(f"Saved exactly 2 files to {out_dir}:")
    for f in os.listdir(out_dir): print(f" - {f}")
    
    print("\nDecrypting ONLY from those disk files...")
    read_enc = cv2.imread(f"{out_dir}/encrypted.png")
    read_rgb = cv2.cvtColor(read_enc, cv2.COLOR_BGR2RGB)
    with open(f"{out_dir}/metadata.json", "r") as f:
        read_meta = deserialize_metadata(json.load(f))
        
    dec_img = decrypt_adaptive(read_rgb, read_meta, passphrase)
    dec_bgr = cv2.cvtColor(dec_img, cv2.COLOR_RGB2BGR)
    
    prep_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
    is_exact = np.array_equal(prep_bgr, dec_bgr)
    print(f"Pixel-perfect match with preprocessed original? {is_exact}")
    if not is_exact:
        diff = np.abs(prep_bgr.astype(int) - dec_bgr.astype(int))
        print(f"Max difference: {np.max(diff)}")

def test_priority3():
    print("\n" + "="*50)
    print("PRIORITY 3: KEY GENERATION (SHA-256 VERIFICATION)")
    print("="*50)
    passphrase = "academic_secure_passphrase"
    dummy_image = np.zeros((10, 10, 3), dtype=np.uint8)
    
    hash_pass = hashlib.sha256(passphrase.encode('utf-8')).digest()
    hash_img = hashlib.sha256(dummy_image.tobytes()).digest()
    
    print(f"Input Passphrase: '{passphrase}'")
    print(f"SHA-256(passphrase): {hash_pass.hex()}")
    print(f"SHA-256(image):      {hash_img.hex()}")
    
    x0_perm, mu_perm, x0_diff, mu_diff = generate_keys(passphrase, dummy_image)
    print("\nGenerated Parameters for Chaotic Engine:")
    print(f"  x0_perm: {x0_perm:.15f}")
    print(f"  mu_perm: {mu_perm:.15f}")
    print(f"  x0_diff: {x0_diff:.15f}")
    print(f"  mu_diff: {mu_diff:.15f}")

def entropy(image):
    hist = cv2.calcHist([image], [0], None, [256], [0, 256])
    hist = hist.ravel() / hist.sum()
    logs = np.log2(hist + 1e-10)
    return -1.0 * np.sum(hist * logs)

def npcr_uaci(img1, img2):
    i1 = img1.astype(np.float64)
    i2 = img2.astype(np.float64)
    diff = np.abs(i1 - i2)
    npcr = np.sum(diff > 0) / i1.size * 100
    uaci = np.sum(diff) / (255.0 * i1.size) * 100
    return npcr, uaci

def correlation_avg(img, samples=3000):
    img = img.astype(np.float64)
    h, w = img.shape[:2]
    if len(img.shape) == 3: img = img[:,:,0]
    
    def get_corr(x1, y1, x2, y2):
        v1, v2 = img[y1, x1], img[y2, x2]
        return np.corrcoef(v1, v2)[0,1] if np.std(v1)>0 and np.std(v2)>0 else 0
        
    x = np.random.randint(0, w-1, samples)
    y = np.random.randint(0, h-1, samples)
    
    ch = get_corr(x, y, x+1, y)
    cv = get_corr(x, y, x, y+1)
    cd = get_corr(x, y, x+1, y+1)
    
    return np.mean([ch, cv, cd])

def test_priority4():
    print("\n" + "="*50)
    print("PRIORITY 4: ACADEMIC EVALUATION METRICS")
    print("="*50)
    images = [
        "sample_images/mri/1 no.jpeg",
        "sample_images/mri/36 no.jpg",
        "sample_images/mri/N15.jpg"
    ]
    passphrase = "academic_eval_passphrase"
    
    print(f"{'Image':<12} | {'Ent(Orig)':<9} | {'Ent(Enc)':<9} | {'NPCR(%)':<9} | {'UACI(%)':<9} | {'Corr(Orig)':<10} | {'Corr(Enc)':<10} | {'Enc Time':<10} | {'Dec Time':<10}")
    print("-" * 115)
    
    for path in images:
        img_name = os.path.basename(path)
        img = cv2.imread(path)
        if img is None: continue
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_rgb = preprocess_image(img_rgb, target_size=(512, 512))
        
        ent_o = entropy(img_rgb)
        corr_o = correlation_avg(img_rgb)
        
        t0 = time.time()
        enc_img, metadata = encrypt_adaptive(img_rgb, passphrase, (4,4))
        enc_time = (time.time() - t0) * 1000
        
        t0 = time.time()
        dec_img = decrypt_adaptive(enc_img, metadata, passphrase)
        dec_time = (time.time() - t0) * 1000
        
        ent_e = entropy(enc_img)
        corr_e = correlation_avg(enc_img)
        
        # NPCR & UACI via 1-bit different key
        enc_img2, _ = encrypt_adaptive(img_rgb, passphrase + "1", (4,4))
        npcr_val, uaci_val = npcr_uaci(enc_img, enc_img2)
        
        print(f"{img_name:<12} | {ent_o:<9.4f} | {ent_e:<9.4f} | {npcr_val:<9.4f} | {uaci_val:<9.4f} | {corr_o:<10.4f} | {corr_e:<10.4f} | {enc_time:>5.1f} ms | {dec_time:>5.1f} ms")

if __name__ == "__main__":
    test_priority1()
    test_priority3()
    test_priority4()
