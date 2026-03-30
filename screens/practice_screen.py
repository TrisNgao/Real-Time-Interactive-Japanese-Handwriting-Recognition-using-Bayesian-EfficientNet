import random
import time
import cv2
import numpy as np

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap, QColor
from PyQt6.QtWidgets import QGraphicsDropShadowEffect

from utils.database import get_progress, update_progress
from utils.score_engine import cham_diem
from utils.webcam_thread import WebcamThread

# ── Color palette ────────────────────────────────────────────
C = {
    'bg'      : '#0A0A0F',
    'bg2'     : '#12121A',
    'surface' : '#1A1A28',
    'surface2': '#222235',
    'border'  : '#2A2A42',
    'border2' : '#353555',
    'gold'    : '#F5C842',
    'gold2'   : '#FFD966',
    'teal'    : '#4ECDC4',
    'blue'    : '#6C63FF',
    'blue2'   : '#8B85FF',
    'green'   : '#50E3A4',
    'red'     : '#FF6B6B',
    'orange'  : '#FFB347',
    'text'    : '#F0F0F8',
    'text2'   : '#8888AA',
    'text3'   : '#4A4A6A',
    'white'   : '#FFFFFF',
}

TYPE_COLORS = {
    'hiragana': ('#6C63FF', '#8B85FF', 'Hiragana'),
    'katakana': ('#4ECDC4', '#6EE7E0', 'Katakana'),
    'kanji'   : ('#F5C842', '#FFD966', 'Kanji N5'),
}


def _shadow(widget, blur=24, offset=6, alpha=100):
    fx = QGraphicsDropShadowEffect()
    fx.setBlurRadius(blur)
    fx.setColor(QColor(0, 0, 0, alpha))
    fx.setOffset(0, offset)
    widget.setGraphicsEffect(fx)
    return widget


def _card(parent=None, bg=None, border=None, radius=16):
    f = QFrame(parent)
    bg_c = bg or C['surface']
    bd_c = border or C['border']
    f.setStyleSheet(f"""
        QFrame {{
            background: {bg_c};
            border: 1px solid {bd_c};
            border-radius: {radius}px;
        }}
    """)
    _shadow(f)
    return f


def _btn(text, bg, fg='#FFFFFF', size=13, pad='10px 20px', radius=10):
    b = QPushButton(text)
    b.setStyleSheet(f"""
        QPushButton {{
            background: {bg};
            color: {fg};
            border: none;
            border-radius: {radius}px;
            padding: {pad};
            font-size: {size}px;
            font-weight: 600;
            letter-spacing: 0.3px;
        }}
        QPushButton:hover   {{ background: {bg}CC; }}
        QPushButton:pressed {{ background: {bg}99; }}
        QPushButton:disabled {{
            background: {C['surface2']};
            color: {C['text3']};
        }}
    """)
    return b


def _label(text='', size=14, color=None, bold=False, align=Qt.AlignmentFlag.AlignLeft):
    lb = QLabel(text)
    lb.setAlignment(align)
    weight = '600' if bold else '400'
    cl     = color or C['text']
    lb.setStyleSheet(f"""
        QLabel {{
            color: {cl};
            font-size: {size}px;
            font-weight: {weight};
            background: transparent;
        }}
    """)
    return lb


