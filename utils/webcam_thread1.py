import cv2
import time
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal


class WebcamThread(QThread):
    frame_ready  = pyqtSignal(np.ndarray)
    result_ready = pyqtSignal(list)

    def __init__(self, engine, target_char=None, cam_id=1):
        super().__init__()
        self.engine      = engine
        self.target_char = target_char
        self.cam_id      = int(cam_id)
        self.running     = True
        self.cap         = None

    def set_target(self, char):
        self.target_char = char

    def run(self):
        self.cap = cv2.VideoCapture(int(self.cam_id))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        last_bbox    = None
        stable_start = None
        STABLE_TIME  = 0.5
        last_results = []

        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                self.msleep(33)
                continue

            bbox    = self._detect(frame)
            display = frame.copy()

            if bbox:
                x, y, w, h = bbox
                if last_bbox:
                    x2, y2, w2, h2 = last_bbox
                    diff = abs(x-x2)+abs(y-y2)+abs(w-w2)+abs(h-h2)
                    if diff < 50:
                        if stable_start is None:
                            stable_start = time.time()
                        elif time.time() - stable_start >= STABLE_TIME:
                            roi     = frame[y:y+h, x:x+w]
                            results = self.engine.predict(roi, self.target_char)
                            if results:
                                last_results = results
                                self.result_ready.emit(results)
                    else:
                        stable_start = None
                last_bbox = bbox

                # Vẽ box
                color = (78, 205, 196) if last_results else (108, 99, 255)
                cv2.rectangle(display, (x, y), (x+w, y+h), color, 2)

                # Progress bar debounce
                if stable_start:
                    prog  = min((time.time()-stable_start)/STABLE_TIME, 1.0)
                    bar_w = int(w * prog)
                    cv2.rectangle(display,
                                  (x, y+h+3), (x+bar_w, y+h+8),
                                  (245, 200, 66), -1)
            else:
                last_bbox    = None
                stable_start = None

            self.frame_ready.emit(display)
            self.msleep(33)

        if self.cap:
            self.cap.release()

    def _detect(self, frame, padding=60, min_area=2000):
        gray     = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        h, w     = gray.shape
        margin   = 50
        roi_gray = gray[margin:h-margin, margin:w-margin]
        roi_h, roi_w = roi_gray.shape

        clahe    = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(4, 4))
        enhanced = clahe.apply(roi_gray)
        blurred  = cv2.GaussianBlur(enhanced, (3, 3), 0)

        _, thresh_o = cv2.threshold(
            blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )
        thresh_a = cv2.adaptiveThreshold(
            blurred, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 25, 10
        )
        thresh  = cv2.bitwise_and(thresh_o, thresh_a)

        k       = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 10))
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, k)

        cnts, _ = cv2.findContours(
            cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        if not cnts:
            return None

        valid = []
        for cnt in cnts:
            area = cv2.contourArea(cnt)
            if area < min_area:
                continue
            x, y, cw, ch = cv2.boundingRect(cnt)
            if x < 10 or y < 10:
                continue
            if x+cw > roi_w-10 or y+ch > roi_h-10:
                continue
            ratio = cw/ch if ch > 0 else 0
            if ratio < 0.1 or ratio > 5:
                continue
            if area > roi_w * roi_h * 0.4:
                continue
            valid.append(cnt)

        if not valid:
            return None

        all_x, all_y, all_x2, all_y2 = [], [], [], []
        for cnt in valid:
            x, y, cw, ch = cv2.boundingRect(cnt)
            all_x.append(x);   all_y.append(y)
            all_x2.append(x+cw); all_y2.append(y+ch)

        x  = min(all_x)  + margin
        y  = min(all_y)  + margin
        x2 = max(all_x2) + margin
        y2 = max(all_y2) + margin

        x  = max(0, x  - padding)
        y  = max(0, y  - padding)
        x2 = min(w, x2 + padding)
        y2 = min(h, y2 + padding)

        return (x, y, x2-x, y2-y)

    def stop(self):
        self.running = False
        self.wait()
