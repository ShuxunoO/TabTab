# tabtab/input_manager.py
from pynput import keyboard
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from pinyin_engine import PinyinEngine
from ai_client import AIClient
import pyautogui
import ctypes

class KeyboardListener(QObject):
    """在独立线程中监听全局键盘事件的QObject。

    为了避免pynput阻塞主GUI线程，该监听器在一个单独的QThread中运行。
    它通过发出keyPressed信号，将键盘事件安全地传递给主线程进行处理。
    """
    keyPressed = pyqtSignal(object)

    def __init__(self, parent=None):
        """KeyboardListener的构造函数。

        Args:
            parent (QObject, optional): 父对象。默认为None。
        """
        super().__init__(parent)
        self.listener = None

    def start_listening(self):
        """启动键盘监听。

        创建并启动pynput的Listener。
        """
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()

    def on_press(self, key):
        """pynput的回调函数，当按键被按下时调用。

        此方法在pynput的监听线程中被调用，它只做一件事：发出keyPressed信号。

        Args:
            key (object): 捕获到的按键对象。
        """
        self.keyPressed.emit(key)

    def stop_listening(self):
        """停止键盘监听。"""
        if self.listener:
            self.listener.stop()

class InputManager(QObject):
    def __init__(self, candidate_window, parent=None):
        super().__init__(parent)
        self.buffer = ""
        self.input_text = ""
        self.pinyin_engine = PinyinEngine()
        self.candidate_window = candidate_window
        
        # This will be the single source of truth for what's displayed.
        self.display_candidates = [] 
        # Keep track of pinyin candidates separately for buffer clearing logic
        self.pinyin_candidates = [] 
        self.ai_completion = ""

        self.ai_client = AIClient(parent=self)
        self.ai_client.worker.response_ready.connect(self.on_ai_response)

        self.listener_thread = QThread(self)
        self.keyboard_listener = KeyboardListener()
        self.keyboard_listener.moveToThread(self.listener_thread)
        
        self.listener_thread.started.connect(self.keyboard_listener.start_listening)
        self.keyboard_listener.keyPressed.connect(self.on_press)
        
        self.listener_thread.start()
        # 新增：Tab键双击检测
        self.last_tab_time = 0
        self.tab_click_count = 0
        self.tab_double_click_interval = 0.4  # 秒

    def on_press(self, key):
        """处理按键事件的主槽函数。"""
        import time
        try:
            # Handle alphanumeric for pinyin buffer
            if key.char and 'a' <= key.char <= 'z':
                self.buffer += key.char
                self._update_candidates()
            # Handle candidate selection
            elif key.char and '1' <= key.char <= '9':
                self.select_candidate(int(key.char) - 1)
            # Handle space key
            elif key == keyboard.Key.space:
                # If there are pinyin candidates, select the first one
                if self.buffer and self.pinyin_candidates:
                    self.select_candidate(0)
                # Otherwise, type a space and get AI completion
                else:
                    pyautogui.typewrite(' ')
                    self.input_text += ' '
                    self._reset_buffer() # Clear buffer and hide window
                    self.ai_client.request_completion(self.input_text)
            # Handle Tab key: 单击Tab写入第一候选，双击Tab写入AI补全
            elif key == keyboard.Key.tab:
                now = time.time()
                if now - self.last_tab_time < self.tab_double_click_interval:
                    self.tab_click_count += 1
                else:
                    self.tab_click_count = 1
                self.last_tab_time = now
                if self.tab_click_count == 2:
                    # 双击Tab，强制AI补全
                    self.accept_ai_completion()
                    self.tab_click_count = 0
                elif self.tab_click_count == 1:
                    # 单击Tab，写入第一候选（AI或拼音）
                    if self.display_candidates:
                        self.select_candidate(0)
            # Handle backspace
            elif key == keyboard.Key.backspace:
                if self.buffer:
                    self.buffer = self.buffer[:-1]
                    self._update_candidates()
                else:
                    # Simulate backspace in the application
                    pyautogui.press('backspace')
                    # Update internal text state
                    if self.input_text:
                        self.input_text = self.input_text[:-1]
                    # Request new AI completion with the updated text
                    self.ai_client.request_completion(self.input_text)
            # Handle Esc to clear buffer
            elif key == keyboard.Key.esc:
                self._reset_buffer()
            # Handle punctuation and enter to finalize input and get AI completion
            elif key == keyboard.Key.enter or (hasattr(key, 'char') and key.char in [',', '.', '?', '!']):
                # 优先写入候选内容
                if self.display_candidates:
                    self.select_candidate(0)
                elif self.buffer:
                    pyautogui.typewrite(self.buffer)
                    self.input_text += self.buffer
                    self._reset_buffer()
                
                # Type the punctuation if it's a character
                if hasattr(key, 'char'):
                    pyautogui.typewrite(key.char)
                    self.input_text += key.char
                
                if self.input_text:
                    self.ai_client.request_completion(self.input_text)
                
                # Hide candidate window
                self._update_candidates()

        except AttributeError:
            # Ignore keys without a 'char' attribute if not handled above (e.g., Shift, Ctrl)
            pass

    def _update_candidates(self):
        """更新候选词窗口。"""
        self.display_candidates = []
        self.pinyin_candidates = []

        # Add AI completion first if available
        if self.ai_completion:
            # We store the raw completion text, but display it with a prefix
            self.display_candidates.append(self.ai_completion)

        # Add pinyin candidates if buffer is active
        if self.buffer:
            self.pinyin_candidates = self.pinyin_engine.get_candidates(self.buffer)
            self.display_candidates.extend(self.pinyin_candidates)
        
        # Prepare candidates for display with numbers and prefixes
        numbered_display = []
        if self.ai_completion:
            # The first candidate is AI
            numbered_display.append(f"1. [AI] {self.display_candidates[0]}")
            # The rest are pinyin candidates
            for i, cand in enumerate(self.display_candidates[1:]):
                numbered_display.append(f"{i+2}. {cand}")
        else:
            # All candidates are from pinyin
            for i, cand in enumerate(self.display_candidates):
                numbered_display.append(f"{i+1}. {cand}")

        if numbered_display:
            self.candidate_window.update_candidates(numbered_display)
            self._move_candidate_window()
        else:
            self.candidate_window.hide()

    def select_candidate(self, index):
        """选择候选词。"""
        if not (0 <= index < len(self.display_candidates)):
            return

        selected_word = self.display_candidates[index]
        is_ai_completion = self.ai_completion and selected_word == self.ai_completion

        if is_ai_completion:
            # If user selects the AI completion by number
            self.accept_ai_completion()
        else:
            # It's a pinyin candidate
            # Clear the pinyin buffer from the input field
            for _ in range(len(self.buffer)):
                pyautogui.press('backspace')
            
            # Type the selected word
            pyautogui.typewrite(selected_word)
            self.input_text += selected_word
            
            # Reset pinyin state and request next AI completion
            self._reset_buffer()
            self.ai_client.request_completion(self.input_text)

    def accept_ai_completion(self):
        """接受 AI 补全建议。"""
        if not self.ai_completion:
            return
            
        # If there's a pinyin buffer, clear it first
        if self.buffer:
            for _ in range(len(self.buffer)):
                pyautogui.press('backspace')

        pyautogui.typewrite(self.ai_completion)
        self.input_text += self.ai_completion
        self.ai_completion = ""
        self._reset_buffer()
        # Request the next completion
        self.ai_client.request_completion(self.input_text)

    def on_ai_response(self, completion):
        """处理 AI 补全响应。"""
        self.ai_completion = completion.strip() # Clean up response
        self._update_candidates()

    def _reset_buffer(self):
        """重置输入缓冲区和相关状态。"""
        self.buffer = ""
        self.pinyin_candidates = []
        # Don't clear AI completion here, let it persist until the next action
        self._update_candidates()

    def _move_candidate_window(self):
        """移动候选词窗口到光标位置。"""
        x, y = self.get_cursor_position()
        self.candidate_window.move_window(x, y)

    def get_cursor_position(self):
        """获取当前光标位置。"""
        try:
            ci = ctypes.wintypes.GUITHREADINFO(cbSize=ctypes.sizeof(ctypes.wintypes.GUITHREADINFO))
            ctypes.windll.user32.GetGUIThreadInfo(0, ctypes.byref(ci))
            return ci.rcCaret.left, ci.rcCaret.bottom
        except Exception:
            return 800, 400

    def stop(self):
        """停止输入法管理器。"""
        self.keyboard_listener.stop_listening()
        self.listener_thread.quit()
        self.listener_thread.wait()