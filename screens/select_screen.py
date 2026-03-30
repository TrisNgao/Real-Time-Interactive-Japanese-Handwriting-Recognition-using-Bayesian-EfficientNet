from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from utils.styles import C, style_btn, card_frame


class SelectScreen(QWidget):
    go_home = pyqtSignal()

    def __init__(self, all_data, on_select):
        super().__init__()
        self.all_data  = all_data
        self.on_select = on_select
        self._build()

    def _build(self):
        self.setStyleSheet(f"background:{C['bg']};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 40, 60, 40)
        layout.setSpacing(24)

        # Back
        btn_back = QPushButton("← Về trang chủ")
        style_btn(btn_back, C['surface'], C['text2'], size=13, pad='8px 16px')
        btn_back.clicked.connect(self.go_home.emit)
        layout.addWidget(btn_back, alignment=Qt.AlignmentFlag.AlignLeft)

        title = QLabel("Chọn bài luyện tập")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"font-size:28px; font-weight:700; color:{C['text']};")
        layout.addWidget(title)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)

        total_all = (len(self.all_data.get('hiragana', [])) +
                     len(self.all_data.get('katakana', [])) +
                     len(self.all_data.get('kanji', [])))

        options = [
            ('hiragana', 'Hiragana', 'あ',
             f'{len(self.all_data.get("hiragana", []))} ký tự', C['blue']),
            ('katakana', 'Katakana', 'ア',
             f'{len(self.all_data.get("katakana", []))} ký tự', C['green']),
            ('kanji',    'Kanji N5', '日',
             f'{len(self.all_data.get("kanji", []))} chữ',      C['gold']),
            ('all',      'Tất cả',   '全',
             f'{total_all} ký tự',                              C['red']),
        ]

        for loai, name, sample, count, color in options:
            f  = card_frame()
            fl = QVBoxLayout(f)
            fl.setContentsMargins(24, 24, 24, 24)
            fl.setSpacing(12)
            f.setFixedSize(220, 260)
            f.setCursor(Qt.CursorShape.PointingHandCursor)

            char_lbl = QLabel(sample)
            char_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            char_lbl.setStyleSheet(
                f"font-size:64px; color:{color}; background:transparent;"
            )

            name_lbl = QLabel(name)
            name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_lbl.setStyleSheet(
                f"font-size:18px; font-weight:700; color:{C['text']}; background:transparent;"
            )

            count_lbl = QLabel(count)
            count_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            count_lbl.setStyleSheet(
                f"font-size:13px; color:{C['text2']}; background:transparent;"
            )

            btn = QPushButton("Bắt đầu →")
            style_btn(btn, color, size=13, pad='10px 20px')
            btn.clicked.connect(lambda checked, l=loai: self.on_select(l))

            fl.addWidget(char_lbl)
            fl.addWidget(name_lbl)
            fl.addWidget(count_lbl)
            fl.addStretch()
            fl.addWidget(btn)
            cards_layout.addWidget(f)

        layout.addLayout(cards_layout)
        layout.addStretch()
