# tabtab/candidate_window.py
import sys
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPalette, QColor

class CandidateWindow(QWidget):
    """输入法候选词窗口的GUI组件。

    该类继承自QWidget，实现了一个无边框、总在最前的浮动窗口，
    用于显示拼音候选词和AI补全建议。
    """
    def __init__(self):
        """CandidateWindow的构造函数。

        初始化窗口属性，如无边框、置顶等，并设置UI布局和样式。
        """
        super().__init__()
        # 设置窗口标志：工具窗口、无边框、总在最前
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        # 设置窗口属性：显示时不激活，避免抢占焦点
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(10, 5, 10, 5)
        
        # 设置一个白色的背景
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(255, 255, 255))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

    def update_candidates(self, candidates):
        """更新并显示候选词列表。

        该方法会清空旧的候选词，然后根据新的列表创建标签并显示。
        如果候选词列表为空，则隐藏窗口。

        Args:
            candidates (list[str]): 要显示的候选词字符串列表。
        """
        # 清空旧的候选词
        for i in reversed(range(self.layout.count())): 
            widget = self.layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        if not candidates:
            self.hide()
            return

        for i, candidate in enumerate(candidates):
            label = QLabel(f"{i+1}. {candidate}")
            label.setStyleSheet("color: black; font-size: 16px;")
            self.layout.addWidget(label)
        
        self.adjustSize()
        self.show()

    def move_window(self, x, y):
        """移动窗口到指定位置。

        通常用于将候选词窗口定位在当前文本光标的下方。

        Args:
            x (int): 目标位置的x坐标。
            y (int): 目标位置的y坐标。
        """
        # 移动窗口到指定位置，y坐标向下偏移20像素以避免遮挡光标
        self.move(QPoint(x, y + 20))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CandidateWindow()
    window.update_candidates(["你好", "牛黄", "内涵"])
    window.move_window(800, 400)
    sys.exit(app.exec())
