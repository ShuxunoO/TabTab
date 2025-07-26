# tabtab/pinyin_engine.py
"""拼音处理引擎，负责将拼音转换为汉字候选词。

该类集成了pypinyin库和自定义的DictionaryManager，
为输入的拼音字符串提供候选汉字列表。
"""

from pypinyin import pinyin, Style
from dictionary_manager import DictionaryManager
from typing import List, Tuple
import re


class PinyinEngine:
    """拼音处理引擎，负责将拼音转换为汉字候选词。"""
    
    def __init__(self):
        """初始化拼音引擎。"""
        self.dict_manager = DictionaryManager()
        # 定义常用短语，用于优先匹配
        self.common_phrases = {
            # 日常问候
            'nihao': ['你好', '您好', '你好啊'],
            'xiexie': ['谢谢', '感谢', '谢了'],
            'duibuqi': ['对不起', '抱歉', '不好意思'],
            'meiguanxi': ['没关系', '没事', '不要紧'],
            
            # 常用表达
            'shenme': ['什么', '啥', '什么东西'],
            'zenme': ['怎么', '怎样', '怎么办'],
            'weishenme': ['为什么', '为啥', '怎么会'],
            'zaijianshuo': ['再见', '拜拜', '下次见'],
            'qingwen': ['请问', '麻烦问一下', '想问一下'],
            'keyi': ['可以', '行', '能够'],
            'bukeyi': ['不可以', '不行', '不能'],
            'xiangyao': ['想要', '需要', '希望'],
            'buxiang': ['不想', '不愿意', '不想做'],
            'meiyou': ['没有', '没', '无'],
            'youmeiyou': ['有没有', '有吗', '是不是有'],
            'shiyong': ['使用', '用', '运用'],
            'bangzhu': ['帮助', '帮忙', '协助'],
            'jiushi': ['就是', '正是', '便是'],
            'bushi': ['不是', '并非', '并不是'],
            'keyong': ['可用', '能用', '管用'],
            'buneng': ['不能', '无法', '不可'],
            'yiding': ['一定', '必定', '肯定'],
            'keyi': ['可以', '可行', '能够'],
            'buke': ['不可', '不行', '不可以'],
            'zenmeyang': ['怎么样', '如何', '怎样'],
            'kaolv': ['考虑', '思考', '思索'],
            'jueding': ['决定', '确定', '选定'],
            'xihuan': ['喜欢', '喜爱', '爱好'],
            'buxihuan': ['不喜欢', '讨厌', '厌恶'],
            'jintian': ['今天', '当日', '这天'],
            'mingtian': ['明天', '明日', '第二天'],
            'zuotian': ['昨天', '昨日', '前一天'],
            'xianzai': ['现在', '目前', '此刻'],
            'yihou': ['以后', '之后', '随后'],
            'yiqian': ['以前', '之前', '从前'],
            'shangban': ['上班', '工作', '上班时间'],
            'xiaban': ['下班', '收工', '下班时间'],
            'chifan': ['吃饭', '用餐', '就餐'],
            'shuijiao': ['睡觉', '睡眠', '休息'],
            'qichuang': ['起床', '起来', '起床时间'],
            'shangche': ['上车', '乘车', '登车'],
            'xiache': ['下车', '落地', '抵达'],
            'kaishi': ['开始', '启动', '着手'],
            'jieshu': ['结束', '完成', '完毕'],
            'jixu': ['继续', '接着', '延续'],
            'tingzhi': ['停止', '停下', '终止'],
            'zhiding': ['制定', '制订', '拟定'],
            'zhixing': ['执行', '实施', '实行'],
            'wancheng': ['完成', '达成', '实现'],
            'jinxing': ['进行', '开展', '展开'],
            'fabu': ['发布', '公布', '发表'],
            'shouji': ['收集', '搜集', '采集'],
            'fenxi': ['分析', '解析', '剖析'],
            'jieshi': ['解释', '说明', '阐述'],
            'biaoda': ['表达', '表述', '表示'],
            'qingqiu': ['请求', '要求', '申请'],
            'tongyi': ['同意', '答应', '许可'],
            'jvju': ['拒绝', '回绝', '谢绝'],
            'lianjie': ['联系', '联络', '沟通'],
            'huifu': ['回复', '回应', '答复'],
            'fasong': ['发送', '传送', '发出'],
            'jieshou': ['接收', '接受', '收受'],
            'bianji': ['编辑', '修改', '更改'],
            'shanchu': ['删除', '去掉', '清除'],
            'chakan': ['查看', '查阅', '浏览'],
            'sousuo': ['搜索', '查找', '检索'],
            'xiugai': ['修改', '更改', '修正'],
            'baocun': ['保存', '储存', '存储'],
            'daoru': ['导入', '引进', '引入'],
            'daochu': ['导出', '输出', '引出'],
            'shangchuan': ['上传', '上载', '传送'],
            'xiazai': ['下载', '获取', '取得'],
            'anzhuang': ['安装', '装配', '装置'],
            'xiezai': ['卸载', '移除', '删除'],
            'qidong': ['启动', '开启', '打开'],
            'guanbi': ['关闭', ' shut down', '关掉'],
            'chongqi': ['重启', '重新启动', '重新开机'],
            'shuaxin': ['刷新', '更新', '重载'],
            'tiaozheng': ['调整', '调节', '校准'],
            'shezhi': ['设置', '设定', '配置'],
            'jiancha': ['检查', '检测', '查验'],
            'ceshi': ['测试', '检验', '试验'],
            'xiufu': ['修复', '修理', '修补'],
            'gengxin': ['更新', '升级', '刷新'],
            'beifen': ['备份', '拷贝', '复制'],
            'huanyuan': ['还原', '恢复', '复原'],
            'qingchu': ['清除', '清理', '清洁'],
            'zhongzhi': ['终止', '中止', '停止'],
            'quxiao': ['取消', '撤销', '废除'],
            'queren': ['确认', '确定', '核实'],
            'tijiao': ['提交', '递交', '呈交'],
            'fanhui': ['返回', '回去', '回退'],
            'zhuanhuan': ['转换', '转化', '变换'],
            'bianhuan': ['变化', '改变', '变动'],
            'tongzhi': ['通知', '告知', '通告'],
            'tixing': ['提醒', '提示', '警示'],
            'jilu': ['记录', '记载', '登记'],
            'chaxun': ['查询', '查找', '检索'],
            'daochu': ['导出', '输出', '引出'],
            'daoru': ['导入', '引进', '引入'],
            'fenxiang': ['分享', '共享', '分发'],
            'shoucang': ['收藏', '珍藏', '保存'],
            'pinglun': ['评论', '评价', '点评'],
            'dianzan': ['点赞', '赞', '支持'],
            'zhuanfa': ['转发', '转播', '传播'],
            'guanzhu': ['关注', '关心', '留意'],
            'quguan': ['取关', '取消关注', '不再关注'],
            'liaotian': ['聊天', '交谈', '对话'],
            'fasong': ['发送', '传送', '发出'],
            'jieshou': ['接收', '接受', '收受'],
            'huifu': ['回复', '回应', '答复'],
            'shanchu': ['删除', '去掉', '清除'],
            'bianji': ['编辑', '修改', '更改'],
            'chakan': ['查看', '查阅', '浏览'],
            'sousuo': ['搜索', '查找', '检索'],
            'xiugai': ['修改', '更改', '修正'],
            'baocun': ['保存', '储存', '存储'],
            'tuichu': ['退出', '登出', '注销'],
            'denglu': ['登录', '登入', '登陆'],
            'zhuce': ['注册', '开户', '建立'],
            'wangji': ['忘记', '遗忘', '忘掉'],
            'chongzhi': ['重置', '复位', '恢复默认'],
            'xiugai': ['修改', '更改', '变更'],
            'genggai': ['更改', '改变', '变更'],
            'bianji': ['编辑', '编排', '编纂'],
            'chaxun': ['查询', '查问', '查访'],
            'jilu': ['记录', '纪录', '记载'],
            'tongji': ['统计', '汇总', '计算'],
            'fenlei': ['分类', '归类', '划分'],
            'shaixuan': ['筛选', '过滤', '挑选'],
            'paixu': ['排序', '排列', '整理'],
            'daochu': ['导出', '输出', '引出'],
            'daoru': ['导入', '引进', '引入'],
            'shangchuan': ['上传', '上载', '传送'],
            'xiazai': ['下载', '获取', '取得'],
            'yulan': ['预览', '预观', '先行观看'],
            'dayin': ['打印', '印刷', '输出'],
            'faxian': ['发现', '发觉', '找到'],
            'jiansuo': ['检索', '搜索', '查找'],
            'dingwei': ['定位', '确定位置', '锁定'],
            'daohang': ['导航', '引领', '指引'],
            'ditu': ['地图', '图示', '地形图'],
            'luxian': ['路线', '路径', '道路'],
            'juli': ['距离', '间距', '长度'],
            'shijian': ['时间', '时刻', '时段'],
            'didian': ['地点', '场所', '位置'],
            'dizhi': ['地址', '住址', '所在地'],
            'weizhi': ['位置', '地点', '方位'],
            'zuobiao': ['坐标', '座标', '定位点'],
            'fangxiang': ['方向', '方位', '指向'],
            'nanfang': ['南方', '南部', '南边'],
            'beifang': ['北方', '北部', '北边'],
            'dongfang': ['东方', '东部', '东边'],
            'xifang': ['西方', '西部', '西边'],
            'zhongxin': ['中心', '中央', '核心'],
            'zuoshang': ['左上', '左上方', '西北'],
            'youshang': ['右上', '右上方', '东北'],
            'zuoxia': ['左下', '左下方', '西南'],
            'youxia': ['右下', '右下方', '东南'],
            'shangmian': ['上面', '上边', '上方'],
            'xiamian': ['下面', '下边', '下方'],
            'zuobian': ['左边', '左侧', '左方'],
            'youbian': ['右边', '右侧', '右方'],
            'qianmian': ['前面', '前方', '前边'],
            'houmian': ['后面', '后方', '后边'],
            'linjin': ['临近', '靠近', '接近'],
            'yuandian': ['远点', '远处', '远方'],
            'fujin': ['附近', '周边', '周围'],
            'zhoubian': ['周边', '周围', '四周'],
            'neibu': ['内部', '内侧', '里面'],
            'waibu': ['外部', '外侧', '外面'],
            'zhongjian': ['中间', '中部', '中央'],
            'qidian': ['起点', '出发点', '开始点'],
            'zhongdian': ['终点', '目的地', '结束点'],
            'zhongzhuan': ['中转', '转乘', '换乘'],
            'jichang': ['机场', '航空港', '飞机场'],
            'chezhan': ['车站', '火车站', '客运站'],
            'ditiezhan': ['地铁站', '地下铁车站', '轨道交通站'],
            'gongjiao': ['公交', '公共汽车', '公交车'],
            'chuzuche': ['出租车', '的士', '计程车'],
            'danche': ['单车', '自行车', '脚踏车'],
            'qiche': ['汽车', '轿车', '机动车'],
            'huoche': ['火车', '列车', '铁路'],
            'ditie': ['地铁', '地下铁', '轨道交通'],
            'feiji': ['飞机', '航班', '航空器'],
            'chuanbo': ['船舶', '船只', '轮船'],
            'gonglu': ['公路', '道路', '马路'],
            'gaosu': ['高速', '高速公路', '快速路'],
            'qiaoliang': ['桥梁', '桥', '大桥'],
            'suidao': ['隧道', '通道', '地道'],
            'jiedao': ['街道', '大街', '马路'],
            'xiaqu': ['辖区', '区域', '地区'],
            'chengshi': ['城市', '都市', '市区'],
            'xiangcun': ['乡村', '农村', '乡下'],
            'shangdian': ['商店', '店铺', '商铺'],
            'chaoshi': ['超市', '卖场', '购物中心'],
            'shangcheng': ['商城', '商业城', '购物网站'],
            'shangjia': ['商家', '商户', '卖家'],
            'guke': ['顾客', '客户', '买家'],
            'xiaofei': ['消费', '花费', '支出'],
            'goumai': ['购买', '采购', '买入'],
            'dingdan': ['订单', '订购单', '购买单'],
            'zhifu': ['支付', '付款', '结账'],
            'jine': ['金额', '数目', '款项'],
            'zhangdan': ['账单', '清单', '明细'],
            'fapiao': ['发票', '票据', '收据'],
            'tuikuan': ['退款', '退货', '返还'],
            'peisong': ['配送', '送货', '快递'],
            'wuliu': ['物流', '货运', '运输'],
            'kuaidi': ['快递', '快件', '速递'],
            'baozhuang': ['包装', '打包', '封装'],
            'shouhou': ['售后', '售后服务', '客户服务'],
            'tousu': ['投诉', '举报', '申诉'],
            'weiquan': ['维权', '维护权益', '保护权利'],
            'pingjia': ['评价', '评分', '评级'],
            'haoping': ['好评', '赞扬', '称赞'],
            'chaping': ['差评', '批评', '负面评价'],
            'tuijian': ['推荐', '推介', '建议'],
            'remen': ['热门', '热销', '流行'],
            'xinpin': ['新品', '新产品', '新款'],
            'tejia': ['特价', '优惠价', '折扣价'],
            'manjian': ['满减', '满额减免', '促销'],
            'youhui': ['优惠', '折扣', '减价'],
            'lijian': ['立减', '立即减免', '当场优惠'],
            'fanli': ['返利', '回扣', '返现'],
            'jifen': ['积分', '点数', '奖励点'],
            'huiyuan': ['会员', 'VIP', '贵宾'],
            'dengji': ['等级', '级别', '层次'],
            'quanxian': ['权限', '权力', '授权'],
            'tequan': ['特权', '特殊权利', '优待'],
            'fuli': ['福利', '好处', '利益'],
            'jiangli': ['奖励', '奖赏', '激励'],
            'chengfa': ['惩罚', '处罚', '惩戒'],
            'guize': ['规则', '规定', '制度'],
            'tiaokuan': ['条款', '条文', '条件'],
            'xieyi': ['协议', '协定', '合约'],
            'hetong': ['合同', '契约', '合约'],
            'qiandu': ['签署', '签字', '签约'],
            'zhongzhi': ['终止', '中止', '停止'],
            'jieshu': ['结束', '完结', '终止'],
            'xuzhi': ['须知', '注意事项', '提示'],
            'shuoming': ['说明', '说明书', '解释'],
            'bangzhu': ['帮助', '协助', '支援'],
            'zaixian': ['在线', '线上', '联网'],
            'lixian': ['离线', '线下', '脱机'],
            'shishou': ['实时', '即时', '同步'],
            'tongbu': ['同步', '一致', '协调'],
            'yibu': ['异步', '不同步', '非同步'],
            'jiami': ['加密', '保密', '密码保护'],
            'jiemi': ['解密', '破译', '解码'],
            'anquan': ['安全', '保安', '防护'],
            'fengxian': ['风险', '危险', '隐患'],
            'baohu': ['保护', '防护', '保卫'],
            'beifen': ['备份', '副本', '拷贝'],
            'huifu': ['恢复', '还原', '复原'],
            'gengxin': ['更新', '升级', '刷新'],
            'banben': ['版本', '版次', '发行版'],
            'shengji': ['升级', '提升', '改善'],
            'jiangji': ['降级', '降低', '下调'],
            'chongzhi': ['重置', '复位', '恢复默认'],
            'chushihua': ['初始化', '初始设置', '初始化配置'],
            'peizhi': ['配置', '设定', '参数'],
            'canshu': ['参数', '变量', '指标'],
            'mubiao': ['目标', '目的', '宗旨'],
            'renwu': ['任务', '工作', '事项'],
            'jihua': ['计划', '规划', '安排'],
            'richeng': ['日程', '行程', '时间表'],
            'shijian': ['时间', '时刻', '时段'],
            'riqi': ['日期', '日子', '日'],
            'shijianbiao': ['时间表', '时刻表', '日程表'],
            'tixing': ['提醒', '通知', '预警'],
            'daiban': ['代办', '代理', '委托'],
            'weituoren': ['委托人', '代理人', '受托人'],
            'shouquan': ['授权', '委托', '委任'],
            'zeren': ['责任', '职责', '义务'],
            'quanli': ['权利', '权益', '权力'],
            'yiwu': ['义务', '职责', '责任'],
            'gangwei': ['岗位', '职位', '职务'],
            'zhiwei': ['职位', '岗位', '职务'],
            'bumen': ['部门', '单位', '科室'],
            'gongsi': ['公司', '企业', '机构'],
            'danwei': ['单位', '机构', '组织'],
            'zuzhi': ['组织', '团体', '机构'],
            'tuandui': ['团队', '队伍', '小组'],
            'chengyuan': ['成员', '人员', '队员'],
            'lingdao': ['领导', '上司', '主管'],
            'xiashu': ['下属', '部下', '手下'],
            'tongshi': ['同事', '同仁', '伙伴'],
            'huoban': ['伙伴', '搭档', '同伴'],
            'pengyou': ['朋友', '好友', '友人'],
            'tongxue': ['同学', '校友', '同窗'],
            'laoshi': ['老师', '教师', '导师'],
            'xuesheng': ['学生', '学员', '学子'],
            'jiazhang': ['家长', '父母', '监护人'],
            'haizi': ['孩子', '小孩', '儿童'],
            'ertong': ['儿童', '孩童', '小朋友'],
            'qingnian': ['青年', '年轻人', '小伙子'],
            'zhongnian': ['中年', '中年人', '壮年'],
            'laonian': ['老年', '老年人', '长者'],
            'nanren': ['男人', '男性', '男士'],
            'nvren': ['女人', '女性', '女士'],
            'qingkuang': ['情况', '状况', '情形'],
            'went': ['问题', '疑问', '难题'],
            'kunnan': ['困难', '难题', '障碍'],
            'jielun': ['结论', '结果', '成果'],
            'guocheng': ['过程', '流程', '步骤'],
            'fangfa': ['方法', '方式', '办法'],
            'jishu': ['技术', '技能', '技艺'],
            'jingyan': ['经验', '体会', '心得'],
            'jiaoxun': ['教训', '经验', '启示'],
            'zhishi': ['知识', '学问', '学识'],
            'xuexi': ['学习', '研习', '进修'],
            'jiaoyu': ['教育', '教导', '培育'],
            'peixun': ['培训', '训练', '培养'],
            'kaoshi': ['考试', '测验', '考核'],
            'chengji': ['成绩', '分数', '成果'],
            'pingfen': ['评分', '打分', '评价'],
            'jidian': ['绩点', '平均分', '学分绩点'],
            'xuefen': ['学分', '学时', '课程单位'],
            'kecheng': ['课程', '科目', '学科'],
            'xueke': ['学科', '科目', '专业'],
            'zhuanye': ['专业', '专门', '专长'],
            'xueyuan': ['学院', '学校', '院校'],
            'xuexiao': ['学校', '学堂', '院校'],
            'banji': ['班级', '班', '班级单位'],
            'jiaoshi': ['教室', '课堂', '教学场所'],
            'shiyanshi': ['实验室', '实验场所', '研究室'],
            'tushuguan': ['图书馆', '图书室', '阅览室'],
            'cangku': ['仓库', '库房', '储存室'],
            'bangongshi': ['办公室', '办公场所', '写字楼'],
            'huiyishi': ['会议室', '会议场所', '会场'],
            'chaozhishi': ['值班室', '值班处', '值守点']
        }
    
    def segment(self, pinyin_str: str) -> List[str]:
        """使用动态规划对拼音字符串进行分词。
        
        Args:
            pinyin_str: 用户输入的拼音字符串
            
        Returns:
            一个或多个分词后的候选词语组合
        """
        if not pinyin_str:
            return []
            
        n = len(pinyin_str)
        # dp[i] 存储前i个字符的所有可能分词结果
        # 每个元素包含(词语组合, 得分)的元组列表
        dp: List[List[Tuple[str, int]]] = [[] for _ in range(n + 1)]
        dp[0] = [("", 0)]

        for i in range(1, n + 1):
            for j in range(i):
                # 如果前j个字符无法分词，则跳过
                if not dp[j]:
                    continue
                    
                sub_pinyin = pinyin_str[j:i]
                words = self.dict_manager.lookup(sub_pinyin)
                if words:
                    for word in words:
                        for prev_segment, prev_score in dp[j]:
                            # 计算当前词语的得分，越常用的词语得分越高
                            word_score = self._get_word_score(word, sub_pinyin)
                            total_score = prev_score + word_score
                            
                            # 限制候选词数量，避免组合爆炸
                            new_segment = f"{prev_segment}{word}" if prev_segment else word
                            candidate = (new_segment, total_score)
                            
                            if len(dp[i]) < 30:  # 增加候选词数量限制
                                dp[i].append(candidate)
                            else:
                                # 保持得分最高的候选词
                                dp[i].append(candidate)
                                dp[i].sort(key=lambda x: x[1], reverse=True)
                                dp[i] = dp[i][:30]
        
        # 对结果进行排序，优先显示得分高的词语组合
        if dp[n]:
            dp[n].sort(key=lambda x: x[1], reverse=True)
            # 只返回词语，不返回得分
            return [segment for segment, score in dp[n]]
        
        return []

    def _get_word_score(self, word: str, pinyin: str) -> int:
        """获取词语的得分，用于排序。
        
        Args:
            word: 词语
            pinyin: 对应的拼音
            
        Returns:
            词语得分，越高表示越常用
        """
        # 基础得分基于词频（如果词库中有词频信息）
        base_score = self.dict_manager.get_word_frequency(word, pinyin)
        
        # 如果是常用短语，给予额外加分
        if pinyin in self.common_phrases and word in self.common_phrases[pinyin]:
            # 根据在列表中的位置确定得分，越靠前得分越高
            position = self.common_phrases[pinyin].index(word)
            base_score += 10000 - position * 1000
            
        return base_score

    def get_candidates(self, pinyin_str: str) -> List[str]:
        """根据拼音字符串获取候选词列表。
        
        查询顺序:
        1. 首先检查是否是常用短语
        2. 然后使用分词算法获取整词候选
        3. 然后在自定义词典中查找完全匹配的词语
        4. 使用pypinyin库获取单字候选
        5. 添加一些硬编码的常用词作为补充
        
        Args:
            pinyin_str: 用户输入的拼音字符串
            
        Returns:
            候选汉字或词语的列表
        """
        if not pinyin_str:
            return []
        
        candidates = []

        # 1. 检查是否是常用短语
        if pinyin_str in self.common_phrases:
            candidates.extend(self.common_phrases[pinyin_str])
        
        # 2. 使用分词算法获取候选
        segmented_candidates = self.segment(pinyin_str)
        candidates.extend(segmented_candidates)
        
        # 3. 检查自定义词典
        dict_candidates = self.dict_manager.get_candidates(pinyin_str, -1)  # 获取所有候选词
        candidates.extend(dict_candidates)
        
        # 4. 使用pypinyin获取单字候选
        try:
            # 获取每个字符的拼音
            result = pinyin(pinyin_str, style=Style.NORMAL, heteronym=True)
            if result:
                # 处理所有可能的读音
                for char_pinyins in result:
                    for char_pinyin in char_pinyins:
                        # 注意：这里原来的逻辑有问题，应该查找汉字而不是拼音
                        # 通过拼音查找对应的汉字
                        hanzi_list = self.dict_manager.lookup(char_pinyin)
                        if hanzi_list:
                            for hanzi in hanzi_list:
                                if hanzi not in candidates:
                                    candidates.append(hanzi)
        except Exception as e:
            print(f"Pypinyin error: {e}")
        
        # 5. 添加硬编码的常用候选词
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
        
        # 去重并保持顺序
        seen = set()
        unique_candidates = []
        for candidate in candidates:
            if candidate not in seen:
                seen.add(candidate)
                unique_candidates.append(candidate)
        
        return unique_candidates  # 返回所有候选词，不限制数量


if __name__ == '__main__':
    # 测试拼音引擎
    engine = PinyinEngine()
    
    test_cases = ['ni', 'hao', 'nihao', 'wo', 'de', 'shi', 'zhongguo', 'nihaoma']
    for test in test_cases:
        candidates = engine.get_candidates(test)
        print(f"'{test}': {candidates}")