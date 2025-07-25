# tabtab/pinyin_engine.py
"""拼音处理引擎，负责将拼音转换为汉字候选词。

该类集成了pypinyin库和自定义的DictionaryManager，
为输入的拼音字符串提供候选汉字列表。
"""

from pypinyin import pinyin, Style
from dictionary_manager import DictionaryManager
from typing import List


class PinyinEngine:
    """拼音处理引擎，负责将拼音转换为汉字候选词。"""
    
    def __init__(self):
        """初始化拼音引擎。"""
        self.dict_manager = DictionaryManager()
    
    def segment(self, pinyin_str: str) -> List[str]:
        """使用动态规划对拼音字符串进行分词。
        
        Args:
            pinyin_str: 用户输入的拼音字符串
            
        Returns:
            一个或多个分词后的候选词语组合
        """
        n = len(pinyin_str)
        dp = [[] for _ in range(n + 1)]
        dp[0] = [""]

        for i in range(1, n + 1):
            for j in range(i):
                sub_pinyin = pinyin_str[j:i]
                words = self.dict_manager.lookup(sub_pinyin)
                if words and dp[j]:
                    for word in words:
                        for prev_word in dp[j]:
                            # 限制候选词数量，避免组合爆炸
                            if len(dp[i]) < 10:
                                dp[i].append(f"{prev_word}{word}")
        
        return dp[n]

    def get_candidates(self, pinyin_str: str) -> List[str]:
        """根据拼音字符串获取候选词列表。
        
        查询顺序:
        1. 首先使用分词算法获取整词候选
        2. 然后在自定义词典中查找完全匹配的词语
        3. 使用pypinyin库获取单字候选
        4. 添加一些硬编码的常用词作为补充
        
        Args:
            pinyin_str: 用户输入的拼音字符串
            
        Returns:
            候选汉字或词语的列表
        """
        if not pinyin_str:
            return []
        
        candidates = []

        # 1. 使用分词算法获取候选
        segmented_candidates = self.segment(pinyin_str)
        candidates.extend(segmented_candidates)
        
        # 2. 检查自定义词典
        dict_candidates = self.dict_manager.get_candidates(pinyin_str, 5)
        candidates.extend(dict_candidates)
        
        # 3. 使用pypinyin获取单字候选
        try:
            # 获取每个字符的拼音
            result = pinyin(pinyin_str, style=Style.NORMAL, heteronym=True)
            if result:
                # 简单处理：取第一个字符的所有可能读音
                for char_pinyins in result[:1]:  # 只处理第一个字符
                    for char_pinyin in char_pinyins:
                        if char_pinyin not in candidates:
                            candidates.append(char_pinyin)
        except Exception as e:
            print(f"Pypinyin error: {e}")
        
        # 4. 添加硬编码的常用候选词
        common_mappings = {
            'ni': ['你', '尼', '泥'],
            'hao': ['好', '号', '毫'],
            'nihao': ['你好'],
            'wo': ['我', '窝'],
            'ta': ['他', '她', '它'],
            'de': ['的', '得', '地'],
            'shi': ['是', '时', '十'],
            'zai': ['在', '再'],
            'you': ['有', '又', '右'],
            'le': ['了', '乐'],
            'yi': ['一', '已', '以'],
            'ge': ['个', '格'],
            'ren': ['人', '任'],
            'shang': ['上', '商'],
            'xia': ['下', '夏'],
            'zhong': ['中', '重'],
            'guo': ['国', '过'],
            'da': ['大', '达'],
            'xiao': ['小', '笑'],
            'shui': ['水', '谁'],
        }
        
        if pinyin_str in common_mappings:
            for word in common_mappings[pinyin_str]:
                if word not in candidates:
                    candidates.append(word)
        
        # 去重并保持顺序，返回前8个结果
        seen = set()
        unique_candidates = []
        for candidate in candidates:
            if candidate not in seen:
                seen.add(candidate)
                unique_candidates.append(candidate)
        
        return unique_candidates[:8]


if __name__ == '__main__':
    # 测试拼音引擎
    engine = PinyinEngine()
    
    test_cases = ['ni', 'hao', 'nihao', 'wo', 'de', 'shi', 'zhongguo', 'nihaoma']
    for test in test_cases:
        candidates = engine.get_candidates(test)
        print(f"'{test}': {candidates}")
