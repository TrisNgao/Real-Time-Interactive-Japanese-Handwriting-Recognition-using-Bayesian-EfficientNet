import cv2
import time
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal


class WebcamThread(QThread):
    frame_ready = pyqtSignal(np.ndarray)
    result_ready = pyqtSignal(list)
    error_ready = pyqtSignal(str)

    def __init__(self, engine, target_char=None, cam_id=0):
        super().__init__()
        self.engine = engine
        self.target_char = target_char
        self.cam_id = int(cam_id)   # thường 0 = cam laptop, 1 = cam ngoài
        self.running = True
        self.cap = None

    def set_target(self, char):
        self.target_char = char

    def set_camera(self, cam_id):
        self.cam_id = int(cam_id)

    def _open_camera(self):
        """
        Ưu tiên mở webcam ngoài trên Windows bằng các backend phù hợp.
        """
        backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]

        for backend in backends:
            cap = cv2.VideoCapture(self.cam_id, backend)
            if not cap.isOpened():
                cap.release()
                continue

            # Thiết lập độ phân giải
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

            # Warm-up camera
            ok_count = 0
            for _ in range(15):
                ret, _ = cap.read()
                if ret:
                    ok_count += 1
                time.sleep(0.03)

            if ok_count > 0:
                self.cap = cap
                return True

            cap.release()

        return False

    def run(self):
        if not self._open_camera():
            self.error_ready.emit(
                f"Không mở được camera ID = {self.cam_id}. "
                f"Hãy thử cam_id = 0, 1, 2..."
            )
            return

        last_bbox = None
        stable_start = None
        STABLE_TIME = 0.5
        last_results = []

        while self.running:
            if self.cap is None or not self.cap.isOpened():
                break

            ret, frame = self.cap.read()
            if not ret or frame is None:
                self.msleep(33)
                continue

            bbox = self._detect(frame)
            display = frame.copy()

            if bbox:
                x, y, w, h = bbox

                if last_bbox is not None:
                    x2, y2, w2, h2 = last_bbox
                    diff = abs(x - x2) + abs(y - y2) + abs(w - w2) + abs(h - h2)

                    if diff < 50:
                        if stable_start is None:
                            stable_start = time.time()
                        elif time.time() - stable_start >= STABLE_TIME:
                            roi = frame[y:y + h, x:x + w]
                            results = self.engine.predict(roi, self.target_char)

                            if results:
                                last_results = results
                                self.result_ready.emit(results)
                    else:
                        stable_start = None
                        last_results = []
                else:
                    stable_start = None
                    last_results = []

                last_bbox = bbox

                # Vẽ khung
                color = (78, 205, 196) if last_results else (108, 99, 255)
                cv2.rectangle(display, (x, y), (x + w, y + h), color, 2)

                # Progress bar debounce
                if stable_start is not None:
                    prog = min((time.time() - stable_start) / STABLE_TIME, 1.0)
                    bar_w = int(w * prog)
                    cv2.rectangle(
                        display,
                        (x, y + h + 3),
                        (x + bar_w, y + h + 8),
                        (245, 200, 66),
                        -1
                    )
            else:
                last_bbox = None
                stable_start = None
                last_results = []

            self.frame_ready.emit(display)
            self.msleep(33)

        if self.cap:
            self.cap.release()
            self.cap = None

    def _detect(self, frame, padding=60, min_area=2000):
        """
        Detect vùng cần nhận diện với CLAHE để giảm ảnh hưởng của điểm sáng/chói.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame_h, frame_w = gray.shape

        # Cắt biên để tránh noise sát mép
        margin = 50
        roi_gray = gray[margin:frame_h - margin, margin:frame_w - margin]

        if roi_gray.size == 0:
            return None

        roi_h, roi_w = roi_gray.shape

        # 1) Giảm cháy sáng / glare
        # Giới hạn pixel sáng quá mức để tránh vùng trắng bị bệt
        roi_gray = np.clip(roi_gray, 0, 200).astype(np.uint8)

        # 2) CLAHE để cân bằng sáng cục bộ
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(roi_gray)

        # 3) Blur nhẹ để giảm nhiễu
        blurred = cv2.GaussianBlur(enhanced, (5, 5), 0)

        # 4) Threshold kép để ổn định hơn trong điều kiện sáng không đều
        _, thresh_otsu = cv2.threshold(
            blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )

        thresh_adaptive = cv2.adaptiveThreshold(
            blurred,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            31,
            5
        )

        thresh = cv2.bitwise_and(thresh_otsu, thresh_adaptive)

        # 5) Morphology close để nối vùng
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        # Có thể mở nhẹ để giảm chấm nhiễu
        kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel_open)

        # 6) Tìm contour
        contours, _ = cv2.findContours(
            cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            return None

        valid = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_area:
                continue

            x, y, w, h = cv2.boundingRect(cnt)

            # Bỏ contour quá sát mép ROI
            if x < 10 or y < 10:
                continue
            if x + w > roi_w - 10 or y + h > roi_h - 10:
                continue

            # Tỷ lệ bbox hợp lý
            ratio = w / h if h > 0 else 0
            if ratio < 0.2 or ratio > 4.5:
                continue

            # Bỏ contour quá lớn
            if area > roi_w * roi_h * 0.5:
                continue

            valid.append(cnt)

        if not valid:
            return None

        # 7) Gộp tất cả contour hợp lệ thành 1 bbox lớn
        all_x, all_y, all_x2, all_y2 = [], [], [], []
        for cnt in valid:
            x, y, w, h = cv2.boundingRect(cnt)
            all_x.append(x)
            all_y.append(y)
            all_x2.append(x + w)
            all_y2.append(y + h)

        x = min(all_x) + margin
        y = min(all_y) + margin
        x2 = max(all_x2) + margin
        y2 = max(all_y2) + margin

        # Nới bbox
        x = max(0, x - padding)
        y = max(0, y - padding)
        x2 = min(frame_w, x2 + padding)
        y2 = min(frame_h, y2 + padding)

        w = x2 - x
        h = y2 - y

        if w <= 0 or h <= 0:
            return None

        return (x, y, w, h)

    def stop(self):
        self.running = False
        self.wait()