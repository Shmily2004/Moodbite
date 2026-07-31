import torch
from torch import nn
from transformers import SegformerForSemanticSegmentation, SegformerConfig
from torch.utils.data import DataLoader

def train_segformer():
    """
    Khung huấn luyện SegFormer (MIT-B3) cho Wall Segmentation.
    """
    # 1. Cấu hình Model
    # Sử dụng pretrained MIT-B3 từ HuggingFace
    id2label = {0: "background", 1: "wall"}
    label2id = {"background": 0, "wall": 1}
    
    config = SegformerConfig.from_pretrained(
        "nvidia/mit-b3", 
        num_labels=2,
        id2label=id2label,
        label2id=label2id
    )
    model = SegformerForSemanticSegmentation.from_pretrained("nvidia/mit-b3", config=config)

    # 2. Optimizer & Loss
    optimizer = torch.optim.AdamW(model.parameters(), lr=6e-5)
    criterion = nn.CrossEntropyLoss()

    # 3. Training Loop (Skeleton)
    print("Starting training SegFormer...")
    # for epoch in range(epochs):
    #     for batch in dataloader:
    #         outputs = model(pixel_values=batch['pixel_values'], labels=batch['labels'])
    #         loss = outputs.loss
    #         loss.backward()
    #         optimizer.step()
    #         optimizer.zero_grad()
    
    print("Training script initialized (Stub).")

if __name__ == "__main__":
    train_segformer()
