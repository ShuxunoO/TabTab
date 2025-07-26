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
from ai_engine import AIEngine
import re


class InputManager(QObject):
    """输入法核心管理器，协调所有输入法组件。"""
    
    def __init__(self, parent=None):
        """初始化输入管理器。"""
        super().__init__(parent)
        
        # 核心组件
        self.pinyin_engine = PinyinEngine()
        self.candidate_window = CandidateWindow()
        self.ai_engine = AIEngine()
        
        # 连接AI引擎信号
        self.ai_engine.completions_ready.connect(self.on_ai_completions_ready)
        self.ai_engine.error_occurred.connect(self.on_ai_error)
        
        # 输入状态
        self.pinyin_buffer = ""  # 拼音缓冲区
        self.candidates: List[str] = []  # 当前候选词
        self.full_candidates: List[str] = []  # 完整候选词列表
        self.current_page = 0  # 当前页码
        self.page_size = 5  # 每页显示数量
        self.is_active = False  # 输入法是否激活
        self.suppress_next_key = False  # 是否阻止下一个按键
        
        # AI补全状态
        self.ai_completions: List[str] = []  # AI补全结果
        self.is_ai_mode = False  # 是否处于AI补全模式
        self.last_ai_request_time = 0  # 上次AI请求时间
        self.ai_request_cooldown = 3  # AI请求冷却时间（秒）
        
        # 最近输入内容跟踪
        self.last_input_text = ""  # 最近一次输入的文本
        self.last_input_pinyin = ""  # 最近一次输入的拼音
        
        # 双击Tab检测相关
        self.last_tab_time = 0  # 上次Tab按键时间戳
        self.tab_double_click_interval = 0.3  # 双击时间间隔阈值（秒）
        
        # 键盘监听
        self.keyboard_listener = KeyboardListenerThread()
        self.keyboard_listener.key_pressed.connect(self.on_key_press)
        
        # 连接候选词窗口信号
        self.candidate_window.candidate_selected.connect(self.on_candidate_selected)
        self.candidate_window.page_change_requested.connect(self.handle_page_change)
        
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
        # 如果在AI模式下，阻止相关按键
        if self.is_ai_mode and self.ai_completions:
            # 阻止数字键1-9
            if is_digit_char(key):
                digit = int(get_key_char(key))
                if 1 <= digit <= len(self.ai_completions):
                    return True
            
            # 阻止空格键、回车键
            if key in [keyboard.Key.space, keyboard.Key.enter]:
                return True

            # 阻止方向键
            if key in [keyboard.Key.left, keyboard.Key.right, keyboard.Key.up, keyboard.Key.down]:
                return True
        
        # 如果输入法激活且有候选词，阻止某些按键
        if self.is_active and self.candidates:
            # 阻止数字键1-9
            if is_digit_char(key):
                digit = int(get_key_char(key))
                if 1 <= digit <= len(self.candidates):
                    return True
            
            # 阻止空格键、回车键（注意：不再阻止Tab键）
            if key in [keyboard.Key.space, keyboard.Key.enter]:
                return True

            # 阻止方向键
            if key in [keyboard.Key.left, keyboard.Key.right, keyboard.Key.up, keyboard.Key.down]:
                return True
        
        # 如果输入法激活，阻止字母键
        if self.is_active and is_alpha_char(key):
            return True
            
        # 如果输入法激活，阻止退格键和ESC键
        if self.is_active and key in [keyboard.Key.backspace, keyboard.Key.esc]:
            return True
            
        return False
    
    def next_page(self) -> bool:
        """翻到下一页。
        
        Returns:
            成功翻页返回True，否则返回False
        """
        max_page = (len(self.full_candidates) + self.page_size - 1) // self.page_size - 1
        if self.current_page < max_page:
            self.current_page += 1
            self.show_current_page_candidates()
            return True
        return False
    
    def previous_page(self) -> bool:
        """翻到上一页。
        
        Returns:
            成功翻页返回True，否则返回False
        """
        if self.current_page > 0:
            self.current_page -= 1
            self.show_current_page_candidates()
            return True
        return False
        
    def handle_page_change(self, direction: int):
        """处理页面变更请求。
        
        Args:
            direction: 1表示下一页，-1表示上一页
        """
        if direction > 0:
            self.next_page()
        else:
            self.previous_page()
    
    def handle_tab_double_click(self):
        """处理双击Tab事件。

        双击Tab键可以在候选词窗口中快速切换到AI补全建议。
        """
        print("Tab键双击事件触发")
        # 检查是否满足AI请求条件
        text_for_ai = ""
        
        # 优先使用当前激活的输入
        if self.is_active and self.pinyin_buffer:
            first_candidate = self.candidates[0] if self.candidates else ""
            text_for_ai = f"{self.pinyin_buffer} {first_candidate}"
        # 如果没有当前输入，尝试使用最近输入的内容
        elif self.last_input_text:
            # 如果有最近输入的拼音，使用拼音+文本
            if self.last_input_pinyin:
                text_for_ai = f"{self.last_input_pinyin} {self.last_input_text}"
            else:
                # 否则只使用最近输入的文本
                text_for_ai = self.last_input_text
        else:
            print("没有激活的输入或最近输入内容，无法请求AI补全")
            return
            
        # 检查冷却时间
        current_time = time.time()
        if (current_time - self.last_ai_request_time) < self.ai_request_cooldown:
            print(f"AI请求冷却中，还需等待{self.ai_request_cooldown - (current_time - self.last_ai_request_time):.1f}秒")
            return
            
        # 记录请求时间
        self.last_ai_request_time = current_time
        
        # 清理发送给AI的文本，移除可能导致问题的特殊字符
        text_for_ai = self.clean_text_for_ai(text_for_ai)
        print(f"请求AI补全: '{text_for_ai}'")
        
        # 请求AI补全
        self.ai_engine.get_completions(text_for_ai)

    def on_ai_completions_ready(self, completions: List[str]):
        """处理AI补全结果。

        Args:
            completions: AI返回的补全结果列表
        """
        print(f"AI补全结果: {completions}")
        self.ai_completions = completions
        self.is_ai_mode = True
        
        # 更新候选窗口显示AI补全结果
        if self.ai_completions:
            self.candidate_window.show_ai_suggestions(self.ai_completions)
            self.move_candidate_window()

    def on_ai_error(self, error_msg: str):
        """处理AI错误。
        
        Args:
            error_msg: 错误信息
        """
        print(f"AI请求错误: {error_msg}")
        # 可以考虑显示错误信息给用户
    
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
            
            # 处理数字键（选择候选词）
            if is_digit_char(key):
                if (self.is_active and self.candidates) or (self.is_ai_mode and self.ai_completions):
                    digit = int(get_key_char(key))
                    print(f"Digit key pressed: {digit}")
                    if self.is_ai_mode and self.ai_completions and 1 <= digit <= len(self.ai_completions):
                        print(f"Selecting AI completion {digit-1}: {self.ai_completions[digit-1]}")
                        self.select_candidate(digit - 1)
                        return True  # 阻止数字键传播
                    elif self.is_active and self.candidates and 1 <= digit <= len(self.candidates):
                        print(f"Selecting candidate {digit-1}: {self.candidates[digit-1]}")
                        self.select_candidate(digit - 1)
                        return True  # 阻止数字键传播
                # 如果输入法未激活或没有候选词，则不处理，让数字键正常输入
                return False

            # 处理字母键（拼音输入）
            if is_alpha_char(key):
                # 如果在AI模式下，先退出AI模式
                if self.is_ai_mode:
                    self.exit_ai_mode()
                    
                char = get_key_char(key).lower()
                self.pinyin_buffer += char
                self.update_candidates()
                self.is_active = True
                print(f"Added char '{char}' to buffer: '{self.pinyin_buffer}'")
                return suppress_key
            
            # 处理方向键（选择候选词和翻页）
            elif key == keyboard.Key.left:
                if self.is_active and self.candidates and not self.is_ai_mode:
                    self.candidate_window.select_previous()
                    return True
                elif self.is_active and self.candidates and self.is_ai_mode:
                    self.candidate_window.select_previous()
                    return True
                return False
                
            elif key == keyboard.Key.right:
                if self.is_active and self.candidates and not self.is_ai_mode:
                    self.candidate_window.select_next()
                    return True
                elif self.is_active and self.candidates and self.is_ai_mode:
                    self.candidate_window.select_next()
                    return True
                return False
                
            elif key == keyboard.Key.up:
                if self.is_ai_mode and self.ai_completions:
                    self.candidate_window.select_previous_ai()
                    return True
                return False
                
            elif key == keyboard.Key.down:
                if self.is_ai_mode and self.ai_completions:
                    self.candidate_window.select_next_ai()
                    return True
                return False
            
            # 处理Tab键（仅处理双击Tab）
            elif key == keyboard.Key.tab:
                print(f"Tab key pressed - Active: {self.is_active}, Candidates: {len(self.candidates)}")
                
                # 检测双击Tab事件
                current_time = time.time()
                if (current_time - self.last_tab_time) < self.tab_double_click_interval:
                    # 双击Tab事件
                    self.handle_tab_double_click()
                    self.last_tab_time = 0  # 重置时间，避免连续触发
                    # 双击Tab时不自动输入候选词，直接返回
                    return True
                
                # 单击Tab事件，记录时间
                self.last_tab_time = current_time
                
                # 单击Tab不再确认候选词，直接返回
                print("Tab key - single click, no action")
                return False  # 让Tab键正常传播
            
            # 处理空格键（确认第一个候选词或输入空格）
            elif key == keyboard.Key.space:
                if self.is_ai_mode and self.ai_completions:
                    print(f"Space selecting first AI completion: {self.ai_completions[0]}")
                    self.select_candidate(0)
                    return True  # 阻止空格键传播
                elif self.is_active and self.candidates:
                    print(f"Space selecting first candidate: {self.candidates[0]}")
                    self.select_candidate(0)
                    return True  # 阻止空格键传播
                else:
                    # 让空格键正常传播（输入空格）
                    return False
            
            # 处理回车键（确认第一个候选词或换行）
            elif key == keyboard.Key.enter:
                if self.is_ai_mode and self.ai_completions:
                    self.select_candidate(0)
                    return True  # 阻止回车键传播
                elif self.is_active and self.candidates:
                    self.select_candidate(0)
                    return True  # 阻止回车键传播
                else:
                    # 让回车键正常传播
                    return False
            
            # 处理退格键
            elif key == keyboard.Key.backspace:
                # 如果在AI模式下，退出AI模式
                if self.is_ai_mode:
                    self.exit_ai_mode()
                    return True  # 阻止退格键传播
                elif self.is_active and self.pinyin_buffer:
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
                # 如果在AI模式下，退出AI模式
                if self.is_ai_mode:
                    self.exit_ai_mode()
                    return True  # 阻止ESC键传播
                elif self.is_active:
                    self.deactivate()
                    return True  # 阻止ESC键传播
                else:
                    return False
            
            # 其他键（如标点符号等）
            else:
                # 如果在AI模式下，退出AI模式
                if self.is_ai_mode:
                    self.exit_ai_mode()
                elif self.is_active:
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
            self.full_candidates = []
            self.current_page = 0
            self.candidate_window.hide()
            return
        
        # 获取候选词
        self.full_candidates = self.pinyin_engine.get_candidates(self.pinyin_buffer)
        self.current_page = 0
        self.show_current_page_candidates()
        
    def show_current_page_candidates(self):
        """显示当前页的候选词。"""
        if not self.full_candidates:
            self.candidates = []
            self.candidate_window.hide()
            return
        
        start_index = self.current_page * self.page_size
        end_index = min(start_index + self.page_size, len(self.full_candidates))
        self.candidates = self.full_candidates[start_index:end_index]
        
        total_pages = (len(self.full_candidates) + self.page_size - 1) // self.page_size
        
        if self.candidates:
            # 显示候选词窗口
            self.candidate_window.update_candidates(
                self.candidates,
                current_page=self.current_page,
                total_pages=total_pages
            )
            self.move_candidate_window()
        else:
            # 如果当前页没有候选词（可能发生在最后一页之后），尝试回到上一页
            if self.current_page > 0:
                self.current_page -= 1
                self.show_current_page_candidates()
            else:
                self.candidate_window.hide()
    
    def select_candidate(self, index: int):
        """选择候选词。
        
        Args:
            index: 候选词索引
        """
        if self.is_ai_mode:
            # AI模式下选择AI补全结果
            if 0 <= index < len(self.ai_completions):
                selected_completion = self.ai_completions[index]
                print(f"选择AI补全结果 {index}: '{selected_completion}'")
                
                # 清除拼音缓冲区中的字符
                self.clear_pinyin_buffer()
                
                # 使用延迟确保清除操作完成
                QTimer.singleShot(50, lambda: self.input_text_delayed(selected_completion))
                
                # 记录最近输入的内容
                self.last_input_text = selected_completion
                self.last_input_pinyin = ""
                
                # 退出AI模式并重置状态
                self.exit_ai_mode()  # 确保这里正确退出AI模式
                print(f"成功选择AI补全结果: '{selected_completion}'")
        else:
            # 普通模式下选择候选词
            if 0 <= index < len(self.candidates):
                absolute_index = self.current_page * self.page_size + index
                selected_word = self.full_candidates[absolute_index]
                print(f"Selecting candidate {index} (absolute {absolute_index}): '{selected_word}'")
                
                # 清除拼音缓冲区中的字符
                self.clear_pinyin_buffer()
                
                # 使用延迟确保清除操作完成
                QTimer.singleShot(50, lambda: self.input_text_delayed(selected_word))
                
                # 记录最近输入的内容
                self.last_input_text = selected_word
                self.last_input_pinyin = self.pinyin_buffer
                
                # 清空状态
                self.reset_state()  # 确保这里正确重置状态
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
    
    def exit_ai_mode(self):
        """退出AI模式，恢复普通候选词显示。"""
        self.is_ai_mode = False
        self.ai_completions = []
        # 重新显示普通候选词
        self.show_current_page_candidates()
        self.candidate_window.ai_suggestion_frame.hide()  # 确保隐藏AI建议框
    
    def reset_state(self):
        """重置输入状态。"""
        self.pinyin_buffer = ""
        self.candidates = []
        self.full_candidates = []
        self.current_page = 0
        self.is_active = False
        self.is_ai_mode = False
        self.ai_completions = []
        self.candidate_window.hide()
        # 注意：不清除last_input_text和last_input_pinyin，以便双击Tab时使用
    
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
    
    def clean_text_for_ai(self, text: str) -> str:
        """清理发送给AI的文本，移除可能导致问题的特殊字符。

        Args:
            text (str): 需要清理的文本

        Returns:
            str: 清理后的文本
        """
        # 移除特殊字符，只保留字母、数字和常见标点符号
        cleaned_text = re.sub(r'[^\w\s.,!?]', '', text)
        return cleaned_text.strip()

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
