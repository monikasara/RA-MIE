import numpy as np
from .chaotic_engine import generate_logistic_sequence

def get_permutation_indices(length, x0, mu):
    """
    Generates permutation indices using the sort-index method on a chaotic sequence.
    """
    chaotic_seq = generate_logistic_sequence(x0, mu, length)
    indices = np.argsort(chaotic_seq)
    return indices

def get_inverse_permutation_indices(indices):
    """
    Generates inverse permutation indices.
    """
    inv_indices = np.empty_like(indices)
    inv_indices[indices] = np.arange(len(indices))
    return inv_indices

def permute(image, x0, mu):
    """
    Permutes the pixels of an image.
    """
    original_shape = image.shape
    
    # Flatten the spatial dimensions (H * W), keep channels intact if present
    if len(original_shape) == 3:
        num_pixels = original_shape[0] * original_shape[1]
        flattened = image.reshape(num_pixels, original_shape[2])
    else:
        num_pixels = original_shape[0] * original_shape[1]
        flattened = image.reshape(num_pixels)
        
    indices = get_permutation_indices(num_pixels, x0, mu)
    
    permuted_flattened = flattened[indices]
    
    return permuted_flattened.reshape(original_shape)

def inverse_permute(image, x0, mu):
    """
    Restores the original pixels from a permuted image.
    """
    original_shape = image.shape
    
    if len(original_shape) == 3:
        num_pixels = original_shape[0] * original_shape[1]
        flattened = image.reshape(num_pixels, original_shape[2])
    else:
        num_pixels = original_shape[0] * original_shape[1]
        flattened = image.reshape(num_pixels)
        
    indices = get_permutation_indices(num_pixels, x0, mu)
    inv_indices = get_inverse_permutation_indices(indices)
    
    restored_flattened = flattened[inv_indices]
    
    return restored_flattened.reshape(original_shape)
