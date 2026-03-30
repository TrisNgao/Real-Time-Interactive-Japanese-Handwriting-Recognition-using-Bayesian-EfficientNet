from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar
)
from PyQt6.QtCore import pyqtSignal
from utils.styles import C, style_btn, card_frame
from utils.database import get_all_stats


class StatsScreen(QWidget):
    go_home = pyqtSignal()

    def __init__(self, all_data):
        super().__init__()
        self.all_data = all_data
        self._build()

    def _build(self):
        self.setStyleSheet(f"background:{C['bg']};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)

        # Top bar
        top = QHBoxLayout()
        btn_back = QPushButton("← Về trang chủ")
        style_btn(btn_back, C['surface'], C['text2'], size=13, pad='8px 16px')
        btn_back.clicked.connect(self.go_home.emit)
        title = QLabel("📊 Tiến độ học tập")
        title.setStyleSheet(f"color:{C['text']}; font-size:16px; font-weight:600;")
        top.addWidget(btn_back)
        top.addStretch()
        top.addWidget(title)
        layout.addLayout(top)

        stats   = get_all_stats()
        total   = sum(len(v) for v in self.all_data.values())
        learned = len([s for s in stats if s[2] > 0])
        perfect = len([s for s in stats if s[1] > 0 and s[2]/s[1] >= 0.9])
        avg_acc = (sum(s[2]/s[1] for s in stats if s[1] > 0) /
                   max(len([s for s in stats if s[1] > 0]), 1))

        # Summary
        summary = QHBoxLayout()
        summary.setSpacing(16)

        for val, label, color in [
            (f"{learned}/{total}", "Đã học",       C['blue']),
            (f"{perfect}",         "Thành thạo",   C['green']),
            (f"{int(avg_acc*100)}%", "Độ chính xác", C['gold']),
        ]:
            f  = card_frame()
            fl = QVBoxLayout(f)
            fl.setContentsMargins(20, 16, 20, 16)
            v  = QLabel(val)
            v.setAlignment(__import__('PyQt6.QtCore', fromlist=['Qt']).Qt.AlignmentFlag.AlignCenter)
            v.setStyleSheet(
                f"font-size:36px; font-weight:900; color:{color}; background:transparent;"
            )
            lb = QLabel(label)
            lb.setAlignment(__import__('PyQt6.QtCore', fromlist=['Qt']).Qt.AlignmentFlag.AlignCenter)
            lb.setStyleSheet(f"font-size:13px; color:{C['text2']}; background:transparent;")
            fl.addWidget(v)
            fl.addWidget(lb)
            summary.addWidget(f)

        layout.addLayout(summary)

        # Top mistakes
        mistakes = sorted(
            [s for s in stats if s[1] > 0 and s[2]/s[1] < 0.7],
            key=lambda x: x[2]/x[1]
        )[:10]

        if mistakes:
            mis_frame  = card_frame()
            mis_layout = QVBoxLayout(mis_frame)
            mis_layout.setContentsMargins(20, 16, 20, 16)
            mis_layout.setSpacing(8)

            mis_title = QLabel("⚠️  Cần ôn luyện thêm")
            mis_title.setStyleSheet(
                f"color:{C['text']}; font-size:14px; font-weight:600; background:transparent;"
            )
            mis_layout.addWidget(mis_title)

            Qt = __import__('PyQt6.QtCore', fromlist=['Qt']).Qt

            for s in mistakes:
                char, attempts, correct = s[0], s[1], s[2]
                acc = correct / attempts if attempts > 0 else 0
                row = QHBoxLayout()

                char_lbl = QLabel(char)
                char_lbl.setFixedWidth(40)
                char_lbl.setStyleSheet(
                    f"font-size:22px; color:{C['red']}; background:transparent;"
                )

                bar = QProgressBar()
                bar.setValue(int(acc * 100))
                bar.setFixedHeight(6)
                bar.setTextVisible(False)
                bar.setStyleSheet(f"""
                    QProgressBar {{ background:{C['bg']}; border-radius:3px; }}
                    QProgressBar::chunk {{ background:{C['red']}; border-radius:3px; }}
                """)

                acc_lbl = QLabel(f"{int(acc*100)}%  ({correct}/{attempts})")
                acc_lbl.setFixedWidth(100)
                acc_lbl.setStyleSheet(
                    f"font-size:12px; color:{C['text3']}; background:transparent;"
                )

                row.addWidget(char_lbl)
                row.addWidget(bar)
                row.addWidget(acc_lbl)
                mis_layout.addLayout(row)

            layout.addWidget(mis_frame)

        layout.addStretch()
