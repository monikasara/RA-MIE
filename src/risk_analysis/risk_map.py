import numpy as np
import cv2
import os
from .risk_score import calculate_risk_score
from .region_classifier import classify_risk_score

def generate_risk_map(image, grid_size=(4, 4), save_dir=None):
    """
    Divides the image into a grid, calculates risk scores for each region,
    and creates a risk map resized to the original image dimensions.
    
    Args:
        image: Original numpy array image.
        grid_size: Tuple of (rows, cols).
        save_dir: Optional directory to save the generated risk map image.
        
    Returns:
        dict: containing:
            - 'score_matrix': 2D numpy array of float risk scores
            - 'level_matrix': 2D numpy array (object) of string risk levels
            - 'risk_map_image': 2D numpy array (float) scaled to image dimensions
    """
    h, w = image.shape[:2]
    rows, cols = grid_size
    
    # Calculate region dimensions
    # Using np.linspace to handle non-divisible dimensions cleanly
    y_splits = np.linspace(0, h, rows + 1, dtype=int)
    x_splits = np.linspace(0, w, cols + 1, dtype=int)
    
    score_matrix = np.zeros((rows, cols), dtype=np.float64)
    level_matrix = np.empty((rows, cols), dtype=object)
    risk_map_image = np.zeros((h, w), dtype=np.float64)
    
    for i in range(rows):
        for j in range(cols):
            y_start, y_end = y_splits[i], y_splits[i+1]
            x_start, x_end = x_splits[j], x_splits[j+1]
            
            # Extract region
            region = image[y_start:y_end, x_start:x_end]
            
            # If region is too small, skip (shouldn't happen with normal grids)
            if region.size == 0:
                continue
                
            score = calculate_risk_score(region)
            level = classify_risk_score(score)
            
            score_matrix[i, j] = score
            level_matrix[i, j] = level
            risk_map_image[y_start:y_end, x_start:x_end] = score
            
    if save_dir is not None:
        os.makedirs(save_dir, exist_ok=True)
        # Convert risk map to visualizable 8-bit image (0-255)
        visual_map = (risk_map_image * 255).astype(np.uint8)
        # Apply a colormap for better visualization
        colored_map = cv2.applyColorMap(visual_map, cv2.COLORMAP_JET)
        
        save_path = os.path.join(save_dir, "risk_map.png")
        cv2.imwrite(save_path, colored_map)
        
    return {
        'score_matrix': score_matrix,
        'level_matrix': level_matrix,
        'risk_map_image': risk_map_image,
        'y_splits': y_splits,
        'x_splits': x_splits
    }
