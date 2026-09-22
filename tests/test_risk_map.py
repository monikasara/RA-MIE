import numpy as np
import os
from src.risk_analysis.risk_map import generate_risk_map

def test_generate_risk_map_dimensions():
    # Odd dimension image to test boundary splitting logic
    image = np.random.randint(0, 256, (105, 105, 3), dtype=np.uint8)
    
    result = generate_risk_map(image, grid_size=(4, 4))
    
    score_matrix = result['score_matrix']
    level_matrix = result['level_matrix']
    risk_map_image = result['risk_map_image']
    
    assert score_matrix.shape == (4, 4)
    assert level_matrix.shape == (4, 4)
    assert risk_map_image.shape == (105, 105)
    
    # Ensure scores are within bounds
    assert np.all((score_matrix >= 0.0) & (score_matrix <= 1.0))
    
    # Ensure levels are correct strings
    for row in level_matrix:
        for level in row:
            assert level in ["LOW", "MEDIUM", "HIGH"]

def test_generate_risk_map_save(tmpdir):
    image = np.random.randint(0, 256, (100, 100), dtype=np.uint8)
    save_dir = str(tmpdir.mkdir("results"))
    
    generate_risk_map(image, grid_size=(2, 2), save_dir=save_dir)
    
    # Check if the map image was saved
    saved_file = os.path.join(save_dir, "risk_map.png")
    assert os.path.exists(saved_file)
