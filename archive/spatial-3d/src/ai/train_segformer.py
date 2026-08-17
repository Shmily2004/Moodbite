import torch
from torch import nn
from transformers import SegformerForSemanticSegmentation, SegformerConfig
from torch.utils.data import DataLoader, Dataset
from pathlib import Path
import logging
import sys

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[3]))
from src.infrastructure.config.config_service import config_service

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class FloorplanDataset(Dataset):
    """Placeholder dataset for Floorplan Segmentation"""
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        # In a real scenario, we would load image paths and mask paths here
        self.images = list(self.data_dir.glob("*.jpg"))
        
    def __len__(self):
        return len(self.images)
    
    def __getitem__(self, idx):
        # Placeholder for actual image loading and preprocessing
        return {
            "pixel_values": torch.randn(3, 512, 512),
            "labels": torch.randint(0, 2, (512, 512))
        }

def train_segformer():
    """
    Huấn luyện SegFormer (MIT-B3) cho Wall Segmentation.
    """
    # 1. Load Configuration
    iou_threshold = config_service.get('ai.segformer.iou_threshold', 0.85)
    input_size = config_service.get('ai.segformer.input_size', [512, 512])
    
    logger.info(f"Initializing SegFormer with config: IoU Threshold={iou_threshold}, Size={input_size}")

    # 2. Cấu hình Model
    id2label = {0: "background", 1: "wall"}
    label2id = {"background": 0, "wall": 1}
    
    config = SegformerConfig.from_pretrained(
        "nvidia/mit-b3", 
        num_labels=2,
        id2label=id2label,
        label2id=label2id
    )
    
    # Check for GPU
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")

    try:
        model = SegformerForSemanticSegmentation.from_pretrained("nvidia/mit-b3", config=config)
        model.to(device)
    except Exception as e:
        logger.error(f"Failed to initialize model: {e}")
        return

    # 3. Optimizer & Loss
    optimizer = torch.optim.AdamW(model.parameters(), lr=6e-5)
    
    # 4. Dataset & DataLoader (Mock for Phase 1)
    dataset = FloorplanDataset(data_dir="data_pipeline/data_cleaned")
    dataloader = DataLoader(dataset, batch_size=2, shuffle=True)

    # 5. Training Loop
    logger.info("Starting training SegFormer...")
    
    model.train()
    # Demo loop for 1 epoch if data exists
    if len(dataset) > 0:
        for epoch in range(1):
            for i, batch in enumerate(dataloader):
                pixel_values = batch['pixel_values'].to(device)
                labels = batch['labels'].to(device)
                
                outputs = model(pixel_values=pixel_values, labels=labels)
                loss = outputs.loss
                
                loss.backward()
                optimizer.step()
                optimizer.zero_grad()
                
                if i % 10 == 0:
                    logger.info(f"Epoch 0, Batch {i}, Loss: {loss.item():.4f}")
    else:
        logger.warning("No data found in data_pipeline/data_cleaned. Training script verified but skipped execution.")

    # 6. Save Checkpoint
    output_dir = Path("outputs/segformer")
    output_dir.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), output_dir / "segformer_wall_latest.pth")
    logger.info(f"Model checkpoint saved to {output_dir}")

if __name__ == "__main__":
    train_segformer()
