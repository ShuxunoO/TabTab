# tabtab/candidate_window.py
"""候选词窗口，显示拼音候选词和AI补全建议。

该模块实现了一个可拖动的浮动窗口，用于展示输入法的候选词。
窗口设计参考了传统输入法的布局，支持键盘和鼠标选择。
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QFrame, QApplication)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor, QMouseEvent
from typing import List


class CandidateWindow(QWidget):
    """候选词窗口，显示候选词列表的浮动窗口。"""
    
    # 信号：当用户点击候选词时发出
    candidate_selected = pyqtSignal(int)
    
    def __init__(self, parent=None):
        """初始化候选词窗口。"""
        super().__init__(parent)
        self.candidates: List[str] = []
        self.selected_index = 0
        self.drag_position = QPoint()
        
        self.setup_ui()
        self.setup_style()
    
    def setup_ui(self):
        """设置用户界面。"""
        # 设置窗口属性
        self.setWindowFlags(
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 候选词容器
        self.candidate_frame = QFrame()
        self.candidate_frame.setObjectName("candidateFrame")
        self.candidate_layout = QHBoxLayout(self.candidate_frame)
        self.candidate_layout.setContentsMargins(8, 4, 8, 4)
        self.candidate_layout.setSpacing(2)
        
        self.main_layout.addWidget(self.candidate_frame)
        
        # 初始化候选词标签列表
        self.candidate_labels: List[QLabel] = []
        
        # 设置字体
        font = QFont("Microsoft YaHei", 12)
        self.setFont(font)
        
        # 隐藏窗口
        self.hide()
    
    def setup_style(self):
        """设置窗口样式。"""
        self.setStyleSheet("""
            #candidateFrame {
                background-color: #E9B72D;
                border: 1px solid #D4A527;
                border-radius: 4px;
            }
            QLabel {
                color: #000000;
                padding: 4px 8px;
                margin: 0px 1px;
                background-color: transparent;
                border-radius: 2px;
            }
            QLabel:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
            .selected {
                background-color: rgba(255, 255, 255, 0.5);
                font-weight: bold;
            }
        """)
    def update_candidates(self, candidates: List[str]):
        """更新候选词列表。
        
        Args:
            candidates: 候选词列表
        """
        self.candidates = candidates
        self.selected_index = 0
        
        print(f"Updating candidates: {candidates}")
        
        # 清除现有的候选词标签
        for label in self.candidate_labels:
            label.deleteLater()
        self.candidate_labels.clear()
        
        if not candidates:
            self.hide()
            return
        
        # 创建新的候选词标签
        for i, candidate in enumerate(candidates):
            label = QLabel(f"{i+1}.{candidate}")
            label.setObjectName(f"candidate_{i}")
            label.mousePressEvent = lambda event, idx=i: self.on_candidate_clicked(idx)
            
            self.candidate_labels.append(label)
            self.candidate_layout.addWidget(label)
        
        # 高亮第一个候选词
        self.update_selection()
        
        # 调整窗口大小
        self.adjustSize()
        self.show()
        
        print(f"Candidates window shown with {len(candidates)} candidates")
    
    def update_selection(self):
        """更新选中状态的显示。"""
        for i, label in enumerate(self.candidate_labels):
            if i == self.selected_index:
                label.setProperty("class", "selected")
            else:
                label.setProperty("class", "")
            label.style().unpolish(label)
            label.style().polish(label)
    
    def select_next(self):
        """选择下一个候选词。"""
        if self.candidates and self.selected_index < len(self.candidates) - 1:
            self.selected_index += 1
            self.update_selection()
    
    def select_previous(self):
        """选择上一个候选词。"""
        if self.candidates and self.selected_index > 0:
            self.selected_index -= 1
            self.update_selection()
    
    def get_selected_candidate(self) -> str:
        """获取当前选中的候选词。
        
        Returns:
            选中的候选词，如果没有则返回空字符串
        """
        if self.candidates and 0 <= self.selected_index < len(self.candidates):
            return self.candidates[self.selected_index]
        return ""
    
    def on_candidate_clicked(self, index: int):
        """处理候选词点击事件。
        
        Args:
            index: 被点击的候选词索引
        """
        if 0 <= index < len(self.candidates):
            self.selected_index = index
            self.candidate_selected.emit(index)
    
    def move_window(self, x: int, y: int):
        """移动窗口到指定位置。
        
        Args:
            x: X坐标
            y: Y坐标
        """
        # 确保窗口不会超出屏幕边界
        screen = QApplication.primaryScreen().geometry()
        window_width = self.width()
        window_height = self.height()
        
        # 调整位置以确保窗口完全可见
        if x + window_width > screen.width():
            x = screen.width() - window_width
        if y + window_height > screen.height():
            y = y - window_height - 30  # 显示在光标上方
            
        if x < 0:
            x = 0
        if y < 0:
            y = 0
            
        self.move(x, y)
    
    def mousePressEvent(self, event: QMouseEvent):
        """处理鼠标按下事件（用于拖动窗口）。"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """处理鼠标移动事件（用于拖动窗口）。"""
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def keyPressEvent(self, event):
        """处理键盘事件。"""
        key = event.key()
        
        if key == Qt.Key.Key_Down or key == Qt.Key.Key_Right:
            self.select_next()
        elif key == Qt.Key.Key_Up or key == Qt.Key.Key_Left:
            self.select_previous()
        elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
            if self.candidates:
                self.candidate_selected.emit(self.selected_index)
        elif key == Qt.Key.Key_Escape:
            self.hide()
        elif Qt.Key.Key_1 <= key <= Qt.Key.Key_9:
            # 数字键选择候选词
            index = key - Qt.Key.Key_1
            if 0 <= index < len(self.candidates):
                self.candidate_selected.emit(index)
        
        super().keyPressEvent(event)


if __name__ == '__main__':
    # 测试候选词窗口
    app = QApplication([])
    
    window = CandidateWindow()
    window.candidate_selected.connect(lambda idx: print(f"Selected: {idx}"))
    
    # 测试数据
    test_candidates = ["你", "尼", "泥", "倪", "妮"]
    window.update_candidates(test_candidates)
    window.move_window(500, 300)
    
    app.exec()
