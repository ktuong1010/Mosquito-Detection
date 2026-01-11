import sys
from pathlib import Path
import shutil
import logging

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def prepare_no_mosquito_dataset():
    dataset_dir = PROJECT_ROOT / "dataset" / "processed_edgeimpulse"
    train_dir = dataset_dir / "train"
    val_dir = dataset_dir / "val"
    
    no_mosquito_train = train_dir / "No_Mosquito"
    no_mosquito_val = val_dir / "No_Mosquito"
    
    # Create directories
    no_mosquito_train.mkdir(parents=True, exist_ok=True)
    no_mosquito_val.mkdir(parents=True, exist_ok=True)
    
    logger.info("=" * 70)
    logger.info("No_Mosquito Dataset Preparation")
    logger.info("=" * 70)
    logger.info(f"Created directories:")
    logger.info(f"  Train: {no_mosquito_train}")
    logger.info(f"  Val: {no_mosquito_val}")
    logger.info()
    logger.info("INSTRUCTIONS:")
    logger.info("=" * 70)
    logger.info("1. Collect images WITHOUT mosquitoes:")
    logger.info("   - Empty surfaces (tables, walls, floors)")
    logger.info("   - Background scenes (outdoor, indoor)")
    logger.info("   - Other insects (flies, bees, etc.) - NOT mosquitoes")
    logger.info("   - Random objects/textures")
    logger.info()
    logger.info("2. Recommended dataset size:")
    logger.info("   - Train: 500-1000 images (similar to Aedes/Culex)")
    logger.info("   - Val: 100-200 images")
    logger.info()
    logger.info("3. Copy images to:")
    logger.info(f"   Train: {no_mosquito_train}")
    logger.info(f"   Val: {no_mosquito_val}")
    logger.info()
    logger.info("4. Image format: JPG, PNG (will be converted during training)")
    logger.info()
    logger.info("5. After adding images, run training script:")
    logger.info("   python scripts/train_mobilenetv2.py")
    logger.info("=" * 70)
    
    # Check if there are already images
    train_images = list(no_mosquito_train.glob("*.jpg")) + list(no_mosquito_train.glob("*.png"))
    val_images = list(no_mosquito_val.glob("*.jpg")) + list(no_mosquito_val.glob("*.png"))
    
    if train_images or val_images:
        logger.info()
        logger.info(f"Current status:")
        logger.info(f"  Train images: {len(train_images)}")
        logger.info(f"  Val images: {len(val_images)}")
    else:
        logger.info()
        logger.info("No images found yet. Please add images to the directories above.")


if __name__ == "__main__":
    prepare_no_mosquito_dataset()

