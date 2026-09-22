import numpy as np
import matplotlib.pyplot as plt
import io

def calculate_entropy(image):
    """Calculates the Shannon entropy of an image."""
    histogram, _ = np.histogram(image.ravel(), bins=256, range=(0, 256))
    histogram_length = sum(histogram)
    probabilities = [float(h) / histogram_length for h in histogram]
    entropy = -sum([p * np.log2(p) for p in probabilities if p != 0])
    return entropy

def calculate_chi_square(image):
    """Calculates the chi-square statistic of an image histogram."""
    histogram, _ = np.histogram(image.ravel(), bins=256, range=(0, 256))
    expected = image.size / 256.0
    chi_square = np.sum((histogram - expected)**2 / expected)
    return chi_square

def calculate_npcr(image1, image2):
    """Calculates the Number of Pixel Change Rate (NPCR) between two images."""
    if image1.shape != image2.shape:
        raise ValueError("Images must have the same shape.")
    
    diff = image1 != image2
    npcr = np.sum(diff) / image1.size * 100.0
    return npcr

def calculate_uaci(image1, image2):
    """Calculates the Unified Average Changing Intensity (UACI) between two images."""
    if image1.shape != image2.shape:
        raise ValueError("Images must have the same shape.")
    
    # Cast to float to avoid overflow
    img1 = image1.astype(np.float64)
    img2 = image2.astype(np.float64)
    
    uaci = np.sum(np.abs(img1 - img2)) / (255.0 * image1.size) * 100.0
    return uaci

def calculate_correlation(image, direction='horizontal', sample_size=3000):
    """
    Calculates the correlation coefficient of adjacent pixels.
    direction: 'horizontal', 'vertical', or 'diagonal'
    """
    if len(image.shape) == 3:
        # Convert to grayscale roughly for correlation metric
        img = np.mean(image, axis=2).astype(np.float64)
    else:
        img = image.astype(np.float64)
        
    h, w = img.shape
    
    if direction == 'horizontal':
        x = img[:, :-1].ravel()
        y = img[:, 1:].ravel()
    elif direction == 'vertical':
        x = img[:-1, :].ravel()
        y = img[1:, :].ravel()
    elif direction == 'diagonal':
        x = img[:-1, :-1].ravel()
        y = img[1:, 1:].ravel()
    else:
        raise ValueError("Invalid direction.")
        
    # Sample randomly to speed up
    if len(x) > sample_size:
        indices = np.random.choice(len(x), sample_size, replace=False)
        x = x[indices]
        y = y[indices]
        
    mean_x = np.mean(x)
    mean_y = np.mean(y)
    
    numerator = np.sum((x - mean_x) * (y - mean_y))
    denominator = np.sqrt(np.sum((x - mean_x)**2) * np.sum((y - mean_y)**2))
    
    if denominator == 0:
        return 0.0
    return numerator / denominator

def plot_histogram(original, encrypted):
    """
    Generates a histogram comparison plot and returns it as a bytes buffer.
    """
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    
    axes[0].hist(np.asarray(original).ravel(), bins=256, range=(0, 256), color='blue', alpha=0.7)
    axes[0].set_title("Original Histogram")
    axes[0].set_xlabel("Pixel Value")
    axes[0].set_ylabel("Frequency")
    
    axes[1].hist(np.asarray(encrypted).ravel(), bins=256, range=(0, 256), color='red', alpha=0.7)
    axes[1].set_title("Encrypted Histogram")
    axes[1].set_xlabel("Pixel Value")
    axes[1].set_ylabel("Frequency")
    
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)
    return buf
