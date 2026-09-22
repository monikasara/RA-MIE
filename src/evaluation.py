import os
import glob
import time
import csv
import cv2
import numpy as np
from collections import defaultdict

from cipher import encrypt, encrypt_selective, decrypt
from adaptive_encryption import encrypt_adaptive, decrypt_adaptive
from metrics import calculate_entropy, calculate_npcr, calculate_uaci, calculate_correlation, calculate_chi_square, plot_histogram
from risk_analysis.risk_map import generate_risk_map

def find_medical_images(base_dir="sample_images"):
    supported_exts = ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.tif', '*.tiff']
    images = []
    
    for subfolder in ['mri', 'xray', 'ct']:
        folder_path = os.path.join(base_dir, subfolder)
        for ext in supported_exts:
            # Case insensitive search might be needed on some OS, but glob handles it on Windows usually
            images.extend(glob.glob(os.path.join(folder_path, ext)))
            images.extend(glob.glob(os.path.join(folder_path, ext.upper())))
            
    # Remove duplicates if any
    return list(set(images))

def modify_one_pixel(image):
    """Creates a copy of the image with a single bit changed in the first pixel."""
    modified = image.copy()
    if len(modified.shape) == 3:
        modified[0, 0, 0] = modified[0, 0, 0] ^ 1
    else:
        modified[0, 0] = modified[0, 0] ^ 1
    return modified

