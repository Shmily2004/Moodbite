from ultralytics import YOLO

def train_yolo():
    """
    Khung huấn luyện YOLOv11 cho Object Detection (Furniture & Openings).
    """
    # 1. Khởi tạo model (YOLOv11 Nano cho tốc độ nhanh)
    model = YOLO('yolo11n.pt') 

    # 2. Huấn luyện
    # data: đường dẫn tới file data.yaml (định dạng YOLO)
    # epochs: số lượt huấn luyện
    # imgsz: kích thước ảnh đầu vào
    
    print("Starting training YOLOv11...")
    # results = model.train(
    #     data='data_pipeline/data.yaml', 
    #     epochs=100, 
    #     imgsz=640, 
    #     device='0' # Sử dụng GPU 0
    # )
    
    print("YOLO Training script initialized (Stub).")

if __name__ == "__main__":
    train_yolo()
