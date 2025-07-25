# tabtab/pinyin_engine.py
from pypinyin import pinyin, Style
from dictionary_manager import DictionaryManager

class PinyinEngine:
    """拼音处理引擎，负责将拼音转换为汉字候选词。

    该类集成了pypinyin库和自定义的DictionaryManager，
    为输入的拼音字符串提供候选汉字列表。
    """
    def __init__(self):
        """PinyinEngine的构造函数。

        初始化词典管理器。在实际应用中，这里可以加载配置文件指定的词库。
        """
        self.dict_manager = DictionaryManager()

    def get_candidates(self, pinyin_str):
        """根据拼音字符串获取候选词列表。

        查询顺序:
        1. 首先在自定义词典中查找完全匹配的词语。
        2. 然后使用pypinyin库获取单字候选。
        3. 添加一些硬编码的常用词作为补充。
        最终返回去重后的前5个候选词。

        Args:
            pinyin_str (str): 用户输入的拼音字符串。

        Returns:
            list[str]: 候选汉字或词语的列表。
        """
        if not pinyin_str:
            return []
        
        candidates = []
        
        # 1. 首先检查自定义词典
        custom_word = self.dict_manager.lookup(pinyin_str)
        if custom_word:
            candidates.append(custom_word)

        # 2. 使用pypinyin获取单字候选
        try:
            # heteronym=True以获取多音字
            result = pinyin(pinyin_str, style=Style.NORMAL, heteronym=True)
            if result:
                # pypinyin返回的是一个列表的列表，如[['cè'], ['shì']]
                # 我们简单地将所有可能性平铺展开
                flat_list = [char for sublist in result for char in sublist]
                unique_chars = sorted(list(set(flat_list)), key=flat_list.index)
                candidates.extend(unique_chars)
        except Exception as e:
            print(f"Pypinyin error: {e}")

        # 3. 为演示目的，添加一些硬编码的候选词
        if pinyin_str == "nihao":
            # 将常用词插入到列表开头，提高其优先级
            candidates.insert(0, "你好") 
            candidates.append("您好")
        
        # 去重并保持顺序，返回前5个结果
        seen = set()
        return [x for x in candidates if not (x in seen or seen.add(x))][:5]

if __name__ == '__main__':
    # 用于独立测试PinyinEngine的脚本
    engine = PinyinEngine()
    # 为测试创建一个虚拟的词典条目
    engine.dict_manager.word_dict['ceshi'] = '测试'
    
    print(f"Candidates for 'a': {engine.get_candidates('a')}")
    print(f"Candidates for 'nihao': {engine.get_candidates('nihao')}")
    print(f"Candidates for 'ceshi': {engine.get_candidates('ceshi')}")