# ════════════════════════════════════════════════════════════
class PracticeScreen(QWidget):
    go_home = pyqtSignal()

    def __init__(self, vocab_data, engine):
        super().__init__()
        self.vocab_data    = vocab_data
        self.engine        = engine
        self.current_card  = None
        self.webcam_thread = None
        self._build()
        self._next_card()

    # ── Build UI ─────────────────────────────────────────────
    def _build(self):
        self.setStyleSheet(f"background:{C['bg']};")
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(14)

        # ── Nav bar ──────────────────────────────────────────
        nav = QHBoxLayout()
        self.btn_back = _btn("← Trang chủ", C['surface2'], C['text2'],
                             size=13, pad='8px 16px', radius=8)
        self.btn_back.clicked.connect(self._stop_cam)
        self.btn_back.clicked.connect(self.go_home.emit)

        self.lbl_progress = _label("Thẻ 1/80", 12, C['text3'])

        nav.addWidget(self.btn_back)
        nav.addStretch()
        nav.addWidget(self.lbl_progress)
        root.addLayout(nav)

        # ── Main columns ─────────────────────────────────────
        cols = QHBoxLayout()
        cols.setSpacing(16)

        # ── LEFT column ──────────────────────────────────────
        left = QVBoxLayout()
        left.setSpacing(12)

        # Card chính
        main_card = _card(radius=20)
        mc_layout = QVBoxLayout(main_card)
        mc_layout.setContentsMargins(28, 24, 28, 24)
        mc_layout.setSpacing(0)

        # Badge loại chữ
        badge_row = QHBoxLayout()
        self.lbl_type = QLabel()
        self.lbl_type.setFixedHeight(26)
        self.lbl_type.setStyleSheet(f"""
            QLabel {{
                background: {C['blue']};
                color: #FFFFFF;
                border-radius: 13px;
                padding: 0px 14px;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 1px;
            }}
        """)
        badge_row.addWidget(self.lbl_type)
        badge_row.addStretch()

        # Số nét nhỏ bên phải
        self.lbl_strokes = _label('', 12, C['text3'])
        badge_row.addWidget(self.lbl_strokes)
        mc_layout.addLayout(badge_row)
        mc_layout.addSpacing(16)

        # Chữ lớn — trung tâm
        self.lbl_char = QLabel()
        self.lbl_char.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_char.setMinimumHeight(160)
        self.lbl_char.setStyleSheet(f"""
            QLabel {{
                font-size: 140px;
                color: {C['gold']};
                background: transparent;
                letter-spacing: -2px;
            }}
        """)
        mc_layout.addWidget(self.lbl_char)
        mc_layout.addSpacing(8)

        # Separator line
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background: {C['border']}; max-height: 1px;")
        mc_layout.addWidget(sep)
        mc_layout.addSpacing(14)

        # Nghĩa
        self.lbl_nghia = _label('', 22, C['text'], bold=True,
                                align=Qt.AlignmentFlag.AlignCenter)
        self.lbl_nghia.setWordWrap(True)
        mc_layout.addWidget(self.lbl_nghia)
        mc_layout.addSpacing(4)

        # Cách đọc
        self.lbl_reading = _label('', 15, C['text2'],
                                  align=Qt.AlignmentFlag.AlignCenter)
        mc_layout.addWidget(self.lbl_reading)
        mc_layout.addSpacing(16)

        left.addWidget(main_card)

        # Card mẹo
        self.tip_card = _card(bg=C['bg2'], radius=12)
        tip_layout    = QHBoxLayout(self.tip_card)
        tip_layout.setContentsMargins(16, 12, 16, 12)

        tip_icon = _label('💡', 16, C['gold'])
        tip_icon.setFixedWidth(24)
        self.lbl_meo = _label('', 13, C['text2'])
        self.lbl_meo.setWordWrap(True)
        tip_layout.addWidget(tip_icon)
        tip_layout.addWidget(self.lbl_meo)
        left.addWidget(self.tip_card)

        # Card ví dụ
        ex_card    = _card(bg=C['bg2'], radius=12)
        ex_layout  = QVBoxLayout(ex_card)
        ex_layout.setContentsMargins(16, 12, 16, 12)
        ex_layout.setSpacing(6)

        ex_header = _label('Ví dụ', 11, C['text3'], bold=True)
        self.lbl_vidu = _label('', 15, C['text2'])
        self.lbl_vidu.setWordWrap(True)
        ex_layout.addWidget(ex_header)
        ex_layout.addWidget(self.lbl_vidu)
        left.addWidget(ex_card)

        left.addStretch()
        cols.addLayout(left, 42)

        # ── RIGHT column ─────────────────────────────────────
        right = QVBoxLayout()
        right.setSpacing(12)

        # Camera card
        cam_card   = _card(radius=20)
        cam_layout = QVBoxLayout(cam_card)
        cam_layout.setContentsMargins(16, 14, 16, 14)
        cam_layout.setSpacing(10)

        cam_header = QHBoxLayout()
        cam_dot    = QLabel()
        cam_dot.setFixedSize(8, 8)
        cam_dot.setStyleSheet(f"""
            QLabel {{
                background: {C['red']};
                border-radius: 4px;
            }}
        """)
        cam_title = _label('Camera', 13, C['text2'])
        cam_header.addWidget(cam_dot)
        cam_header.addWidget(cam_title)
        cam_header.addStretch()
        cam_layout.addLayout(cam_header)

        self.lbl_cam = QLabel("Camera chưa bật\nBấm ▶ để bắt đầu")
        self.lbl_cam.setFixedSize(420, 315)
        self.lbl_cam.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_cam.setStyleSheet(f"""
            QLabel {{
                background: {C['bg2']};
                border: 1px solid {C['border']};
                border-radius: 12px;
                color: {C['text3']};
                font-size: 13px;
                line-height: 1.8;
            }}
        """)
        cam_layout.addWidget(self.lbl_cam)

        cam_btns = QHBoxLayout()
        cam_btns.setSpacing(8)
        self.btn_start_cam = _btn("▶  Bật camera", C['teal'],
                                  '#0A0A0F', size=12, pad='9px 18px')
        self.btn_stop_cam  = _btn("■  Tắt", C['surface2'], C['red'],
                                  size=12, pad='9px 18px')
        self.btn_stop_cam.setEnabled(False)
        self.btn_start_cam.clicked.connect(self._start_cam)
        self.btn_stop_cam.clicked.connect(self._stop_cam)
        cam_btns.addWidget(self.btn_start_cam)
        cam_btns.addWidget(self.btn_stop_cam)
        cam_btns.addStretch()
        cam_layout.addLayout(cam_btns)
        right.addWidget(cam_card)

        # Result card
        res_card   = _card(radius=20)
        res_layout = QVBoxLayout(res_card)
        res_layout.setContentsMargins(20, 16, 20, 16)
        res_layout.setSpacing(6)

        res_title = _label('Kết quả', 11, C['text3'], bold=True)
        res_layout.addWidget(res_title)

        # Score + verdict row
        score_row = QHBoxLayout()

        self.lbl_score = QLabel("—")
        self.lbl_score.setFixedWidth(90)
        self.lbl_score.setStyleSheet(f"""
            QLabel {{
                font-size: 52px;
                font-weight: 800;
                color: {C['text3']};
                background: transparent;
                letter-spacing: -1px;
            }}
        """)

        verdict_col = QVBoxLayout()
        verdict_col.setSpacing(4)
        self.lbl_verdict = _label('Đưa chữ vào camera...', 14, C['text2'])
        self.lbl_verdict.setWordWrap(True)
        self.lbl_top3 = _label('', 12, C['text3'])
        verdict_col.addWidget(self.lbl_verdict)
        verdict_col.addWidget(self.lbl_top3)
        verdict_col.addStretch()

        score_row.addWidget(self.lbl_score)
        score_row.addSpacing(12)
        score_row.addLayout(verdict_col)
        res_layout.addLayout(score_row)

        self.lbl_streak = _label('', 13, C['gold'],
                                 align=Qt.AlignmentFlag.AlignCenter)
        res_layout.addWidget(self.lbl_streak)

        right.addWidget(res_card)

        # Next button
        self.btn_next = _btn("Thẻ tiếp theo  →", C['blue'],
                             size=14, pad='14px 0px', radius=12)
        self.btn_next.setMinimumHeight(48)
        self.btn_next.clicked.connect(self._next_card)
        right.addWidget(self.btn_next)

        cols.addLayout(right, 58)
        root.addLayout(cols)

    # ── Logic ────────────────────────────────────────────────
    def _next_card(self):
        self._reset_result()

        now = time.time()
        due = [k for k in self.vocab_data
               if get_progress(k['char'])['next_review'] <= now]
        self.current_card = random.choice(due if due else self.vocab_data)
        card = self.current_card

        self.lbl_char.setText(card['char'])
        self.lbl_nghia.setText(card.get('nghia_vi', ''))

        onyomi  = card.get('onyomi', '') or card.get('romaji', '')
        kunyomi = card.get('kunyomi', '')
        reading = f"{onyomi}  /  {kunyomi}" if onyomi or kunyomi else ''
        self.lbl_reading.setText(reading)

        so_net = card.get('so_net', '')
        self.lbl_strokes.setText(f"{so_net} nét" if so_net else '')

        meo = card.get('meo', '')
        self.lbl_meo.setText(meo if meo else '')
        self.tip_card.setVisible(bool(meo))

        examples = card.get('vi_du', [])[:2]
        ex_lines = '\n'.join(
            [f"{e['tu']}  ({e['doc']})  =  {e['nghia']}" for e in examples]
        )
        self.lbl_vidu.setText(ex_lines)

        idx = next((i for i, k in enumerate(self.vocab_data)
                    if k['char'] == card['char']), 0)
        self.lbl_progress.setText(
            f"Thẻ {idx+1} / {len(self.vocab_data)}"
        )

        # Badge loại chữ
        char_type = ''
        if hasattr(self.engine, 'get_char_type'):
            char_type = self.engine.get_char_type(card['char'])
        bg1, _, name = TYPE_COLORS.get(char_type, (C['blue'], C['blue2'], '—'))
        self.lbl_type.setText(name.upper())
        self.lbl_type.setStyleSheet(f"""
            QLabel {{
                background: {bg1};
                color: #FFFFFF;
                border-radius: 13px;
                padding: 0px 14px;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 1px;
            }}
        """)
        # Màu chữ theo loại
        self.lbl_char.setStyleSheet(f"""
            QLabel {{
                font-size: 140px;
                color: {bg1};
                background: transparent;
                letter-spacing: -2px;
            }}
        """)

        prog = get_progress(card['char'])
        self.lbl_streak.setText(
            f"  Streak {prog['streak']}" if prog['streak'] >= 3 else ""
        )

        if self.webcam_thread:
            self.webcam_thread.set_target(card['char'])

    def _reset_result(self):
        self.lbl_score.setText("—")
        self.lbl_score.setStyleSheet(f"""
            QLabel {{
                font-size: 52px; font-weight: 800;
                color: {C['text3']}; background: transparent;
                letter-spacing: -1px;
            }}
        """)
        self.lbl_verdict.setText("Đưa chữ vào camera...")
        self.lbl_verdict.setStyleSheet(
            f"color:{C['text2']}; font-size:14px; background:transparent;"
        )
        self.lbl_top3.setText("")

    def _start_cam(self, cam_id=0):
        if self.webcam_thread and self.webcam_thread.isRunning():
            return
        target = self.current_card['char'] if self.current_card else None
        self.webcam_thread = WebcamThread(
            self.engine, target_char=target, cam_id=int(cam_id)
        )
        self.webcam_thread.frame_ready.connect(self._update_frame)
        self.webcam_thread.result_ready.connect(self._on_result)
        self.webcam_thread.start()
        self.btn_start_cam.setEnabled(False)
        self.btn_stop_cam.setEnabled(True)

    def _stop_cam(self):
        if self.webcam_thread:
            self.webcam_thread.stop()
            self.webcam_thread = None
        self.lbl_cam.setText("Camera đã tắt\nBấm ▶ để bắt đầu lại")
        self.btn_start_cam.setEnabled(True)
        self.btn_stop_cam.setEnabled(False)

    def _update_frame(self, frame):
        h, w, _ = frame.shape
        rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        qimg   = QImage(rgb.data, w, h, w*3, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg).scaled(
            420, 315,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.lbl_cam.setPixmap(pixmap)

    def _on_result(self, results):
        if not results or not self.current_card:
            return

        target = self.current_card['char']
        result = cham_diem(target, results)
        score  = result['score']
        update_progress(target, score)

        pct = int(score * 100)
        color_map = {
            'green' : C['green'],
            'orange': C['orange'],
            'red'   : C['red'],
        }
        color = color_map.get(result['color'], C['text'])

        self.lbl_score.setText(f"{pct}%")
        self.lbl_score.setStyleSheet(f"""
            QLabel {{
                font-size: 52px; font-weight: 800;
                color: {color}; background: transparent;
                letter-spacing: -1px;
            }}
        """)
        self.lbl_verdict.setText(result['nhan_xet'])
        self.lbl_verdict.setStyleSheet(
            f"color:{color}; font-size:14px; background:transparent;"
        )

        top3 = '   '.join(
            [f"{r['char']} {int(r['prob']*100)}%" for r in results[:3]]
        )
        self.lbl_top3.setText(top3)

        prog = get_progress(target)
        self.lbl_streak.setText(
            f"  Streak {prog['streak']}" if prog['streak'] >= 3 else ""
        )