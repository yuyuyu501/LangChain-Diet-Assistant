def process_feedback(feedback_list):
    feedback_categories = {
        '效果显著': 0,
        '部分改善': 0,
        '效果一般': 0,
        '无明显效果': 0
    }

    # 定义关键词映射
    keywords = {
        '效果显著': [
            # 中文正面评价
            '效果显著', '很好', '非常好', '特别好', '极好', '明显改善', '显著改善', 
            '效果很好', '效果非常好', '很有效', '非常有效', '特别有效', '立竿见影',
            '完全康复', '彻底改善', '非常满意', '很满意', '效果明显', '改善显著',
            '恢复很好', '效果突出', '非常有帮助', '帮助很大', '非常棒', '太棒了',
            '效果卓越', '效果惊人', '效果神奇', '效果出众', '效果完美', '完全好转',
            '彻底解决', '非常理想', '特别满意', '相当满意', '十分满意', '百分百满意',
            '效果绝佳', '非常舒服', '很舒服', '特别舒服', '完全恢复', '痊愈了',
            # 情感表达
            '很喜欢', '非常喜欢', '特别喜欢', '超喜欢', '真的很喜欢', '好喜欢',
            '很爱', '特别爱', '超爱', '真的很爱', '太爱了', '很推荐', '强烈推荐',
            '大力推荐', '极力推荐', '特别推荐', '真心推荐', '必须推荐', '值得推荐',
            '超级棒', '真的棒', '特别棒', '很赞', '非常赞', '超赞', '真赞',
            '很开心', '非常开心', '特别开心', '超开心', '很满意', '特别满意',
            '超级满意', '很感谢', '非常感谢', '特别感谢', '太感谢了', '很感激',
            '真的很好', '确实很好', '真心不错', '真的不错', '确实不错', '真好',
            # 数字评分
            '100分', '五星', '满分', '5分', '五颗星', '五分', '10分', '十分',
            # 网络用语
            '666', 'yyds', '太强了', '无敌了', '绝了', '牛逼', 'nb', '太牛了',
            '太厉害了', '神了', '太神了', '吊炸天', '太赞了', '给力', '太给力了',
            # 身体感受
            '舒服多了', '精神多了', '轻松多了', '有劲多了', '好多了', '强多了',
            '清爽多了', '神清气爽', '浑身舒畅', '精力充沛', '活力满满',
            # 时间相关
            '立刻见效', '马上就好', '很快就好', '立即生效', '速效', '见效快',
            '效果立竿见影', '立马见效', '立即见效', '立刻起效',
            # 程度词
            '超级', '特别', '极其', '十分', '无比', '极度', '极为', '格外',
            '分外', '尤其', '尤为', '异常', '特殊', '特异', '非同寻常',
            # 英文正面评价
            'excellent', 'perfect', 'great', 'amazing', 'wonderful', 'fantastic',
            'very good', 'very effective', 'highly effective', 'super', 'brilliant',
            'outstanding', 'remarkable', 'exceptional', 'superb', 'awesome',
            'terrific', 'fabulous', 'magnificent', 'marvelous', 'impressive',
            'incredible', 'best', 'perfect', 'completely cured', 'fully recovered',
            'very satisfied', 'highly satisfied', 'extremely satisfied',
            # 英文情感表达
            'love it', 'really love', 'really like', 'like it very much',
            'highly recommend', 'strongly recommend', 'definitely recommend',
            'would recommend', 'must recommend', 'worth recommending',
            'very happy', 'really happy', 'super happy', 'very pleased',
            'really pleased', 'delighted', 'grateful', 'thankful',
            'appreciate', 'really appreciate', 'very grateful', 'very thankful',
            'satisfied', 'very satisfied', 'really satisfied', 'totally satisfied',
            'completely satisfied', 'absolutely satisfied', 'perfectly satisfied',
            # 英文网络用语
            'omg', 'wow', 'lit', 'goat', 'fire', 'dope', 'sick', 'epic',
            'legendary', 'insane', 'crazy good', 'mind-blowing', 'game-changing'
        ],
        
        '部分改善': [
            # 中文部分改善
            '部分改善', '有所改善', '略有改善', '稍有改善', '有点改善', '有些改善',
            '好一些', '好一点', '有好转', '略有好转', '稍有好转', '有点好转',
            '改善一些', '有一定效果', '效果一般般', '还可以', '尚可', '有帮助',
            '有点用', '有点效果', '略有成效', '有所帮助', '有所好转', '有所成效',
            '稍微改善', '略微改善', '些许改善', '小有改善', '渐渐好转', '慢慢好转',
            '逐渐改善', '逐步改善', '初见成效', '开始改善', '有改进', '有进步',
            '略有起色', '稍有起色', '略有进展', '有些进展', '略有效果', '有些效果',
            # 情感表达
            '还喜欢', '有点喜欢', '还不错', '还行', '可以接受', '还算喜欢',
            '还算可以', '还算好', '还算不错', '有点满意', '基本满意', '比较满意',
            '还算满意', '有点满意', '稍微满意', '一般满意', '可以推荐',
            # 时间相关
            '慢慢变好', '逐渐改善', '正在恢复', '在改善', '在好转', '在进步',
            '在康复', '在恢复', '在改进', '慢慢来', '循序渐进',
            # 程度词
            '有一些', '略微', '稍稍', '渐渐', '慢慢', '逐步', '逐渐', '缓缓',
            # 保守表达
            '感觉还行', '应该可以', '似乎有效', '可能有效', '或许可以',
            '觉得还行', '感觉不错', '似乎不错', '应该不错', '大概可以',
            # 英文部分改善
            'somewhat better', 'slightly better', 'a bit better', 'getting better',
            'improving', 'slight improvement', 'some improvement', 'partially improved',
            'moderately effective', 'somewhat effective', 'fairly good', 'quite good',
            'relatively good', 'not bad', 'acceptable', 'decent', 'making progress',
            'gradually improving', 'slowly improving', 'showing improvement',
            # 英文情感表达
            'kind of like', 'somewhat like', 'quite like', 'fairly like',
            'moderately satisfied', 'somewhat satisfied', 'quite satisfied',
            'can recommend', 'might recommend', 'okay to recommend',
            # 英文口语
            'getting there', 'not too bad', 'kinda good', 'pretty okay',
            'fairly decent', 'reasonably good', 'sort of working'
        ],
        
        '效果一般': [
            # 中文一般评价
            '效果一般', '一般般', '普通', '不太明显', '不太好', '一般效果',
            '效果平平', '效果不明显', '效果不太好', '一般般吧', '马马虎虎',
            '不温不火', '不好不坏', '中等效果', '效果中等', '有限效果',
            '效果有限', '不太理想', '不太满意', '一般满意', '勉强可以',
            '凑合', '将就', '一般性', '中规中矩', '平平常常', '普普通通',
            '不上不下', '不咸不淡', '差强人意', '凑合着用', '可以接受',
            '基本可以', '还过得去', '还说得过去', '不算太差', '不算很好',
            # 情感表达
            '不太喜欢', '一般喜欢', '说不上喜欢', '谈不上喜欢', '不太满意',
            '一般满意', '说不上满意', '谈不上满意', '不太推荐', '一般推荐',
            '不好说', '说不准', '不确定', '不太确定', '不太清楚',
            # 模棱两可
            '说不好', '不太确定', '有待观察', '不好说', '说不准', '不一定',
            '不好判断', '难说', '不太了解', '不太懂', '不太清楚',
            # 观望态度
            '再看看', '观察中', '待定', '继续观察', '拭目以待', '再等等',
            '看情况', '随缘', '再说', '以后再说', '暂时不好说',
            # 中性词
            '一般般啦', '还过得去吧', '凑合用吧', '将就用吧', '勉强用吧',
            '凑活着用', '过得去', '可以用', '能用', '将就着用',
            # 英文一般评价
            'average', 'ordinary', 'normal', 'moderate', 'mediocre', 'fair',
            'so so', 'neither good nor bad', 'not very effective', 'ok',
            'okay', 'alright', 'passable', 'tolerable', 'medium', 'standard',
            'regular', 'common', 'usual', 'neutral', 'intermediate',
            # 英文情感表达
            'not sure if like', 'not sure about', 'cannot say', 'hard to say',
            'not particularly satisfied', 'not really satisfied',
            'would not really recommend', 'not sure if recommend',
            # 英文口语
            'meh', 'just ok', 'could be better', 'nothing special',
            'nothing extraordinary', 'nothing remarkable', 'whatever'
        ],
        
        '无明显效果': [
            # 中文负面评价
            '无明显效果', '没效果', '无效果', '效果不大', '没什么效果', '没有效果',
            '完全没效果', '根本没用', '毫无效果', '没有任何效果', '效果不理想',
            '效果很差', '没有改善', '没有好转', '毫无改善', '毫无好转',
            '完全无效', '不起作用', '没有帮助', '没什么用', '没有用',
            '效果差', '不满意', '很不满意', '完全不满意', '毫无用处',
            '完全没用', '一点用都没有', '一点效果都没有', '没有一点效果',
            '完全无用', '纯属浪费', '白费功夫', '徒劳无功', '没有任何改善',
            '没有任何好转', '完全没有改善', '完全没有好转', '效果为零',
            # 情感表达
            '不喜欢', '很不喜欢', '特别不喜欢', '完全不喜欢', '根本不喜欢',
            '讨厌', '很讨厌', '特别讨厌', '非常讨厌', '完全不满意',
            '特别不满意', '非常不满意', '极不满意', '不推荐', '不建议',
            '不值得推荐', '不值得尝试', '不建议使用', '不建议购买',
            '后悔', '很后悔', '特别后悔', '非常后悔', '太后悔了',
            # 强烈否定
            '垃圾', '废物', '不行', '差劲', '太差了', '差爆了',
            '烂透了', '太烂了', '糟糕', '太糟了', '糟透了', '太糟糕了',
            # 失望表达
            '太失望', '不敢相信', '难以置信', '大失所望', '令人失望',
            '让人失望', '太让人失望', '令人心寒', '让人心凉', '寒心',
            # 否定程度
            '完全不行', '根本不好', '压根没用', '根本不行', '完全不好',
            '根本不管用', '完全没效果', '彻底没用', '统统无效', '全然无效',
            # 英文负面评价
            'no effect', 'not effective', 'ineffective', 'useless', 'worthless',
            'no improvement', 'no change', 'not working', 'doesn\'t work',
            'not helpful', 'poor', 'terrible', 'awful', 'bad', 'unsatisfactory',
            'disappointing', 'waste of time', 'zero effect', 'no use',
            'not satisfied', 'dissatisfied', 'totally ineffective', 'completely useless',
            'absolutely no effect', 'no result', 'failed', 'not good at all',
            # 英文情感表达
            'don\'t like', 'really don\'t like', 'hate', 'really hate',
            'would not recommend', 'cannot recommend', 'do not recommend',
            'wouldn\'t recommend', 'not worth', 'regret', 'really regret',
            'totally regret', 'completely regret', 'waste of money',
            'waste of time', 'not worth trying', 'not worth buying',
            # 英文口语否定
            'garbage', 'trash', 'waste', 'junk', 'crap', 'rubbish',
            'horrible', 'pathetic', 'lousy', 'worthless', 'useless'
        ]
    }

    for feedback in feedback_list:
        if not feedback:  # 处理空值情况
            continue
            
        feedback = str(feedback).lower()  # 转换为小写以进行不区分大小写的匹配
        matched = False
        
        # 按优先级顺序检查各个类别的关键词
        for category, keyword_list in keywords.items():
            for keyword in keyword_list:
                if keyword.lower() in feedback:  # 确保关键词也转换为小写
                    feedback_categories[category] += 1
                    matched = True
                    break
            if matched:
                break
        
        # 如果没有匹配任何关键词，归类为效果显著
        if not matched:
            feedback_categories['效果显著'] += 1

    return feedback_categories 