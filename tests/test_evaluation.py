import os
import pytest
from src.evaluation import find_medical_images

def test_find_medical_images(tmpdir):
    # Create fake directory structure
    base_dir = str(tmpdir.mkdir("sample_images"))
    os.makedirs(os.path.join(base_dir, "mri"))
    os.makedirs(os.path.join(base_dir, "xray"))
    os.makedirs(os.path.join(base_dir, "ct"))
    
    # Create fake files
    with open(os.path.join(base_dir, "mri", "brain.png"), 'w') as f: f.write("test")
    with open(os.path.join(base_dir, "xray", "chest.jpg"), 'w') as f: f.write("test")
    with open(os.path.join(base_dir, "ct", "not_image.txt"), 'w') as f: f.write("test")
    
    images = find_medical_images(base_dir=base_dir)
    
    assert len(images) == 2
    assert any("brain.png" in p for p in images)
    assert any("chest.jpg" in p for p in images)
    assert not any("not_image.txt" in p for p in images)
