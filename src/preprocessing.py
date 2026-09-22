import cv2
import numpy as np

def preprocess_image(img_rgb, target_size=(512, 512)):
    """
    Preprocesses the input image before encryption:
    1. Resizes with aspect-ratio preserving padding to target_size.
    2. Applies light Gaussian denoise.
    3. Applies CLAHE for clarity enhancement.
    """
    # 1. Resize with Padding
    h, w = img_rgb.shape[:2]
    tw, th = target_size
    scale = min(tw/w, th/h)
    new_w, new_h = int(w * scale), int(h * scale)
    
    resized = cv2.resize(img_rgb, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    pad_w = tw - new_w
    pad_h = th - new_h
    top, bottom = pad_h // 2, pad_h - (pad_h // 2)
    left, right = pad_w // 2, pad_w - (pad_w // 2)
    
    color = [0, 0, 0] # black padding
    padded = cv2.copyMakeBorder(resized, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
    
    # 2. Light Gaussian Denoise
    denoised = cv2.GaussianBlur(padded, (3, 3), 0)
    
    # 3. CLAHE (Contrast Limited Adaptive Histogram Equalization)
    # CLAHE is applied on the L channel of LAB color space to preserve colors
    lab = cv2.cvtColor(denoised, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    cl = clahe.apply(l)
    
    limg = cv2.merge((cl, a, b))
    enhanced = cv2.cvtColor(limg, cv2.COLOR_LAB2RGB)
    
    return enhanced
