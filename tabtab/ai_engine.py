# tabtab/ai_engine.py
"""AI引擎，负责调用Ollama服务获取文本补全建议。"""

import ast
import re
from ollama import Client
from typing import List
from PyQt6.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool
import datetime


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
        print("用户输入:", self.text)
        
        try:
            client = Client()
            datetime_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            prompt = (
               """ 用户的输入是：‘{user_input}’，请继续补全或者回答剩下的对话，不要提供任何解释或多余的文字，只返回补全的内容。
                要求返1个string list，list中包含三个字符串，格式为：['response1', 'response2', 'response3'].
                注意：
                1. 只要3条内容，不能多也不能少；
                2. 3条内容要各不相同，尽可能差异化；
                3. 每条回复必须少于30个字；
                4. 用户很有可能会输入错别字和模糊拼音，根据你常识纠正补全的内容。
                5. 当前的时间是：{datetime}。
                """.format(user_input=self.text, datetime=datetime_str)
            )

            print("AI请求内容:", prompt)
            response = client.chat(model='qwen2.5:3b', messages=[
                {'role': 'user', 'content': prompt}
            ])
            
            content = response.get("message", {}).get("content", "")
            print("AI原始返回内容:", content)
            
            # 尝试多种解析方式
            completions = self._parse_completions(content)
            
            if completions and isinstance(completions, list) and len(completions) > 0:
                # 确保最多只返回3个结果
                completions = completions[:3]
                self.signals.finished.emit(completions)
            else:
                self.signals.error.emit("AI返回格式不正确或内容为空")
                
        except Exception as e:
            self.signals.error.emit(f"AI请求失败: {e}")

    def _parse_completions(self, content: str) -> List[str]:
        """解析AI返回的内容。
        
        Args:
            content: AI返回的原始内容
            
        Returns:
            解析后的补全列表
        """
        # 方法1: 直接使用ast.literal_eval
        try:
            completions = ast.literal_eval(content)
            if isinstance(completions, list):
                return completions
        except:
            pass
        
        # 方法2: 尝试提取方括号内的内容再解析
        try:
            # 使用正则表达式提取类似 [item1, item2, item3] 的内容
            match = re.search(r'\[(.*?)\]', content, re.DOTALL)
            if match:
                list_content = f"[{match.group(1)}]"
                completions = ast.literal_eval(list_content)
                if isinstance(completions, list):
                    return completions
        except:
            pass
        
        # 方法3: 尝试按行分割
        try:
            if isinstance(content, str):
                # 按行分割并清理内容
                lines = [line.strip(' \n\r\t"\'') for line in content.split('\n') if line.strip()]
                # 过滤掉空行和无用行
                filtered_lines = [line for line in lines if line and not line.startswith('[') and not line.endswith(']')]
                if filtered_lines:
                    # 取前3个非空行
                    return filtered_lines[:3]
        except:
            pass
        
        # 方法4: 尝试提取引号内的内容
        try:
            # 匹配引号内的内容
            quoted_items = re.findall(r'["\']([^"\']*)["\']', content)
            if quoted_items:
                # 过滤掉空内容
                non_empty_items = [item for item in quoted_items if item.strip()]
                if non_empty_items:
                    return non_empty_items[:3]
        except:
            pass
        
        return []

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
