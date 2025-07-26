"""候选词窗口，显示拼音候选词和AI补全建议。

该模块实现了一个可拖动的浮动窗口，用于展示输入法的候选词。
窗口设计参考了传统输入法的布局，支持键盘和鼠标选择。
该窗口支持两种状态：
1. 候选词模式：只显示一行候选词，支持左右键切换。
2. AI建议模式：在候选词下方扩展，显示多行AI补全建议，支持上下键切换。
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QFrame, QApplication)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor, QMouseEvent
from typing import List



class CandidateWindow(QWidget):
    """候选词窗口，显示候选词列表和AI建议的浮动窗口。"""
    
    # 信号：当用户点击候选词时发出
    candidate_selected = pyqtSignal(int)
    # 信号：请求翻页（1为下一页，-1为上一页）
    page_change_requested = pyqtSignal(int)
    
    def __init__(self, parent=None):
        """初始化候选词窗口。

        Args:
            parent: 父窗口，默认为None。
        """
        super().__init__(parent)
        self.candidates: List[str] = []
        self.ai_suggestions: List[str] = []
        self.selected_index = 0
        self.ai_selected_index = 0
        self.drag_position = QPoint()
        self.current_page = 0
        self.total_pages = 1
        
        self.setup_ui()
        self.setup_style()
    
    def setup_ui(self):
        """设置用户界面。

        配置窗口属性和布局，包括候选词和AI建议区域。
        """
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
        
        # AI建议容器 (可隐藏)
        self.ai_suggestion_frame = QFrame()
        self.ai_suggestion_frame.setObjectName("aiSuggestionFrame")
        self.ai_suggestion_layout = QVBoxLayout(self.ai_suggestion_frame)
        self.ai_suggestion_layout.setContentsMargins(8, 4, 8, 4)
        self.ai_suggestion_layout.setSpacing(2)
        self.ai_suggestion_frame.hide()
        self.main_layout.addWidget(self.ai_suggestion_frame)
        
        # 初始化标签列表
        self.candidate_labels: List[QLabel] = []
        self.ai_suggestion_labels: List[QLabel] = []
        
        # 设置字体
        font = QFont("Microsoft YaHei", 12)
        self.setFont(font)
        
        # 隐藏窗口
        self.hide()
    
    def setup_style(self):
        """设置窗口样式。

        定义容器、候选词、选中状态和AI建议的样式。
        """
        self.setStyleSheet("""
            #candidateFrame {
                background-color: #E9B72D;
                border: 1px solid #D4A527;
                border-radius: 4px;
            }
            #aiSuggestionFrame {
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
    
    def update_candidates(self, candidates: List[str], current_page: int = 0, total_pages: int = 1):
        """更新候选词列表。

        Args:
            candidates (List[str]): 候选词列表。
            current_page (int): 当前页码，默认为0。
            total_pages (int): 总页数，默认为1。
        """
        self.candidates = candidates
        self.selected_index = 0
        self.current_page = current_page
        self.total_pages = total_pages
        
        print(f"Updating candidates: {candidates}, Page: {current_page+1}/{total_pages}")
        
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
        
        # 添加页码信息
        if total_pages > 1:
            page_info = QLabel(f"[{current_page+1}/{total_pages}]")
            page_info.setObjectName("page_info")
            page_info.setStyleSheet("color: #444; font-size: 10pt;")
            self.candidate_labels.append(page_info)
            self.candidate_layout.addWidget(page_info)
        
        # 高亮第一个候选词
        self.update_selection()
        
        # 调整窗口大小
        self.adjustSize()
        self.show()
        
        print(f"Candidates window shown with {len(candidates)} candidates")
    
    def show_ai_suggestions(self, suggestions: List[str]):
        """显示AI建议列表。

        Args:
            suggestions (List[str]): AI建议的字符串列表。
        """
        if not suggestions:
            self.ai_suggestion_frame.hide()
            return

        self.ai_suggestions = suggestions
        self.ai_selected_index = 0
        
        # 清除现有的AI建议标签
        for label in self.ai_suggestion_labels:
            label.deleteLater()
        self.ai_suggestion_labels.clear()
        
        # 创建新的AI建议标签
        for i, suggestion in enumerate(suggestions):
            label = QLabel(f"{i+1}. {suggestion}")
            label.setObjectName(f"aiSuggestion_{i}")
            label.mousePressEvent = lambda event, idx=i: self.on_ai_suggestion_clicked(idx)
            self.ai_suggestion_labels.append(label)
            self.ai_suggestion_layout.addWidget(label)
        
        self.ai_suggestion_frame.show()
        self.update_ai_selection()
        self.adjustSize()
        self.show()
    
    def update_selection(self):
        """更新候选词选中状态的显示。

        高亮当前选中的候选词。
        """
        for i, label in enumerate(self.candidate_labels):
            if label.objectName() == "page_info":
                continue
                
            if i == self.selected_index:
                label.setProperty("class", "selected")
            else:
                label.setProperty("class", "")
            label.style().unpolish(label)
            label.style().polish(label)
    
    def update_ai_selection(self):
        """更新AI建议选中状态的显示。

        高亮当前选中的AI建议。
        """
        for i, label in enumerate(self.ai_suggestion_labels):
            if i == self.ai_selected_index:
                label.setProperty("class", "selected")
            else:
                label.setProperty("class", "")
            label.style().unpolish(label)
            label.style().polish(label)
    
    def select_next(self) -> bool:
        """选择下一个候选词。

        Returns:
            bool: 如果已经是最后一个则返回True，否则返回False。
        """
        if self.selected_index < len(self.candidates) - 1:
            self.selected_index += 1
            self.update_selection()
            return False
        return True
    
    def select_previous(self) -> bool:
        """选择上一个候选词。

        Returns:
            bool: 如果已经是第一个则返回True，否则返回False。
        """
        if self.selected_index > 0:
            self.selected_index -= 1
            self.update_selection()
            return False
        return True
    
    def select_next_ai(self) -> bool:
        """选择下一个AI建议。

        Returns:
            bool: 如果已经是最后一个则返回True，否则返回False。
        """
        if self.ai_selected_index < len(self.ai_suggestions) - 1:
            self.ai_selected_index += 1
            self.update_ai_selection()
            return False
        return True
    
    def select_previous_ai(self) -> bool:
        """选择上一个AI建议。

        Returns:
            bool: 如果已经是第一个则返回True，否则返回False。
        """
        if self.ai_selected_index > 0:
            self.ai_selected_index -= 1
            self.update_ai_selection()
            return False
        return True
    
    def select_first(self):
        """选择第一个候选词。"""
        self.selected_index = 0
        self.update_selection()
    
    def select_last(self):
        """选择最后一个候选词。"""
        if self.candidates:
            self.selected_index = len(self.candidates) - 1
            self.update_selection()
    
    def is_at_beginning(self) -> bool:
        """检查是否在列表开头。

        Returns:
            bool: 如果在开头返回True，否则返回False。
        """
        return self.selected_index == 0
    
    def is_at_end(self) -> bool:
        """检查是否在列表末尾。

        Returns:
            bool: 如果在末尾返回True，否则返回False。
        """
        return self.selected_index == len(self.candidates) - 1
    
    def get_selected_candidate(self) -> str:
        """获取当前选中的候选词。

        Returns:
            str: 选中的候选词，如果没有则返回空字符串。
        """
        if self.candidates and 0 <= self.selected_index < len(self.candidates):
            return self.candidates[self.selected_index]
        return ""
    
    def get_selected_ai_suggestion(self) -> str:
        """获取当前选中的AI建议。

        Returns:
            str: 选中的AI建议，如果没有则返回空字符串。
        """
        if self.ai_suggestions and 0 <= self.ai_selected_index < len(self.ai_suggestions):
            return self.ai_suggestions[self.ai_selected_index]
        return ""
    
    def on_candidate_clicked(self, index: int):
        """处理候选词点击事件。

        Args:
            index (int): 被点击的候选词索引。
        """
        if 0 <= index < len(self.candidates):
            self.selected_index = index
            self.update_selection()
            self.candidate_selected.emit(index)
    
    def on_ai_suggestion_clicked(self, index: int):
        """处理AI建议点击事件。

        Args:
            index (int): 被点击的AI建议索引。
        """
        if 0 <= index < len(self.ai_suggestions):
            self.ai_selected_index = index
            self.update_ai_selection()
            self.candidate_selected.emit(index)
    
    def move_window(self, x: int, y: int):
        """移动窗口到指定位置。

        Args:
            x (int): X坐标。
            y (int): Y坐标。
        """
        screen = QApplication.primaryScreen().geometry()
        window_width = self.width()
        window_height = self.height()
        
        if x + window_width > screen.width():
            x = screen.width() - window_width
        if y + window_height > screen.height():
            y = y - window_height - 30
        
        if x < 0:
            x = 0
        if y < 0:
            y = 0
            
        self.move(x, y)
    
    def mousePressEvent(self, event: QMouseEvent):
        """处理鼠标按下事件（用于拖动窗口）。

        Args:
            event (QMouseEvent): 鼠标事件对象。
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """处理鼠标移动事件（用于拖动窗口）。

        Args:
            event (QMouseEvent): 鼠标事件对象。
        """
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def keyPressEvent(self, event):
        """处理键盘事件。

        支持左右键切换候选词，上下键切换AI建议。
        """
        key = event.key()
        
        if key == Qt.Key.Key_Right:
            if self.select_next():
                if self.current_page < self.total_pages - 1:
                    self.page_change_requested.emit(1)  # 请求下一页
        elif key == Qt.Key.Key_Left:
            if self.select_previous():
                if self.current_page > 0:
                    self.page_change_requested.emit(-1)  # 请求上一页
        elif key == Qt.Key.Key_Down and self.ai_suggestion_frame.isVisible():
            self.select_next_ai()
        elif key == Qt.Key.Key_Up and self.ai_suggestion_frame.isVisible():
            self.select_previous_ai()
        elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
            if self.candidates:
                self.candidate_selected.emit(self.selected_index)
            elif self.ai_suggestions:
                self.candidate_selected.emit(self.ai_selected_index)
        elif key == Qt.Key.Key_Escape:
            self.hide()
        elif Qt.Key.Key_1 <= key <= Qt.Key.Key_9:
            index = key - Qt.Key.Key_1
            if 0 <= index < len(self.candidates):
                self.candidate_selected.emit(index)
            elif self.ai_suggestion_frame.isVisible() and 0 <= index < len(self.ai_suggestions):
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
    
    def show_ai_suggestions():
        ai_data = ["AI建议1: 你好", "AI建议2: 尼好", "AI建议3: 泥好"]
        window.show_ai_suggestions(ai_data)
    
    QTimer.singleShot(2000, show_ai_suggestions)

    def show_v1_again():
        print("\nUser continues typing, switching back to v1 UI...")
        test_candidates_2 = ["再见", "在见", "载建"]
        window.update_candidates(test_candidates_2, current_page=1, total_pages=1)

    QTimer.singleShot(5000, show_v1_again)
    
    app.exec()