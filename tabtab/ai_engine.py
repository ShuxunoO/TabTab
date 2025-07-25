# tabtab/ai_engine.py
"""AI引擎，负责调用Ollama服务获取文本补全建议。"""

import ast
from ollama import Client
from typing import List
from PyQt6.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool

class AICompletionWorker(QRunnable):
    """在后台线程中运行AI补全的Worker。"""
    
    def __init__(self, text: str):
        super().__init__()
        self.text = text
        self.signals = self.WorkerSignals()

    class WorkerSignals(QObject):
        """定义此Worker可发出的信号。"""
        finished = pyqtSignal(list)
        error = pyqtSignal(str)

    def run(self):
        """执行AI补全任务。"""
        try:
            client = Client()
            prompt = (
                f"请继续补全剩下的文本，不要提供任何解释或多余的文字，只返回补全的内容，"
                f"要求返回3条补全之后的对话，结果以list的形式返回，格式为：[respone1, response2, response3]. "
                f"注意：1. 只要3条内容，不能多也不能少；2. 3条内容要各不相同，尽可能差异化；"
                f"3. 每条回复必须少于30个字；4. 用户很有可能会输入错别字和模糊拼音，根据你常识纠正补全的内容，"
                f"用户的输入是：{self.text}"
            )
            response = client.chat(model='qwen2.5:0.5b', messages=[
                {'role': 'user', 'content': prompt}
            ])
            
            content = response.get("message", {}).get("content", "")
            
            # 使用ast.literal_eval安全地解析字符串为列表
            completions = ast.literal_eval(content)
            
            if isinstance(completions, list) and len(completions) == 3:
                self.signals.finished.emit(completions)
            else:
                # 如果不符合要求，尝试简单分割
                if isinstance(content, str):
                    # 尝试用换行符分割，并取前3个
                    fallback_completions = [c.strip() for c in content.split('\n') if c.strip()][:3]
                    if len(fallback_completions) > 0:
                         self.signals.finished.emit(fallback_completions)
                    else:
                        self.signals.error.emit("AI返回格式不正确或内容为空")
                else:
                    self.signals.error.emit("AI返回格式不正确")
                
        except Exception as e:
            self.signals.error.emit(f"AI请求失败: {e}")


class AIEngine(QObject):
    """AI引擎，用于从Ollama获取补全建议。"""
    
    completions_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """初始化AI引擎。"""
        super().__init__(parent)
        self.thread_pool = QThreadPool()
        print("AI Engine initialized.")

    def get_completions(self, text: str):
        """异步获取AI补全建议。
        
        Args:
            text: 用户输入的文本
        """
        worker = AICompletionWorker(text)
        worker.signals.finished.connect(self.completions_ready.emit)
        worker.signals.error.connect(self.error_occurred.emit)
        self.thread_pool.start(worker)
