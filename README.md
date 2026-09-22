# ChaosCrypt

ChaosCrypt is a Python-based image encryption system that leverages chaos theory (specifically the logistic map) to securely encrypt images. It supports both full-image encryption and Region-of-Interest (ROI) face-selective encryption.

## Features
- **Chaotic Engine**: Uses a logistic map to generate pseudorandom sequences for permutation and diffusion.
- **Plaintext-dependent Key Generation**: The encryption keys depend on both the user's passphrase and the plaintext image, protecting against chosen-plaintext attacks.
- **Permutation Module**: Scrambles pixel locations globally using the sort-index method.
- **Diffusion Module**: Alters pixel values using a CBC-style XOR operation with the chaotic keystream, ensuring a strong avalanche effect.
- **Face-Selective Encryption**: Detects faces using OpenCV Haar Cascades and exclusively encrypts the detected ROIs while leaving the background untouched.
- **Security Metrics Analysis**: Built-in calculations for Shannon Entropy, NPCR, UACI, and Pixel Correlation, alongside histogram visualizations.
- **Streamlit GUI**: A sleek, user-friendly interface to perform encryption, decryption, and view security metrics in real time.

## Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: OpenCV < 5 is required for Haar Cascade support)*

2. **Run the Streamlit App:**
   ```bash
   streamlit run src/app.py
   ```

3. **Run the Test Suite:**
   ```bash
   pytest tests/
   ```

## Encryption Algorithm Overview

1. **Key Generation**: 
   - SHA-256 hash of the passphrase XORed with the SHA-256 hash of the original image bytes.
   - The combined 256-bit hash is split into 4 chunks to seed the initial value ($x_0$) and control parameter ($\mu$) for the permutation and diffusion logistic maps.
2. **Permutation**: 
   - A logistic sequence is generated and sorted. The resulting sorted indices map original pixel positions to their new scrambled locations.
3. **Diffusion**:
   - A second logistic sequence is converted to byte values (0-255).
   - Each permuted pixel is XORed with the keystream byte and the previously encrypted pixel value (Cipher Block Chaining style), ensuring that a 1-bit change in the plaintext cascades through the ciphertext.

## Risk-Adaptive Encryption

- **Risk Analysis**: Generates a risk map dividing the image into a configurable grid.
- **Classification**: Regions are classified as LOW, MEDIUM, or HIGH risk based on diagnostic importance, uncertainty, and security threat.
- **Adaptive Encryption**: Encryption strength is selected according to risk (LOW=1 round, MEDIUM=2 rounds, HIGH=3 rounds).
- **Key Generation**: SHA-256 derives the key from the user's password, original image information, and risk-map information, ensuring that a change in any input produces a completely different key.
- **Core Cipher**: Chaotic permutation and diffusion provide the underlying encryption for each round.

> **Note**: This implementation is a research prototype and has not been clinically validated.

## Security Metrics Achieved

On sample images, ChaosCrypt demonstrates robust security metrics typical of strong chaos-based systems:
- **Shannon Entropy**: ~7.99 bits (ideal is 8.0), indicating uniform pixel distribution.
- **NPCR (Number of Pixel Change Rate)**: > 99.5%, meaning almost all pixels change value when one bit of the original image is altered.
- **UACI (Unified Average Changing Intensity)**: ~33.4%, meaning the average intensity change between the ciphertexts of two slightly different plaintexts is ideal.
- **Correlation**: Close to 0.0, destroying the high correlation found in natural images.
