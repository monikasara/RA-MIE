import numpy as np
from .chaotic_engine import generate_logistic_sequence

def diffuse(image, x0, mu):
    """
    Applies diffusion using CBC style XOR with a chaotic keystream.
    """
    original_shape = image.shape
    flattened = image.ravel()
    num_bytes = len(flattened)
    
    # Generate chaotic sequence
    chaotic_seq = generate_logistic_sequence(x0, mu, num_bytes)
    
    # Convert to byte values (0-255)
    # chaotic_seq is in (0, 1), multiply by 256 and cast to uint8
    keystream = np.floor(chaotic_seq * 256).astype(np.uint8)
    
    # P(i) XOR K(i)
    temp = np.bitwise_xor(flattened, keystream)
    
    # Cumulative XOR for CBC style: C(i) = temp(i) XOR C(i-1)
    diffused = np.bitwise_xor.accumulate(temp)
    
    return diffused.reshape(original_shape)

def inverse_diffuse(image, x0, mu):
    """
    Reverses the diffusion process.
    """
    original_shape = image.shape
    flattened = image.ravel()
    num_bytes = len(flattened)
    
    chaotic_seq = generate_logistic_sequence(x0, mu, num_bytes)
    keystream = np.floor(chaotic_seq * 256).astype(np.uint8)
    
    # C(i-1)
    c_prev = np.empty_like(flattened)
    c_prev[0] = 0
    c_prev[1:] = flattened[:-1]
    
    # P(i) = C(i) XOR K(i) XOR C(i-1)
    restored = np.bitwise_xor(flattened, keystream)
    restored = np.bitwise_xor(restored, c_prev)
    
    return restored.reshape(original_shape)
