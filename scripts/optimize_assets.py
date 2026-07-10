import os
import glob
try:
    from PIL import Image
except ImportError:
    print("Please install Pillow: pip install Pillow")
    exit(1)

def optimize_images(directory="assets"):
    if not os.path.exists(directory):
        print(f"Directory {directory} not found. Skipping.")
        return

    print(f"Optimizing images in {directory}...")
    
    # Find all png and jpg images
    images = glob.glob(f"{directory}/**/*.png", recursive=True) + glob.glob(f"{directory}/**/*.jpg", recursive=True)
    
    for img_path in images:
        try:
            with Image.open(img_path) as img:
                # Convert to WEBP
                webp_path = os.path.splitext(img_path)[0] + ".webp"
                img.save(webp_path, "webp", optimize=True, quality=80)
                print(f"Optimized: {img_path} -> {webp_path}")
                # Optionally, you could remove the original file here to save space
                # os.remove(img_path)
        except Exception as e:
            print(f"Failed to optimize {img_path}: {e}")

if __name__ == "__main__":
    optimize_images()
    optimize_images("frontend-vue/src/assets")
    print("Optimization complete!")
