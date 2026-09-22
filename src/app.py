import streamlit as st
import numpy as np
from PIL import Image
from cipher import encrypt, encrypt_selective, decrypt
from metrics import calculate_entropy, calculate_npcr, calculate_uaci, calculate_correlation, plot_histogram

st.set_page_config(page_title="ChaosCrypt", layout="wide")

st.title("ChaosCrypt: Chaotic Image Encryption")

# Sidebar for inputs
with st.sidebar:
    st.header("Settings")
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
    passphrase = st.text_input("Passphrase", type="password")
    encryption_mode = st.radio("Encryption Mode", ["Full Encryption", "Face-Selective Encryption"])
    process_btn = st.button("Encrypt & Analyze")

if uploaded_file is not None and process_btn:
    if not passphrase:
        st.error("Please enter a passphrase.")
    else:
        # Read original image
        original_pil = Image.open(uploaded_file).convert("RGB")
        original_image = np.array(original_pil)
        
        with st.spinner("Processing..."):
            # 1. Encrypt
            if encryption_mode == "Full Encryption":
                encrypted_image = encrypt(original_image, passphrase)
            else:
                encrypted_image = encrypt_selective(original_image, passphrase)
            
            # 2. Decrypt
            decrypted_image = decrypt(encrypted_image, passphrase)
            
            # Layout images
            st.subheader("Visual Results")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.image(original_image, caption="Original Image", use_container_width=True)
            with col2:
                # Need to convert encrypted_image to standard array for display
                st.image(np.asarray(encrypted_image), caption="Encrypted Image", use_container_width=True)
            with col3:
                st.image(decrypted_image, caption="Decrypted Image", use_container_width=True)
            
            st.divider()
            
            # Metrics
            st.subheader("Security Metrics")
            
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            
            # Entropy
            entropy_orig = calculate_entropy(original_image)
            entropy_enc = calculate_entropy(np.asarray(encrypted_image))
            col_m1.metric("Shannon Entropy", f"{entropy_enc:.4f} bits", f"{entropy_enc - entropy_orig:.4f} from original")
            
            # NPCR
            npcr = calculate_npcr(original_image, np.asarray(encrypted_image))
            col_m2.metric("NPCR", f"{npcr:.4f}%")
            
            # UACI
            uaci = calculate_uaci(original_image, np.asarray(encrypted_image))
            col_m3.metric("UACI", f"{uaci:.4f}%")
            
            # Correlation
            corr_orig = calculate_correlation(original_image, 'horizontal')
            corr_enc = calculate_correlation(np.asarray(encrypted_image), 'horizontal')
            col_m4.metric("Correlation (Horizontal)", f"{corr_enc:.4f}", f"{corr_enc - corr_orig:.4f} from original", delta_color="inverse")
            
            # Histograms
            st.subheader("Histogram Analysis")
            hist_buf = plot_histogram(original_image, np.asarray(encrypted_image))
            st.image(hist_buf, use_container_width=True)
            
        st.success("Analysis complete!")
