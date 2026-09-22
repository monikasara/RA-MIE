import cv2
import numpy as np

def npcr_uaci(img1, img2):
    i1 = img1.astype(np.float64)
    i2 = img2.astype(np.float64)
    diff = np.abs(i1 - i2)
    npcr = np.sum(diff > 0) / i1.size * 100
    uaci = np.sum(diff) / (255.0 * i1.size) * 100
    return npcr, uaci

def run_sanity_check():
    img1 = cv2.imread("sample_images/mri/1 no.jpeg")
    img2 = cv2.imread("sample_images/mri/36 no.jpg")
    
    # NPCR/UACI require identical dimensions, so we crop to the minimum overlap
    min_h = min(img1.shape[0], img2.shape[0])
    min_w = min(img1.shape[1], img2.shape[1])
    
    c1 = img1[:min_h, :min_w]
    c2 = img2[:min_h, :min_w]
    
    npcr_val, uaci_val = npcr_uaci(c1, c2)
    print("==================================================")
    print("SANITY CHECK: NPCR/UACI ON UNRELATED IMAGES")
    print("==================================================")
    print("Images compared: '1 no.jpeg' vs '36 no.jpg' (cropped to matching overlap)")
    print(f"Calculated NPCR: {npcr_val:.4f}%")
    print(f"Calculated UACI: {uaci_val:.4f}%")

if __name__ == "__main__":
    run_sanity_check()
