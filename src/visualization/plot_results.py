import pandas as pd
import matplotlib.pyplot as plt
import os

def generate_graphs():
    csv_path = "results/evaluation_results.csv"
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found. Run evaluation.py first.")
        return

    df = pd.read_csv(csv_path)
    
    if df.empty:
        print("Error: No data in evaluation_results.csv to plot.")
        return
        
    os.makedirs("results/graphs", exist_ok=True)
    
    metrics = {
        "Entropy": "entropy_comparison.png",
        "NPCR": "npcr_comparison.png",
        "UACI": "uaci_comparison.png",
        "Horizontal_Correlation": "correlation_comparison.png", # Grouping correlations might be better, but prompt asks for specific graphs or one? "correlation_comparison.png" 
        "Encryption_Time": "encryption_time_comparison.png",
        "Decryption_Time": "decryption_time_comparison.png"
    }

    # Group by method to get averages across all images
    avg_df = df.groupby('Method').mean(numeric_only=True).reset_index()
    
    methods = avg_df['Method']

    # 1. Entropy
    plt.figure(figsize=(8, 6))
    plt.bar(methods, avg_df['Entropy'], color=['#3498db', '#2ecc71', '#e74c3c'])
    plt.title('Average Shannon Entropy Comparison')
    plt.ylabel('Entropy (bits)')
    plt.ylim(7.5, 8.0) # Zoom in to see differences near 8.0
    plt.savefig("results/graphs/entropy_comparison.png")
    plt.close()

    # 2. NPCR
    plt.figure(figsize=(8, 6))
    plt.bar(methods, avg_df['NPCR'], color=['#3498db', '#2ecc71', '#e74c3c'])
    plt.title('Average NPCR Comparison')
    plt.ylabel('NPCR (%)')
    plt.ylim(99.0, 100.0)
    plt.savefig("results/graphs/npcr_comparison.png")
    plt.close()

    # 3. UACI
    plt.figure(figsize=(8, 6))
    plt.bar(methods, avg_df['UACI'], color=['#3498db', '#2ecc71', '#e74c3c'])
    plt.title('Average UACI Comparison')
    plt.ylabel('UACI (%)')
    plt.ylim(30.0, 35.0)
    plt.savefig("results/graphs/uaci_comparison.png")
    plt.close()
    
    # 4. Correlation (Grouped bar chart for H, V, D)
    plt.figure(figsize=(10, 6))
    bar_width = 0.25
    r1 = np.arange(len(methods))
    r2 = [x + bar_width for x in r1]
    r3 = [x + bar_width for x in r2]
    
    plt.bar(r1, avg_df['Horizontal_Correlation'], color='#3498db', width=bar_width, edgecolor='white', label='Horizontal')
    plt.bar(r2, avg_df['Vertical_Correlation'], color='#2ecc71', width=bar_width, edgecolor='white', label='Vertical')
    plt.bar(r3, avg_df['Diagonal_Correlation'], color='#e74c3c', width=bar_width, edgecolor='white', label='Diagonal')
    
    plt.title('Average Pixel Correlation Comparison')
    plt.ylabel('Correlation Coefficient')
    plt.xticks([r + bar_width for r in range(len(methods))], methods)
    plt.legend()
    plt.savefig("results/graphs/correlation_comparison.png")
    plt.close()

    # 5. Encryption Time
    plt.figure(figsize=(8, 6))
    plt.bar(methods, avg_df['Encryption_Time'], color=['#3498db', '#2ecc71', '#e74c3c'])
    plt.title('Average Encryption Time Comparison')
    plt.ylabel('Time (seconds)')
    plt.savefig("results/graphs/encryption_time_comparison.png")
    plt.close()
    
    # 6. Decryption Time
    plt.figure(figsize=(8, 6))
    plt.bar(methods, avg_df['Decryption_Time'], color=['#3498db', '#2ecc71', '#e74c3c'])
    plt.title('Average Decryption Time Comparison')
    plt.ylabel('Time (seconds)')
    plt.savefig("results/graphs/decryption_time_comparison.png")
    plt.close()

    print("Graphs successfully generated in results/graphs/")

def generate_scatter_plots():
    import cv2
    import numpy as np
    
    # Use chest_xray_01.jpg as representative image
    orig_path = "sample_images/xray/chest_xray_01.jpg"
    enc_path = "results/encrypted_images/chest_xray_01_RA-MIE.png"
    
    if not os.path.exists(orig_path) or not os.path.exists(enc_path):
        print("Cannot generate scatter plots: representative image not found.")
        return
        
    def plot_scatter(img_path, title, save_path):
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if img is None: return
        
        # Sample 1000 adjacent horizontal pixel pairs
        h, w = img.shape
        x = np.random.randint(0, w - 1, 1000)
        y = np.random.randint(0, h, 1000)
        
        px1 = img[y, x]
        px2 = img[y, x + 1]
        
        plt.figure(figsize=(6, 6))
        plt.scatter(px1, px2, s=2, alpha=0.5, c='blue' if 'Plaintext' in title else 'red')
        plt.title(title)
        plt.xlabel("Pixel (x, y)")
        plt.ylabel("Pixel (x+1, y)")
        plt.xlim(0, 255)
        plt.ylim(0, 255)
        plt.grid(True, alpha=0.3)
        plt.savefig(save_path)
        plt.close()

    os.makedirs("results/graphs", exist_ok=True)
    plot_scatter(orig_path, "Correlation Scatter (Plaintext)", "results/graphs/correlation_scatter_plaintext.png")
    plot_scatter(enc_path, "Correlation Scatter (RA-MIE Ciphertext)", "results/graphs/correlation_scatter_ciphertext.png")
    print("Scatter plots generated.")

if __name__ == "__main__":
    import numpy as np
    generate_graphs()
    generate_scatter_plots()
