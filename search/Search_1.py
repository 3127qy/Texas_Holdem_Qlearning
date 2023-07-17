import itertools
import re


# 采用Bill Chen 的翻牌前阶段估值
def preflop(handCards):

    # 每张牌的估分
    ranks= [0.0,0.0]

    #总分值
    result = 0.0

    # 牌的值
    cs_array = []
    # 牌值对应的花色
    cc_array = []

    for i in handCards:

        # 分割字符，pre、mid、last分别确定"<"," ," ,">"下标
        pre = i.index("<")
        mid = i.index(",")
        last = i.index(">")
        cs_array.append(eval(i[(mid + 1):last]))
        cc_array.append(eval(i[(pre + 1) :mid]))

    for i in range(0,2):
        # 12 对应 A
        if cs_array[i] == 12:
            ranks[i] = 10

        #11 对应 K
        elif cs_array[i] == 11:
            ranks[i] = 8

        # 10 对应 Q
        elif cs_array[i] == 10:
            ranks[i] = 7

        #9 对应 J
        elif cs_array[i] == 9:
            ranks[i] = 6

        else:
            ranks[i] = (cs_array[i] + 2) / 2


    result = ranks[0] if ranks[0] >= ranks[1] else ranks[1]


    if cs_array[0] == cs_array[1]:
        result = result * 2

        if result < 5:
            result = 5

    if cc_array[0] == cc_array[1]:
        result = result + 2


    tempAbs = abs(cs_array[0] - cs_array[1])

    if tempAbs == 2:
        result = result - 1

    elif tempAbs == 3:
        result = result - 2

    elif tempAbs == 4:
        result = result - 4

    elif tempAbs >= 5:
        result = result - 5

    if cs_array[0] < 10 and cs_array[1] < 10:
        if tempAbs == 0 or tempAbs == 1:
            result = result + 1

#     最高分对A 分值为20

    # return  result / 20

    return  int(result)



def isThree(boardCards):

    for tempCards in itertools.combinations(boardCards,3):
        tempCard =[]
        for i in tempCards:
            tempCard.append(re.split("[,>]",i)[1])

        if tempCard[0] == tempCard[1] and tempCard[0] == tempCard[2]:
            return "三条"


    return None


def isTwoPairs(boardCards):

    if (len(boardCards)) > 3:

        for tempCards in itertools.combinations(boardCards, 4):

            tempCard = []
            for i in tempCards:
                tempCard.append(re.split("[,>]", i)[1])

            if tempCard[0] == tempCard[1] and tempCard[2] == tempCard[3]:
                return "两对"

            if tempCard[0] == tempCard[2] and tempCard[1] == tempCard[3]:
                return "两对"

            if tempCard[0] == tempCard[3] and tempCard[1] == tempCard[2]:
                return "两对"

    return None


def isOnePair(boardCards):

    for tempCards in itertools.combinations(boardCards, 2):

        tempCard = []

        for i in tempCards:
            tempCard.append(re.split("[,>]", i)[1])

        if tempCard[0] == tempCard[1]:
            return "一对"

    return None



def getBoardCardType(boardCards):

    type = isThree(boardCards)

    if type is None:
        type = isTwoPairs(boardCards)

    if type is None:
        type = isOnePair(boardCards)


    if type is None:
        return "高牌"
    else:
        return type