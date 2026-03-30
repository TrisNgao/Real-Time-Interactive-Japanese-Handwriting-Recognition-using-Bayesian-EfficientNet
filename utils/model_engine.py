import cv2
import numpy as np
import albumentations as A
from albumentations.pytorch import ToTensorV2
from pathlib import Path

BASE_DIR         = Path(__file__).parent.parent
MODEL_HIRA_PATH  = BASE_DIR / "model" / "japanese_char_model.pt"
MODEL_KANJI_PATH = BASE_DIR / "model" / "kanji_model.pt"
HIRA_NAMES_PATH  = BASE_DIR / "data"  / "class_names.json"
KANJI_NAMES_PATH = BASE_DIR / "data"  / "kanji_class_names.json"


class ModelEngine:
    def __init__(self):
        import torch
        self.torch  = torch
        self.device = torch.device('cpu')
        self.model_hira  = None
        self.model_kanji = None
        self.names_hira  = []
        self.names_kanji = []
        self.transform   = A.Compose([
            A.Resize(224, 224),
            A.Normalize(mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225]),
            ToTensorV2()
        ])
        self._load()

    def _load(self):
        import json
        torch = self.torch
        try:
            self.model_hira = torch.jit.load(
                str(MODEL_HIRA_PATH), map_location=self.device
            )
            self.model_hira.eval()
            with open(HIRA_NAMES_PATH, 'r', encoding='utf-8') as f:
                self.names_hira = json.load(f)
            print(f'✅ Hira/Kata model — {len(self.names_hira)} classes')
        except Exception as e:
            print(f'⚠️  Hira model: {e}')

        try:
            self.model_kanji = torch.jit.load(
                str(MODEL_KANJI_PATH), map_location=self.device
            )
            self.model_kanji.eval()
            with open(KANJI_NAMES_PATH, 'r', encoding='utf-8') as f:
                self.names_kanji = json.load(f)
            print(f'✅ Kanji model — {len(self.names_kanji)} classes')
        except Exception as e:
            print(f'⚠️  Kanji model: {e}')

    def apply_clahe(self, gray, clip=2.0, grid=(4, 4)):
        clahe = cv2.createCLAHE(clipLimit=clip, tileGridSize=grid)
        return clahe.apply(gray)

    def get_char_type(self, char):
        code = ord(char)
        if 0x3041 <= code <= 0x3096: return 'hiragana'
        if 0x30A1 <= code <= 0x30F6: return 'katakana'
        if 0x4E00 <= code <= 0x9FFF: return 'kanji'
        return 'unknown'

    def _preprocess(self, frame_bgr):
        """
        Xử lý ảnh trước khi predict
        Tự động detect màu mực (đen/đỏ/xanh) trên nền trắng
        → convert về nền trắng chữ đen chuẩn
        """
        hsv      = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        gray_raw = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

        # Mask mực đỏ
        mask_red = cv2.bitwise_or(
            cv2.inRange(hsv, (0,   50, 50), (10,  255, 255)),
            cv2.inRange(hsv, (160, 50, 50), (180, 255, 255))
        )

        # Mask mực xanh dương
        mask_blue = cv2.inRange(hsv, (100, 50, 50), (130, 255, 255))

        # Mask mực xanh lá
        mask_green = cv2.inRange(hsv, (40, 50, 50), (80, 255, 255))

        # Mask mực tối (đen/navy)
        _, mask_dark = cv2.threshold(gray_raw, 80, 255, cv2.THRESH_BINARY_INV)

        # Chọn mask có nhiều pixel nhất = màu mực đang dùng
        masks = {
            'red'  : mask_red,
            'blue' : mask_blue,
            'green': mask_green,
            'dark' : mask_dark,
        }
        best_key  = max(masks, key=lambda k: cv2.countNonZero(masks[k]))
        best_mask = masks[best_key]

        # Tạo ảnh chuẩn: nền trắng, chữ đen
        result              = np.ones_like(gray_raw) * 255
        result[best_mask > 0] = 0

        # CLAHE tăng contrast
        result = self.apply_clahe(result, clip=2.0, grid=(4, 4))

        return result

    def predict(self, frame_bgr, target_char=None, top_k=3):
        torch     = self.torch
        char_type = self.get_char_type(target_char) if target_char else 'kanji'

        if char_type in ('hiragana', 'katakana') and self.model_hira:
            model       = self.model_hira
            class_names = self.names_hira
        elif char_type == 'kanji' and self.model_kanji:
            model       = self.model_kanji
            class_names = self.names_kanji
        else:
            print(f'⚠️  Không có model cho: {char_type}')
            return []

        try:
            # Preprocess — tự detect màu mực
            gray   = self._preprocess(frame_bgr)
            img    = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
            tensor = self.transform(image=img)['image'].unsqueeze(0)

            with torch.no_grad():
                probs = torch.softmax(model(tensor), dim=1)[0]

            top_probs, top_idxs = probs.topk(min(top_k, len(class_names)))
            return [
                {'char': class_names[idx.item()], 'prob': prob.item()}
                for prob, idx in zip(top_probs, top_idxs)
            ]
        except Exception as e:
            print(f'Predict error: {e}')
            return []