def run_evaluation():
    print("RA-MIE Experimental Evaluation Pipeline")
    print("=======================================")
    
    images = find_medical_images()
    
    if not images:
        print("\n[WARNING] Evaluation dataset needs to be added.")
        print("No medical images found in sample_images/mri/, sample_images/xray/, or sample_images/ct/.")
        print("Please add actual medical images to these folders to run the full evaluation.")
        print("Stopping experiment gracefully. No experimental values will be fabricated.")
        return
        
    print(f"Found {len(images)} medical images for evaluation.")
    
    results = []
    passphrase = "secure_evaluation_password_2026"
    
    os.makedirs("results/histograms", exist_ok=True)
    os.makedirs("results/risk_maps", exist_ok=True)
    os.makedirs("results/encrypted_images", exist_ok=True)
    os.makedirs("results/decrypted_images", exist_ok=True)
    
    for img_path in images:
        print(f"\nProcessing {img_path}...")
        image_name = os.path.basename(img_path)
        original_img = cv2.imread(img_path)
        if original_img is None:
            print(f"Error loading {img_path}, skipping.")
            continue
            
        # Convert BGR to RGB for processing
        original_img = cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB)
        modified_img = modify_one_pixel(original_img)
        
        methods = {
            "Full Encryption": lambda img: encrypt(img, passphrase),
            "ROI Encryption": lambda img: encrypt_selective(img, passphrase),
            "RA-MIE": lambda img: encrypt_adaptive(img, passphrase, grid_size=(4, 4))
        }
        
        for method_name, method_func in methods.items():
            print(f"  Running {method_name}...")
            
            # --- Timing Encryption ---
            start_enc = time.perf_counter()
            enc_result = method_func(original_img)
            end_enc = time.perf_counter()
            enc_time = end_enc - start_enc
            
            # Handle return types (RA-MIE returns tuple)
            if method_name == "RA-MIE":
                enc_img_array, metadata = enc_result
                # Save risk map for RA-MIE
                rm_save_dir = os.path.join("results", "risk_maps")
                # Ensure the generate_risk_map generates and saves correctly
                generate_risk_map(original_img, grid_size=(4, 4), save_dir=rm_save_dir)
                # Rename risk map safely
                if os.path.exists(os.path.join(rm_save_dir, "risk_map.png")):
                    os.replace(os.path.join(rm_save_dir, "risk_map.png"),
                               os.path.join(rm_save_dir, f"{os.path.splitext(image_name)[0]}_risk_map.png"))
            else:
                enc_img_array = np.asarray(enc_result)
                metadata = None
                
            # --- NPCR / UACI (Requires encrypting modified image) ---
            mod_result = method_func(modified_img)
            if method_name == "RA-MIE":
                mod_enc_img_array, _ = mod_result
            else:
                mod_enc_img_array = np.asarray(mod_result)
                
            npcr_val = calculate_npcr(enc_img_array, mod_enc_img_array)
            uaci_val = calculate_uaci(enc_img_array, mod_enc_img_array)
            
            # --- Entropy, Correlation, & Chi-Square ---
            entropy_val = calculate_entropy(enc_img_array)
            corr_h = calculate_correlation(enc_img_array, 'horizontal')
            corr_v = calculate_correlation(enc_img_array, 'vertical')
            corr_d = calculate_correlation(enc_img_array, 'diagonal')
            chi_square = calculate_chi_square(enc_img_array)
            chi_pass = chi_square < 293.25
            print(f"    Chi-Square: {chi_square:.2f} (Pass: {chi_pass})")
            
            # --- Timing Decryption ---
            start_dec = time.perf_counter()
            if method_name == "RA-MIE":
                dec_img = decrypt_adaptive(enc_img_array, metadata, passphrase)
            else:
                dec_img = decrypt(enc_result, passphrase)
            end_dec = time.perf_counter()
            dec_time = end_dec - start_dec
            
            # --- Key Sensitivity Test ---
            wrong_passphrase = passphrase[:-1] + ('7' if passphrase[-1] != '7' else '8')
            if method_name == "RA-MIE":
                dec_img_wrong = decrypt_adaptive(enc_img_array, metadata, wrong_passphrase)
            else:
                dec_img_wrong = decrypt(enc_result, wrong_passphrase)
            
            key_sens_npcr = calculate_npcr(original_img, dec_img_wrong)
            
            # --- Differential Attack Analysis (RA-MIE only) ---
            diff_high_npcr, diff_high_uaci = None, None
            diff_low_npcr, diff_low_uaci = None, None
            
            if method_name == "RA-MIE":
                level_matrix = metadata['level_matrix']
                y_splits = metadata['y_splits']
                x_splits = metadata['x_splits']
                rows, cols = metadata['grid_size']
                
                high_idx = next(((i, j) for i in range(rows) for j in range(cols) if level_matrix[i, j] == "HIGH"), None)
                low_idx = next(((i, j) for i in range(rows) for j in range(cols) if level_matrix[i, j] == "LOW"), None)
                
                def eval_diff_region(idx):
                    if not idx: return None, None
                    i, j = idx
                    y, x = y_splits[i], x_splits[j]
                    mod_img = original_img.copy()
                    if len(mod_img.shape) == 3:
                        mod_img[y, x, 0] = mod_img[y, x, 0] ^ 1
                    else:
                        mod_img[y, x] = mod_img[y, x] ^ 1
                    mod_enc, _ = encrypt_adaptive(mod_img, passphrase, grid_size=(4, 4))
                    return calculate_npcr(enc_img_array, mod_enc), calculate_uaci(enc_img_array, mod_enc)
                    
                diff_high_npcr, diff_high_uaci = eval_diff_region(high_idx)
                diff_low_npcr, diff_low_uaci = eval_diff_region(low_idx)
            
            # --- Verify Decryption ---
            is_lossless = np.array_equal(original_img, dec_img)
            print(f"    Decryption success (lossless): {is_lossless}")
            
            # Save results
            results.append({
                "Image": image_name,
                "Method": method_name,
                "Entropy": entropy_val,
                "NPCR": npcr_val,
                "UACI": uaci_val,
                "Horizontal_Correlation": corr_h,
                "Vertical_Correlation": corr_v,
                "Diagonal_Correlation": corr_d,
                "Encryption_Time": enc_time,
                "Decryption_Time": dec_time,
                "Lossless_Decryption": is_lossless,
                "Chi_Square": chi_square,
                "Key_Sensitivity_NPCR": key_sens_npcr,
                "Key_Sensitivity_Diff_Percent": key_sens_npcr,
                "Diff_Attack_HighRisk_NPCR": diff_high_npcr,
                "Diff_Attack_LowRisk_NPCR": diff_low_npcr,
                "Diff_Attack_HighRisk_UACI": diff_high_uaci,
                "Diff_Attack_LowRisk_UACI": diff_low_uaci
            })
            
            # Save Encrypted Image
            out_name = f"{os.path.splitext(image_name)[0]}_{method_name.replace(' ', '_')}.png"
            cv2.imwrite(os.path.join("results", "encrypted_images", out_name), cv2.cvtColor(enc_img_array, cv2.COLOR_RGB2BGR))
            
            # Save Decrypted Image
            dec_out_name = f"{os.path.splitext(image_name)[0]}_{method_name.replace(' ', '_')}_decrypted.png"
            cv2.imwrite(os.path.join("results", "decrypted_images", dec_out_name), cv2.cvtColor(dec_img, cv2.COLOR_RGB2BGR))
            
            # Save Histogram
            hist_buf = plot_histogram(original_img, enc_img_array)
            with open(os.path.join("results", "histograms", f"{os.path.splitext(image_name)[0]}_{method_name.replace(' ', '_')}_histogram.png"), "wb") as f:
                f.write(hist_buf.read())
                
            # Risk Map Percentages (Only for RA-MIE)
            if method_name == "RA-MIE":
                total_regions = metadata['level_matrix'].size
                unique, counts = np.unique(metadata['level_matrix'], return_counts=True)
                counts_dict = dict(zip(unique, counts))
                low_pct = (counts_dict.get('LOW', 0) / total_regions) * 100
                med_pct = (counts_dict.get('MEDIUM', 0) / total_regions) * 100
                high_pct = (counts_dict.get('HIGH', 0) / total_regions) * 100
                print(f"    Risk Map - LOW: {low_pct:.1f}%, MEDIUM: {med_pct:.1f}%, HIGH: {high_pct:.1f}%")
                
    # --- Write CSV ---
    csv_path = "results/evaluation_results.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "Image", "Method", "Entropy", "NPCR", "UACI", 
            "Horizontal_Correlation", "Vertical_Correlation", "Diagonal_Correlation", 
            "Encryption_Time", "Decryption_Time", "Lossless_Decryption",
            "Chi_Square", "Key_Sensitivity_NPCR", "Key_Sensitivity_Diff_Percent",
            "Diff_Attack_HighRisk_NPCR", "Diff_Attack_LowRisk_NPCR",
            "Diff_Attack_HighRisk_UACI", "Diff_Attack_LowRisk_UACI"
        ])
        writer.writeheader()
        writer.writerows(results)
        
    print(f"\nSaved detailed results to {csv_path}")
    
    # --- Generate Averaged Table ---
    avg_results = defaultdict(lambda: defaultdict(list))
    for r in results:
        m = r["Method"]
        for k, v in r.items():
            if k not in ["Image", "Method"]:
                avg_results[m][k].append(v)
                
    table_path = "results/table_results.csv"
    with open(table_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "Method", "Entropy", "NPCR", "UACI", 
            "Horizontal Correlation", "Vertical Correlation", "Diagonal Correlation", 
            "Average Encryption Time", "Average Decryption Time"
        ])
        for m in ["Full Encryption", "ROI Encryption", "RA-MIE"]:
            if m in avg_results:
                writer.writerow([
                    m,
                    np.mean(avg_results[m]["Entropy"]),
                    np.mean(avg_results[m]["NPCR"]),
                    np.mean(avg_results[m]["UACI"]),
                    np.mean(avg_results[m]["Horizontal_Correlation"]),
                    np.mean(avg_results[m]["Vertical_Correlation"]),
                    np.mean(avg_results[m]["Diagonal_Correlation"]),
                    np.mean(avg_results[m]["Encryption_Time"]),
                    np.mean(avg_results[m]["Decryption_Time"])
                ])
                
    print(f"Saved averaged table to {table_path}")
    
    print("\n[NOTE] Graph generation is skipped as it requires data. Once images are evaluated, run src/visualization/plot_results.py.")
    print("Experiment completed successfully.")

if __name__ == "__main__":
    run_evaluation()
