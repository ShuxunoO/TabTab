# tabtab/input_manager.py
"""输入管理器，协调输入法的各个组件。

该模块是输入法的核心控制器，负责协调键盘监听、拼音转换、
候选词显示和文本输入等功能。
"""

import pyautogui
import ctypes
import time
from pynput import keyboard
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QApplication
from typing import List, Optional

from pinyin_engine import PinyinEngine
from candidate_window import CandidateWindow
from keyboard_listener import KeyboardListenerThread, is_alpha_char, is_digit_char, get_key_char


class InputManager(QObject):
    """输入法核心管理器，协调所有输入法组件。"""
    
    def __init__(self, parent=None):
        """初始化输入管理器。"""
        super().__init__(parent)
        
        # 核心组件
        self.pinyin_engine = PinyinEngine()
        self.candidate_window = CandidateWindow()
        
        # 输入状态
        self.pinyin_buffer = ""  # 拼音缓冲区
        self.candidates: List[str] = []  # 当前候选词
        self.is_active = False  # 输入法是否激活
        self.suppress_next_key = False  # 是否阻止下一个按键
        
        # 键盘监听
        self.keyboard_listener = KeyboardListenerThread()
        self.keyboard_listener.key_pressed.connect(self.on_key_press)
        
        # 连接候选词窗口信号
        self.candidate_window.candidate_selected.connect(self.on_candidate_selected)
        
        # 设置pyautogui的延迟，提高输入速度
        pyautogui.PAUSE = 0.01
        pyautogui.FAILSAFE = False
    
    def start(self):
        """启动输入法。"""
        print("Starting TabTab Input Method...")
        self.keyboard_listener.start()
        print("TabTab Input Method is running. Press Ctrl+C to stop.")
    
    def stop(self):
        """停止输入法。"""
        print("Stopping TabTab Input Method...")
        self.keyboard_listener.stop_listening()
        self.candidate_window.hide()
        print("TabTab Input Method stopped.")
    
    def should_suppress_key(self, key) -> bool:
        """判断是否应该阻止按键传播到其他应用程序。
        
        Args:
            key: 按下的键
            
        Returns:
            True如果应该阻止，False如果允许传播
        """
        # 如果输入法激活且有候选词，阻止某些按键
        if self.is_active and self.candidates:
            # 阻止数字键1-9
            if is_digit_char(key):
                digit = int(get_key_char(key))
                if 1 <= digit <= len(self.candidates):
                    return True
            
            # 阻止Tab键、空格键、回车键
            if key in [keyboard.Key.tab, keyboard.Key.space, keyboard.Key.enter]:
                return True
        
        # 如果输入法激活，阻止字母键
        if self.is_active and is_alpha_char(key):
            return True
            
        # 如果输入法激活，阻止退格键和ESC键
        if self.is_active and key in [keyboard.Key.backspace, keyboard.Key.esc]:
            return True
            
        return False
    
    def on_key_press(self, key):
        """处理键盘按下事件。
        
        Args:
            key: 按下的键
        """
        try:
            print(f"Key pressed: {key}, Type: {type(key)}")
            print(f"Input state - Active: {self.is_active}, Buffer: '{self.pinyin_buffer}', Candidates: {len(self.candidates)}")
            
            # 检查是否应该阻止按键
            suppress_key = self.should_suppress_key(key)
            
            # 处理字母键（拼音输入）
            if is_alpha_char(key):
                char = get_key_char(key).lower()
                self.pinyin_buffer += char
                self.update_candidates()
                self.is_active = True
                print(f"Added char '{char}' to buffer: '{self.pinyin_buffer}'")
                return suppress_key
            
            # 处理数字键（选择候选词）
            elif is_digit_char(key):
                digit = int(get_key_char(key))
                print(f"Digit key pressed: {digit}")
                if self.is_active and self.candidates and 1 <= digit <= len(self.candidates):
                    print(f"Selecting candidate {digit-1}: {self.candidates[digit-1]}")
                    self.select_candidate(digit - 1)
                    return True  # 阻止数字键传播
                else:
                    print(f"Digit key not handled - Active: {self.is_active}, Candidates: {len(self.candidates)}")
            
            # 处理Tab键（确认第一个候选词）
            elif key == keyboard.Key.tab:
                print(f"Tab key pressed - Active: {self.is_active}, Candidates: {len(self.candidates)}")
                if self.is_active and self.candidates:
                    print(f"Tab selecting first candidate: {self.candidates[0]}")
                    self.select_candidate(0)
                    return True  # 阻止Tab键传播
                else:
                    print("Tab key - not in input mode or no candidates")
            
            # 处理空格键（确认第一个候选词或输入空格）
            elif key == keyboard.Key.space:
                if self.is_active and self.candidates:
                    self.select_candidate(0)
                    return True  # 阻止空格键传播
                else:
                    # 让空格键正常传播
                    return False
            
            # 处理回车键（确认第一个候选词或换行）
            elif key == keyboard.Key.enter:
                if self.is_active and self.candidates:
                    self.select_candidate(0)
                    return True  # 阻止回车键传播
                else:
                    # 让回车键正常传播
                    return False
            
            # 处理退格键
            elif key == keyboard.Key.backspace:
                if self.is_active and self.pinyin_buffer:
                    self.pinyin_buffer = self.pinyin_buffer[:-1]
                    self.update_candidates()
                    if not self.pinyin_buffer:
                        self.deactivate()
                    return True  # 阻止退格键传播
                else:
                    # 让退格键正常传播
                    return False
            
            # 处理ESC键（取消输入）
            elif key == keyboard.Key.esc:
                if self.is_active:
                    self.deactivate()
                    return True  # 阻止ESC键传播
                else:
                    return False
            
            # 处理上下方向键（选择候选词）
            elif key == keyboard.Key.down:
                if self.is_active:
                    self.candidate_window.select_next()
                    return True
                return False
            
            elif key == keyboard.Key.up:
                if self.is_active:
                    self.candidate_window.select_previous()
                    return True
                return False
            
            # 其他键（如标点符号等）
            else:
                if self.is_active:
                    # 如果正在输入拼音，先确认第一个候选词，然后输入字符
                    if self.candidates:
                        self.select_candidate(0)
                    else:
                        self.deactivate()
                
                # 让其他键正常传播
                return False
                
            return suppress_key
        
        except Exception as e:
            print(f"Error handling key press: {e}")
            return False
    
    def update_candidates(self):
        """更新候选词列表。"""
        if not self.pinyin_buffer:
            self.candidates = []
            self.candidate_window.hide()
            return
        
        # 获取候选词
        self.candidates = self.pinyin_engine.get_candidates(self.pinyin_buffer)
        
        if self.candidates:
            # 显示候选词窗口
            self.candidate_window.update_candidates(self.candidates)
            self.move_candidate_window()
        else:
            self.candidate_window.hide()
    
    def select_candidate(self, index: int):
        """选择候选词。
        
        Args:
            index: 候选词索引
        """
        if 0 <= index < len(self.candidates):
            selected_word = self.candidates[index]
            print(f"Selecting candidate {index}: '{selected_word}'")
            
            # 清除拼音缓冲区中的字符
            self.clear_pinyin_buffer()
            
            # 使用延迟确保清除操作完成
            QTimer.singleShot(50, lambda: self.input_text_delayed(selected_word))
            
            # 清空状态
            self.reset_state()
            print(f"Successfully selected candidate: '{selected_word}'")
    
    def input_text_delayed(self, text: str):
        """延迟输入文本。
        
        Args:
            text: 要输入的文本
        """
        self.input_text(text)
    
    def on_candidate_selected(self, index: int):
        """处理候选词窗口的选择事件。
        
        Args:
            index: 选中的候选词索引
        """
        self.select_candidate(index)
    
    def input_text(self, text: str):
        """输入文本到当前应用程序。
        
        Args:
            text: 要输入的文本
        """
        try:
            print(f"Inputting text: '{text}'")
            
            # 使用Windows剪贴板方式输入（更可靠）
            if hasattr(ctypes.windll, 'user32'):
                self.input_text_via_clipboard(text)
            else:
                # 备用方法：直接使用pyautogui
                pyautogui.typewrite(text, interval=0.01)
            
            print(f"Text input completed: '{text}'")
        except Exception as e:
            print(f"Error inputting text: {e}")
            # 备用方法
            try:
                pyautogui.typewrite(text, interval=0.01)
            except Exception as e2:
                print(f"Backup input method also failed: {e2}")
    
    def input_text_via_clipboard(self, text: str):
        """通过剪贴板输入文本。
        
        Args:
            text: 要输入的文本
        """
        try:
            import win32clipboard
            import win32con
            
            # 保存当前剪贴板内容
            win32clipboard.OpenClipboard()
            try:
                original_data = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
            except:
                original_data = ""
            win32clipboard.CloseClipboard()
            
            # 设置新的剪贴板内容
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(text)
            win32clipboard.CloseClipboard()
            
            # 发送Ctrl+V粘贴
            pyautogui.hotkey('ctrl', 'v')
            
            # 延迟后恢复原剪贴板内容
            QTimer.singleShot(100, lambda: self.restore_clipboard(original_data))
            
        except ImportError:
            # 如果没有win32clipboard，使用备用方法
            pyautogui.typewrite(text, interval=0.01)
        except Exception as e:
            print(f"Clipboard input failed: {e}")
            pyautogui.typewrite(text, interval=0.01)
    
    def restore_clipboard(self, original_data: str):
        """恢复剪贴板内容。
        
        Args:
            original_data: 原始剪贴板内容
        """
        try:
            import win32clipboard
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            if original_data:
                win32clipboard.SetClipboardText(original_data)
            win32clipboard.CloseClipboard()
        except:
            pass
    
    def clear_pinyin_buffer(self):
        """清除拼音缓冲区对应的字符。"""
        if self.pinyin_buffer:
            print(f"Clearing pinyin buffer: '{self.pinyin_buffer}' ({len(self.pinyin_buffer)} chars)")
            # 发送退格键清除已输入的拼音
            for _ in range(len(self.pinyin_buffer)):
                pyautogui.press('backspace')
            print("Pinyin buffer cleared")
    
    def reset_state(self):
        """重置输入状态。"""
        self.pinyin_buffer = ""
        self.candidates = []
        self.is_active = False
        self.candidate_window.hide()
    
    def deactivate(self):
        """取消激活输入法。"""
        self.reset_state()
    
    def move_candidate_window(self):
        """移动候选词窗口到光标位置附近。"""
        try:
            x, y = self.get_cursor_position()
            self.candidate_window.move_window(x, y + 25)  # 显示在光标下方
        except Exception as e:
            print(f"Error moving candidate window: {e}")
            # 使用默认位置
            screen = QApplication.primaryScreen().geometry()
            self.candidate_window.move_window(screen.width() // 2, screen.height() // 2)
    
    def get_cursor_position(self) -> tuple:
        """获取当前光标位置。
        
        Returns:
            光标位置的(x, y)坐标
        """
        try:
            # 尝试使用Windows API获取光标位置
            class POINT(ctypes.Structure):
                _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
            
            point = POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
            return point.x, point.y
        except Exception:
            # 如果失败，使用屏幕中心
            screen = QApplication.primaryScreen().geometry()
            return screen.width() // 2, screen.height() // 2


if __name__ == '__main__':
    # 测试输入管理器
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    input_manager = InputManager()
    
    try:
        input_manager.start()
        app.exec()
    except KeyboardInterrupt:
        print("\nReceived Ctrl+C, stopping...")
    finally:
        input_manager.stop()
