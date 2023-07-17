import collections
import sys
import re
import itertools



'''
返回根据所传入的牌能组合出的最大牌型对应的值
以及其牌型
'''
def rank(handCards, boardCards):
    # print('handCards'+handCards)
    # print('boardCards' + boardCards)

    # 组合出的最大值
    maxResult = 0

    # 手牌类别数组下标对应值
    resultValue = -1

    # 牌型，为什么这么排，阅读calculateRank函数
    handsType = ['四条', '同花顺', '顺子', '同花', '高牌', '一对', '两对', '皇家同花顺', '三条', '葫芦']

    # 对公共牌进行组合
    # 手牌可以和公共牌组成 1，4 ； 2，3 一共凑成5张牌

    if len(boardCards) == 3:
        maxResult, resultValue = calculateRank(handCards, boardCards,maxResult,resultValue)


    elif len(boardCards) != 3:
        allHandCardsCombination = [handCards[0], handCards[1], [handCards[0], handCards[1]]]

        for tempHandCards in allHandCardsCombination:
            # 2张手牌,3张公共牌 凑成 5 张牌
            if len(tempHandCards) == 2:
                for tempBoardCards in itertools.combinations(boardCards, 3):
                    maxResult, resultValue  = calculateRank(tempHandCards, tempBoardCards,maxResult,resultValue)

            # 1张手牌,4张公共牌 凑成 5 张牌
            else:
                for tempBoardCards in itertools.combinations(boardCards, 4):
                    # [tempHandCards] 是 一张牌读出来的是字符串，把字符串变为一个数组
                    maxResult, resultValue = calculateRank([tempHandCards], tempBoardCards,maxResult,resultValue)

    return maxResult, handsType[resultValue]

# 根据不同的组合获取具体的值
def calculateRank(handCards, boardCards,maxResult,resultValue):

    # 牌的值
    cs_array = []
    # 牌值对应的花色
    cc_array = []

    for i in handCards:
        # string = re.split('[<,>]',i)
        # print(string)
        # 分割字符，pre、mid、last分别确定"<"," ," ,">"下标
        pre = i.index("<")
        mid = i.index(",")
        last = i.index(">")
        cs_array.append(eval(i[(mid + 1):last]))
        cc_array.append(eval(i[(pre + 1):mid]))

    for i in boardCards:
        # 分割字符，pre、mid、last分别确定"<"," ," ,">"下标
        pre = i.index("<")
        mid = i.index(",")
        last = i.index(">")
        cs_array.append(eval(i[(mid + 1):last]))
        cc_array.append(eval(i[(pre + 1):mid]))

    #     修改cc_array数组:红桃： 0x0001,黑桃：0x0002，方块0x0004,梅花：0x0008
    for i in range(0, len(cc_array)):
        cc_array[i] = 1 << (cc_array[i])

    # print(cc_array)

    #     flag:整型,表示忽略花色，忽略重复牌后的情况
    flag = 1 << cs_array[0] | 1 << cs_array[1] | 1 << cs_array[2] | 1 << cs_array[3] | 1 << cs_array[4]

    # print(flag)

    value = 0

    for i in range(0, 5):
        offset = 1 << cs_array[i] * 4
        value += offset * ((value // offset & 0x000f) + 1)

    # value 取得标志位 （A,2,3,4,5）的标志位为0x100f,但该比赛平台没有把（A,2,3,4,5）视为顺子
    # value = value % 0x000f - (3 if (((flag // (flag & -flag)) == 0x001f) or (flag == 0x100f)) else 1)
    value = value % 0x000f - (3 if (((flag // (flag & -flag)) == 0x001f)) else 1)

    # 处理之后根据value的值可以得到列表对应值
    # 下标：  0，  1，  2，   3，  4，   5，   6，  7，  8，   9
    # 值：  四条  无   顺子  无   高牌  一对  两对  无   三条  葫芦（三带二）

    # 判断是否为同花
    if (cc_array[0] & cc_array[1] & cc_array[2] & cc_array[3] & cc_array[4] & 0xffff != 0):

        # 如果是顺子，判断同花顺
        if (value == 2):
            # 皇家同花顺的标志位为0x7c00
            if (flag == 0x1f00):
                value += 5
            else:
                value -= 1

        # 将当前牌值小于同花的都变为同花，主要是把高牌变为同花，三条、两对、一对 是多余的 我没有去除掉
        if (value == 8 or value == 6 or value == 5 or value == 4):
            # 同花下标为3
            value = 3

    # 处理之后根据value的值可以得到列表对应值
    # 下标：  0，     1，    2，   3，  4，   5，   6，       7，      8，   9
    # 值：  四条  同花顺   顺子  同花   高牌  一对  两对  皇家同花顺   三条  葫芦（三带二）

    # 定义手牌类别
    handsType = ['四条', '同花顺', '顺子', '同花', '高牌', '一对', '两对', '皇家同花顺', '三条', '葫芦']

    # print("手牌类别：" +  handsType[value])

    # 将手牌的转化为确切的值
    # hs是与cardType相对应的值
    hs = [8, 9, 5, 6, 1, 2, 3, 10, 4, 7]

    # 按照出现次数排序，返回一个Counter
    cs_array = sorted(cs_array, reverse=True)
    cs_count_array = collections.Counter(cs_array)
    # 转化为列表
    cs_count_array = cs_count_array.most_common(5)
    # print(cs_count_array)

    result = 0

    # 如果是顺子a,2,3,4,5（标志位0x100f），需要特殊处理
    # if (flag == 0x100f):
    #     # (12,1)在第一位，忽略掉（12，1）
    #     for i in range(1, len(cs_count_array)):
    #         result = result | cs_count_array[i][0] << (4 * (4 - i))
    # else:
    #     for i in range(0, len(cs_count_array)):
    #         result = result | cs_count_array[i][0] << (4 * (4 - i))

    for i in range(0, len(cs_count_array)):
        result = result | cs_count_array[i][0] << (4 * (4 - i))

    # 加入组合牌型的影响
    result = hs[value] << 52 | result

    # print("手牌对应值：" + str(result))

    if result > maxResult:
        maxResult = result
        resultValue = value


    return  maxResult,resultValue


