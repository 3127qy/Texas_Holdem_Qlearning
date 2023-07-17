import winsound

import  re

import  random
import time
from search import Rank, Search_1
import itertools
import logging
import traceback


# 最大回合数
from search import Rank

maxBout = 70

#todo 当前局数
currentBout=0

#todo opactions
opactionsInpreflop={"raise":0,"callOrCheck":0,"3bet":0}


# 每个新阶段判断是不是自己开始的标志
myStartTurn = False


# 当前阶段
phase = ""

# 位置
position = ""

# 手牌
handCards = []

# 公共牌
boardCards = []

# 每一阶段轮到自己走步的次数
myCount = 0

# 当前局数自己剩余筹码量
myRestChips = 20000

# 暂存上一阶段后自己所剩的筹码量
lastPhaseMyRestChips = 20000

# 自己上次行为所下注大小
myLastPutChips = 0

# 底池总金额
chipsPool = 0

# 需要赢的下限
winLowLimit = 101


# 对手非翻牌前阶段加注次数
opRaiseCount = 0

# 对手非翻牌前阶段看牌次数
opCheckCount = 0

# 下注的最低预警线
betline = 110

#对手类型
IsBigBet=False

# 52张牌
allCards = ['<0,0>','<0,1>','<0,2>','<0,3>','<0,4>','<0,5>','<0,6>','<0,7>','<0,8>','<0,9>','<0,10>','<0,11>','<0,12>',
            '<1,0>','<1,1>','<1,2>','<1,3>','<1,4>','<1,5>','<1,6>','<1,7>','<1,8>','<1,9>','<1,10>','<1,11>','<1,12>',
            '<2,0>','<2,1>','<2,2>','<2,3>','<2,4>','<2,5>','<2,6>','<2,7>','<2,8>','<2,9>','<2,10>','<2,11>','<2,12>',
            '<3,0>','<3,1>','<3,2>','<3,3>','<3,4>','<3,5>','<3,6>','<3,7>','<3,8>','<3,9>','<3,10>','<3,11>','<3,12>',]


"""
sk：socket通信接口
alreadyWinChips:已经赢取的筹码量
currentBout：当前是第几局
"""
def basic(sk,alreadyWinChips,currentBout):


        # 初始化函数
        clear()

        global myStartTurn,lastPhaseMyRestChips,opRaiseCount,opCheckCount,message,IsBigBet

        # 暂存上一阶段
        lastPhase = "None"

        # 无限循环接受消息
        while True:
            # time.sleep(1)
            try:
                message = sk.recv(1024).decode("utf-8")
                print("message: " + str(message))

                # time.sleep(3)
                #判断对手的下大注行为
                # if int(opactionsInpreflop.get("raise"))/int(opactionsInpreflop.get("callOrCheck"))>(23/46) or opactionsInpreflop.get("3bet")>3):
                #     IsBigBet=True

                #先判断该局是否结束
                winSign,winChips = checkFinish(message)
                if winSign:
                    return winChips,winLowLimit

                # 获取位置信息
                getPosition(message)

                # 获取阶段信息,成功获取阶段信息后将手牌或者公共牌存入相应变量
                getPhase(message)

                if not myStartTurn:
                    myStartTurn = True
                    continue

                time.sleep(1)

                # 获取对手行为
                opAction = getOpAction(message)
                print("opAction: " + str(opAction))

                # 记录对方加注次数
                if phase != "preflop" and opAction[0] == "raise":
                    opRaiseCount += 1
                    print("opRaiseCount : " + str(opRaiseCount))

                # 记录对方看牌次数
                if phase != "preflop" and opAction[0] == "check":
                    opCheckCount += 1
                    print("opCheckCount : " + str(opCheckCount))

                # 如果最终局面已经赢了，直接弃牌
                # judgeAlreadyWin(alreadyWinChips, currentBout)
                if judgeAlreadyWin(alreadyWinChips, currentBout):
                    # winsound.Beep(600, 1000)
                    print("Already Win!!!!")
                    # time.sleep(5)
                    sk.send("fold".encode())



                # 不是已经赢了就正常操作
                else:

                    # 如果对手行为不是“fold”，我需要做决策
                    if opAction[0] != "fold":

                        # time.sleep(1)

                        print("myCount: " + str(myCount))


                        if lastPhase != phase and phase != "preflop":
                            lastPhase = phase
                            lastPhaseMyRestChips = myRestChips
                        # print("myRestChips : " + str(myRestChips))

                        # 采取行动
                        if phase == "preflop":
                            doPreflop(sk,opAction,alreadyWinChips,currentBout)
                        elif phase == "turn" or phase == "flop":
                            doFlopAndTurn(sk,opAction,alreadyWinChips,currentBout)
                        elif phase == "river":
                            doRiver(sk,opAction,alreadyWinChips,currentBout)

                        # print("myRestChips : " + str(myRestChips))

                        # 分界线
                        print("---")

            except Exception as e:

                # time.sleep(5)
                logging.exception(e)

                continue






#本回合结束后重置所有的全局变量进行下一次对局
def clear():
    global myStartTurn, phase, position, handCards, boardCards, myCount, myRestChips,myLastPutChips,chipsPool,lastPhaseMyRestChips,opRaiseCount,opCheckCount

    # IsBigBet=False
    myStartTurn = False
    phase = ""
    position = ""
    handCards = []
    boardCards = []
    myCount = 0
    myRestChips = 20000
    myLastPutChips = 0
    chipsPool = 150
    lastPhaseMyRestChips = 20000
    opRaiseCount = 0
    opCheckCount = 0

#判断本轮是否结束
def checkFinish(message):

    elements = re.split("[ ]",message)

    if elements[0] == "earnChips" and "oppo_hands" not in elements[1] and "preflop" not in elements[1]:
        winChips = eval(elements[1])
        return True,winChips
    elif elements[0] == "earnChips":
        winChips = 0
        if "oppo_hands" in elements[1]:
            winChips = eval(elements[1][:elements[1].index("oppo_hands")])
        elif "preflop" in elements[1]:
            winChips = eval(elements[1][:elements[1].index("preflop")])

        return True,winChips
    else:

        return False,0


# 返回能赢的最小筹码
def getWinMinChips(currentBout):
    return (maxBout - currentBout) * 75

#判断是否已经赢了
def judgeAlreadyWin(alreadyWinChips,currentBout):

    # 判断自己是否已经输了
    if alreadyWinChips + (maxBout - currentBout) * 75 < 0: # todo 这个线时对手可以一直弃牌我也不可能达到更多的筹码量。
        print("Already lose!!!!")

    # maxBout局后保证自己所赢筹码量大于指定数量
    if alreadyWinChips - (getWinMinChips(currentBout)) >= winLowLimit:
        return True
    else:
        return False


# 返回一个下注的界限
def betLine(alreadyWinChips,currentBout,percentage):


    if alreadyWinChips < 0 and (((getWinMinChips(currentBout) + alreadyWinChips) * percentage)) >= 0 :
        line = (((getWinMinChips(currentBout) + alreadyWinChips) * percentage)) if (((getWinMinChips(currentBout) + alreadyWinChips) * percentage)) > betline else betline

        opAction = getOpAction(message)
        if opAction[0] == "raise":
            if opAction[1] >= line:
                print("opRaise : " + str(opAction[1]) + " Line : " + str(line))

        print("Line :         " + str(line))

        return line

    elif alreadyWinChips >= 0 and (((getWinMinChips(currentBout)) * percentage)) >= 0:
        line = (((getWinMinChips(currentBout)) * percentage)) if (((getWinMinChips(currentBout)) * percentage)) > betline else betline

        opAction = getOpAction(message)
        if opAction[0] == "raise":
            if opAction[1] >= line:
                print("opRaise : " + str(opAction[1]) + " Line : " + str(line))

        print("Line :         " + str(line))
        return line

    else:

        print("Line :         " + str(maxBout * 75))

        return maxBout * 75

# 获取阶段
def getPhase(message):

    global phase,myCount,myStartTurn,handCards,boardCards,myRestChips


    if "oppo_hands" in message and "preflop" in message:
        index = message.index("preflop")
        message = message[index:]

    elements = re.split("[|]",message)

    if ( elements[0] != "oppo_hands" and len(elements) == 2 or len(elements) == 3 and "|" in message ):
        phase = elements[0]
        # print(message)
        print("phase: " + str(phase))

#       进入新阶段，判断是否是自己起手
        if phase == "preflop":
            if position == "BIGBLIND":
                myStartTurn = False
                myRestChips -= 100
            else:
                myStartTurn = True
                myRestChips -= 50

            # print("enterNewContest myRestChips:" + str(myRestChips))
        else:
            if position == "BIGBLIND":
                myStartTurn = True
            else:
                myStartTurn = False

#         进入新阶段，将myCount置为0
        myCount = 0



#     成功获取阶段信息后将手牌或者公共牌存入变量
        if phase == "preflop":

            getHandCards(elements[2])
        elif phase != "oppo_hands":

            getBoardCards(elements[1])

#获取位置大盲/小盲
def getPosition(message):

    global  position

    if "oppo_hands" in message and "preflop" in message:
        index = message.index("preflop")
        message = message[index:]

    elements = re.split("[|]",message)

    if (len(elements) == 3):
        position = elements[1]

def getOpAction(message):

    opAction = []
    elements = re.split("[ ]",message)

    if elements[0] == "call" or elements[0] == "fold" or elements[0] == "check" or elements[0] == "allin":
        opAction.append(elements[0])
        return opAction

    # raise 操作平台会返回信息 raise 筹码 用 opAction[0]存储动作, 用 opAction[1] 存储筹码
    elif elements[0] == "raise":
        opAction.append(elements[0])
        opAction.append(eval(elements[1]))
        return opAction
    else:
        return ["None"]

#手牌
def getHandCards(cardStr):

    global handCards

    tempCards = re.split("[<,>]",cardStr)
    # print('tempCards'+tempCards)
    # 将字符数组中 所有 '' 字符移除
    for i in range(0,len(tempCards)):
        if '' in tempCards:
            tempCards.remove('')

    for i in range(0, len(tempCards),2):
        str = "<" + tempCards[i] + "," + tempCards[i + 1] + ">"
        handCards.append(str)

#牌桌牌
def getBoardCards(cardStr):

    global boardCards

    tempCards = re.split("[<,>]", cardStr)

    # 将字符数组中 所有 '' 字符移除
    for i in range(0, len(tempCards)):
        if '' in tempCards:
            tempCards.remove('')

    for i in range(0, len(tempCards), 2):
        str = "<" + tempCards[i] + "," + tempCards[i + 1] + ">"
        boardCards.append(str)


# 生成手牌函数
def creatHandCard():

    tempOpHandCards = []

    # 获取所有还未出现的牌
    tempAllCards = getTempAllCards()


    # 再随机生成第一张对手手牌
    firstOpHandCard = tempAllCards[random.randint(0, len(tempAllCards) -1)]

    tempAllCards.remove(firstOpHandCard)

    # 再随机生成第二张对手手牌
    secondOpHandCard = tempAllCards[random.randint(0, len(tempAllCards) - 1)]

    tempOpHandCards.append(firstOpHandCard)
    tempOpHandCards.append(secondOpHandCard)


    return tempOpHandCards

# 获取所有还未出现的牌
def getTempAllCards(opCards = None):

    # 先将先讲所有牌存入零时变量
    tempAllCards = allCards[0:]

    # for i in allCards:
    #     tempAllCards.append(i)

    # 再在所有牌中删去已知的牌
    for i in handCards:
        if i in tempAllCards:
            tempAllCards.remove(i)

    for i in boardCards:
        if i in tempAllCards:
            tempAllCards.remove(i)

    if opCards is not None:
        for i in opCards:
            if i in tempAllCards:
                tempAllCards.remove(i)


    return tempAllCards

# 手牌强度
def handStrength(handCards,boardCards):

    ahead = tied = behind = 0


    # 自己手牌的值
    maxMyRank,handType = Rank.rank(handCards, boardCards)

    print("handCards: " + str(handCards))
    print("boardCards: " + str(boardCards))
    print("handType: " + str(handType))

    boardType = Search_1.getBoardCardType(boardCards)
    print("boardType : " + str(boardType))

    # 获取所有还未出现的牌
    tempAllCards = getTempAllCards()

    for tempOpHandCards in itertools.combinations(tempAllCards,2):
        # print("currentCount:" + str(i))

        # 模拟对手手牌
        # tempOpHandCards = creatHandCard()

        # 存储对方手牌最大的值
        maxOpRank,maxOpType = Rank.rank(tempOpHandCards, boardCards)

        # 如果对方加注了，其牌型应该不小，所以直接忽略掉小的牌型
        if opRaiseCount >= 1 and boardType == maxOpType:
            if random.random() <= 0.6:
                continue


        if maxMyRank > maxOpRank:
            ahead += 1

        elif maxMyRank == maxOpRank:
            tied += 1

        elif maxMyRank < maxOpRank:
            behind += 1

    # 未加入潜力值的手牌强度  todo 这里的强度是相对整个牌局能有的强度，与preflop的直接打分强度不同
    HS = (ahead + tied / 2) / (ahead + tied + behind)



    # 对自己未来可能出现的牌型做预测

    # # 预测手牌强度
    # PHS = 0
    #
    # # 对自己未来手牌预测的牌型字典
    # handsType = {"高牌": 0, "一对": 0, "两对": 0, "三条": 0, "顺子": 0, "同花": 0, "葫芦": 0, "四条": 0, "同花顺": 0, "皇家同花顺": 0}
    #
    # # 每个阶段可模拟的总次数
    # count = 0
    #
    # if phase == 'flop':
    #
    #     # # c(47,2) = 1081
    #     # count = 1081
    #
    #     for tempCards in itertools.combinations(tempAllCards,2):
    #         count += 1
    #
    #         # 模拟的公共牌
    #         tempBoardCards = boardCards[0:]
    #
    #         for i in tempCards:
    #             tempBoardCards.append(i)
    #
    #         rank,handType = Rank.rank(handCards,tempBoardCards)
    #
    #         handsType[handType] += 1
    #
    #
    # elif phase == 'turn':
    #
    #     # # c(46,1) = 46
    #     # count = 46
    #
    #     for tempCards in tempAllCards:
    #         count += 1
    #
    #         # 模拟的公共牌
    #         tempBoardCards = boardCards[0:]
    #
    #
    #         tempBoardCards.append(tempCards)
    #
    #         rank,handType = Rank.rank(handCards,tempBoardCards)
    #
    #         handsType[handType] += 1
    #
    # if phase != "river":
    #     for type in handsType.keys():
    #
    #         # 跳过预测牌型为高牌的牌型
    #         if type == "高牌":
    #             continue
    #
    #
    #         # 记录小于该牌型的牌型数
    #         lowCount = 0
    #
    #         # 先将小于该牌型的所有牌型相加
    #         for lowType in handsType.keys():
    #
    #             # 直到到了与该牌型相同情况，则退出循环
    #             if type == lowType:
    #                 break
    #
    #             lowCount += handsType[lowType]
    #
    #         PHS += (handsType[type] / count) * (lowCount / count)


    # 加入预测值的手牌强度
    # HS = HS + (1-HS) * PHS

    return HS

# 判断是不是输太多
def judgeLoseMuch(alreadyWinChips,currentBout):
    if alreadyWinChips + getWinMinChips(currentBout) <= (getWinMinChips(currentBout)) * 0.7 and alreadyWinChips < 0:
        print("True!!!!!!!!!!!!")
        return True
    else:
        return False

#返回所赢筹码的相反数
def oppositeAlreadyWinChips(alreadyWinChips):
    return -alreadyWinChips


# 返回下大注的确切的值
def betBigChips(currentBout,alreadyWinChips):
    # 加201 是为了设置下限
    bigChips = int(getWinMinChips(currentBout) + winLowLimit + oppositeAlreadyWinChips(alreadyWinChips) + 201)
    if bigChips >= 101:
        return bigChips
    else:
        return 101

# preflop阶段决策
def doPreflop(sk,opAction,alreadyWinChips,currentBout):
    global myCount,myRestChips,myLastPutChips,chipsPool,lastPhaseMyRestChips

    action = None

    HS = Search_1.preflop(handCards)
    print("handCards: " + str(handCards))
    print("HS:" + str(HS))

    if HS >= 13:
        print("BigPreflop!！！")

    elif HS >= 9  and HS < 13:
        print("MiddlePreflop!！！")

    if position == "BIGBLIND":

        if myCount == 0:

            #如果对手选择跟注
            if opAction[0] == 'call':
                opactionsInpreflop['callOrCheck']+=1
                if HS >= 13 and action is None:
                    if int(betBigChips(currentBout,alreadyWinChips) * 0.125) > 201:
                        action = "raise " + str(int(betBigChips(currentBout,alreadyWinChips) * 0.125))
                        myRestChips = lastPhaseMyRestChips - int((betBigChips(currentBout,alreadyWinChips) * 0.125))
                    else:
                        action = "raise 201"
                        myRestChips = lastPhaseMyRestChips - 201

                elif HS >= 5 and HS <13  and action is None:
                    action = "raise 201"
                    myRestChips = lastPhaseMyRestChips - 201

                elif HS < 5 and action is None:
                    # action = "check"
                    action = "fold"


            # 如果对手选择加注
            elif opAction[0] == "raise":
                opactionsInpreflop['raise']+=1
                if HS >= 13 and action is None:
                    if int(betBigChips(currentBout,alreadyWinChips) * 0.125) > 201 and (opAction[1] * 2) > int(betBigChips(currentBout,alreadyWinChips) * 0.125):
                        action = "raise " + str(opAction[1] * 2)
                        myRestChips = lastPhaseMyRestChips - int(opAction[1] * 2)

                    elif int(betBigChips(currentBout,alreadyWinChips) * 0.125) > 201:
                        action = "raise " + str(int(betBigChips(currentBout, alreadyWinChips) * 0.125))
                        myRestChips = lastPhaseMyRestChips - int((betBigChips(currentBout, alreadyWinChips) * 0.125))
                    else:
                        action = "raise " + str(opAction[1] * 2)
                        myRestChips = lastPhaseMyRestChips - int(opAction[1] * 2)

                if myRestChips <= 0:
                    action = "allin"
                    myRestChips = 0

                elif HS >= 9 and HS <13 and action is None:

                    if opAction[1] < betLine(alreadyWinChips,currentBout,0.25):
                        action = "raise " + str(opAction[1] * 2)
                        myRestChips = lastPhaseMyRestChips - int(opAction[1] * 2)
                    elif opAction[1] >= betLine(alreadyWinChips,currentBout,0.25):
                        # action = "check"
                        action = "call"


                    if myRestChips <= 0:
                        action = "allin"
                        myRestChips = 0


                elif HS >= 3 and HS < 9 and action is None:

                    # action = "check"
                    action = "call"

                    # if opAction[1] < betLine(alreadyWinChips,currentBout,0.25) or betLine(alreadyWinChips,currentBout,0.25) == betline:
                    #     action = "check"
                    # elif opAction[1] >= betLine(alreadyWinChips,currentBout,0.25) and HS >= 7 and betLine(alreadyWinChips,currentBout,0.25) != betline:
                    #     action = "check"
                    # elif opAction[1] >= betLine(alreadyWinChips,currentBout,0.25) and betLine(alreadyWinChips,currentBout,0.25) != betline:
                    #     action = "fold"

                    # if myRestChips <= 0:
                    #     if HS >= 7 :
                    #         action = "allin"
                    #         myRestChips = 0
                    #     else:
                    #         action = "fold"


                elif HS >= 1 and HS < 3 and action is None:
                    # options = ["fold", "check"]
                    # action = options[random.randint(0, 1)]

                    # action = "check"
                    action = "call"

                    # if action == "check":
                    #     if opAction[1] >= betLine(alreadyWinChips,currentBout,0.25):
                    #         action = "fold"

                elif HS < 1 and action is None:
                    # action = "check"
                    action = "call"
                    # action = "fold"


            # 如果对手选择allin
            elif opAction[0] == "allin" and action is None:
                opactionsInpreflop['3bet'] += 1
                action = "call"

                # if HS >= 13:
                #     action = "check"
                # else:
                #     action = "fold"


            if action is None:
                action = "fold"

            myCount = myCount + 1

            print("myAction: " + action)
            sk.send(action.encode())

        else:

            # 如果对手选择加注
            if opAction[0] == "raise":
                opactionsInpreflop['3bet']+=1
                if HS >= 13 and action is None:
                    if myCount <= 2:
                        if int(betBigChips(currentBout,alreadyWinChips) * 0.125) > 201 and (opAction[1] * 2) > int(betBigChips(currentBout,alreadyWinChips) * 0.125):
                            action = "raise " + str(opAction[1] * 2)
                            myRestChips = lastPhaseMyRestChips - int(opAction[1] * 2)

                        elif int(betBigChips(currentBout,alreadyWinChips) * 0.125) > 201:
                            action = "raise " + str(int(betBigChips(currentBout, alreadyWinChips) * 0.125))
                            myRestChips = lastPhaseMyRestChips - int((betBigChips(currentBout, alreadyWinChips) * 0.125))
                        else:
                            action = "raise " + str(opAction[1] * 2)
                            myRestChips = lastPhaseMyRestChips - int(opAction[1] * 2)

                    else:
                        action = "call"
                        myRestChips = lastPhaseMyRestChips - int(opAction[1])

                if myRestChips <= 0:
                    action = "allin"
                    myRestChips = 0

                elif HS >= 9 and HS < 13 and action is None:

                    if myCount <= 1:
                        if opAction[1] < betLine(alreadyWinChips,currentBout,0.25):
                            action = "raise " + str(opAction[1] * 2)
                            myRestChips = lastPhaseMyRestChips - int(opAction[1] * 2)

                        elif opAction[1] >= betLine(alreadyWinChips,currentBout,0.25) and betLine(alreadyWinChips,currentBout,0.25) > (betline + 100):
                            action = "fold"

                        else:
                            action = "call"
                            myRestChips = lastPhaseMyRestChips - int(opAction[1])

                    else:

                        if opAction[1] >= betLine(alreadyWinChips, currentBout, 0.5) and betLine(alreadyWinChips,currentBout, 0.5) > (betline + 100):
                            action = "fold"

                        else:
                            action = "call"
                            myRestChips = lastPhaseMyRestChips - int(opAction[1])

                    if myRestChips <= 0:
                        action = "allin"
                        myRestChips = 0

                elif HS >= 3 and HS < 9 and action is None:

                    # action = "call"
                    # myRestChips = lastPhaseMyRestChips - opAction[1]

                    if opAction[1] < betLine(alreadyWinChips,currentBout,0.25) or betLine(alreadyWinChips,currentBout,0.25) <= (betline + 100):
                        action = "call"
                        myRestChips = lastPhaseMyRestChips - int(opAction[1])
                    elif opAction[1] >= betLine(alreadyWinChips,currentBout,0.25) and HS >= 7 and betLine(alreadyWinChips,currentBout,0.25) > (betline + 100):
                        action = "call"
                        myRestChips = lastPhaseMyRestChips - int(opAction[1])
                    elif opAction[1] >= betLine(alreadyWinChips,currentBout,0.25) and betLine(alreadyWinChips,currentBout,0.25) > (betline + 100):
                        action = "fold"

                    if myRestChips <= 0:
                        # if HS >= 7 :
                        #     action = "allin"
                        #     myRestChips = 0
                        # else:
                        action = "fold"

                elif HS >= 1 and HS < 3 and action is None:
                    # options = ["fold", "call"]
                    # action = options[random.randint(0, 1)]

                    action = "call"

                    if action == "call":
                        if opAction[1] < betLine(alreadyWinChips,currentBout,0.125) or betLine(alreadyWinChips,currentBout,0.125) <= (betline + 100):
                            myRestChips = lastPhaseMyRestChips - int(opAction[1])

                            if myRestChips <= 0:
                                action = "fold"

                        else:
                            action = "fold"

                elif HS < 1 and action is None:
                    action = "fold"

            # 如果对手选择allin
            elif opAction[0] == "allin" and action is None:
                opactionsInpreflop['3bet'] += 1
                if HS >= 13:
                    action = "call"
                    myRestChips = 0
                else:
                    action = "fold"

            if action is None:
                action = "fold"


            myCount = myCount + 1

            print("myAction: " + action)
            sk.send(action.encode())

    elif position == "SMALLBLIND":


        if myCount == 0:

            if HS >= 13 and action is None:
                if int(betBigChips(currentBout, alreadyWinChips) * 0.125) > 201:
                    action = "raise " + str(int(betBigChips(currentBout, alreadyWinChips) * 0.125))
                    myRestChips = lastPhaseMyRestChips - int((betBigChips(currentBout, alreadyWinChips) * 0.125))
                else:
                    action = "raise 201"
                    myRestChips = lastPhaseMyRestChips - 201

            elif HS >= 3 and HS < 13 and action is None:
                action = "call"

                myRestChips -= 50

            elif HS >= 1 and HS < 3 and action is None:
                action = "call"

                myRestChips -= 50

            elif HS < 1 and action is None:
                options = ["call","fold"]
                action = options[random.randint(0,1)]
                if action == "call":
                    myRestChips -= 50

            if action is None:
                action = "fold"


            myCount = myCount + 1

            print("myAction: " + action)
            sk.send(action.encode())

        else:

            # 如果对手选择加注
            if opAction[0] == "raise":

                if HS >= 13 and action is None:
                    if myCount <= 2:
                        if int(betBigChips(currentBout,alreadyWinChips) * 0.125) > 201 and (opAction[1] * 2) > int(betBigChips(currentBout,alreadyWinChips) * 0.125):
                            action = "raise " + str(opAction[1] * 2)
                            myRestChips = lastPhaseMyRestChips - int(opAction[1] * 2)

                        elif int(betBigChips(currentBout,alreadyWinChips) * 0.125) > 201:
                            action = "raise " + str(int(betBigChips(currentBout, alreadyWinChips) * 0.125))
                            myRestChips = lastPhaseMyRestChips - int((betBigChips(currentBout, alreadyWinChips) * 0.125))
                        else:
                            action = "raise " + str(opAction[1] * 2)
                            myRestChips = lastPhaseMyRestChips - int(opAction[1] * 2)
                    else:
                        action = "call"
                        myRestChips = lastPhaseMyRestChips - int(opAction[1])

                if myRestChips <= 0:
                    action = "allin"
                    myRestChips = 0

                elif HS >= 9 and HS <13 and action is None:

                    if opAction[1] >= betLine(alreadyWinChips, currentBout, 0.25) and betLine(alreadyWinChips,currentBout, 0.25) > (betline + 100):
                        action = "fold"

                    else:
                        action = "call"
                        myRestChips = lastPhaseMyRestChips - int(opAction[1])


                    if myRestChips <= 0:
                        action = "allin"
                        myRestChips = 0


                elif HS >= 3 and HS < 9 and action is None:

                    # action = "call"
                    # myRestChips = lastPhaseMyRestChips - opAction[1]

                    if opAction[1] < betLine(alreadyWinChips,currentBout,0.25) or betLine(alreadyWinChips,currentBout,0.25) <= (betline + 100):
                        action = "call"
                        myRestChips = lastPhaseMyRestChips - int(opAction[1])
                    elif opAction[1] >= betLine(alreadyWinChips,currentBout,0.25) and HS >= 7 and betLine(alreadyWinChips,currentBout,0.25) > (betline + 100):
                        action = "call"
                        myRestChips = lastPhaseMyRestChips - int(opAction[1])
                    elif opAction[1] >= betLine(alreadyWinChips,currentBout,0.25) and betLine(alreadyWinChips,currentBout,0.25) > (betline + 100):
                        action = "fold"

                    if myRestChips <= 0:
                        # if HS >= 7:
                        #     action = "allin"
                        #     myRestChips = 0
                        # else:
                        action = "fold"

                elif HS >= 1 and HS < 3 and action is None:
                    # options = ["fold", "call"]
                    # action = options[random.randint(0, 1)]

                    action = "call"


                    if action == "call":
                        if opAction[1] < betLine(alreadyWinChips,currentBout,0.125) or betLine(alreadyWinChips,currentBout,0.125) <= (betline + 100):
                            myRestChips = lastPhaseMyRestChips - int(opAction[1])

                            if myRestChips <= 0:
                                action = "fold"

                        else:
                            action = "fold"


                elif HS < 1 and action is None:
                    action = "fold"


            # 如果对方选择check
            elif opAction[0] == "check":

                if HS >= 13 and action is None:
                    if int(betBigChips(currentBout,alreadyWinChips) * 0.125) > 201:
                        action = "raise " + str(int(betBigChips(currentBout, alreadyWinChips) * 0.125))
                        myRestChips = lastPhaseMyRestChips - int((betBigChips(currentBout, alreadyWinChips) * 0.125))
                    else:
                        action = "raise 201"
                        myRestChips = lastPhaseMyRestChips - 201


                    if myRestChips <= 0:
                        action = "allin"
                        myRestChips = 0

                else:
                    action = "call"

                # # 程序的特殊设定，对方check 我方call 之后 拥有的筹码量为 19900
                # myRestChips = 19900


            # 如果对手选择allin
            elif opAction[0] == "allin" and action is None:
                if HS >= 13:
                    action = "call"
                    myRestChips = 0
                else:
                    action = "fold"



            if action is None:
                action = "fold"



            myCount = myCount + 1

            print("myAction: " + action)
            sk.send(action.encode())

# flop和turn阶段决策
def doFlopAndTurn(sk,opAction,alreadyWinChips,currentBout):

    global myCount,myRestChips

    # 最终行为
    action = None


    # 经过模拟之后得到的手牌强度
    HS = handStrength(handCards,boardCards)
    print("HS:" + str(HS))

    #    开始做决策
    if position == "SMALLBLIND":

        if opAction[0] == "allin" and action is None:
            if HS >= 0.95:
                action = "call"
                myRestChips = 0
            else:
                action = "fold"


        if HS >= 0.95 and action is None:

            randomChoice = random.random()

            if randomChoice <= 0.9:

                action = "raise"

                # if opAction[0] == "raise":
                #     if opAction[1] >= betLine(alreadyWinChips, currentBout, 0.25) and betLine(alreadyWinChips,currentBout,0.25) != betline:
                #         if HS < 0.95:
                #             action = "fold"
#todo 随机决策，可以通过修改参数控制其激进程度
            elif randomChoice > 0.9:
                if opAction[0] == "raise":

                    action = "call"
                    myRestChips = lastPhaseMyRestChips - int(opAction[1])

                    # if opAction[1] >= betLine(alreadyWinChips, currentBout, 0.25) and betLine(alreadyWinChips,currentBout,0.25) != betline:
                    #     if HS < 0.95:
                    #         action = "fold"

                elif opAction[0] == "check":
                    if opCheckCount >= 1:
                        if random.random() < 0.95:
                            if int(betBigChips(currentBout, alreadyWinChips) * 0.125) > 101:
                                action = "raise " + str(int(betBigChips(currentBout, alreadyWinChips) * 0.125))
                                myRestChips = lastPhaseMyRestChips - (int(betBigChips(currentBout, alreadyWinChips) * 0.125))
                            else:
                                action = "raise " + str(101)
                                myRestChips = lastPhaseMyRestChips - int(101)
                        else:
                            action = "call"
                    else:
                        action = "call"


            if opAction[0] == "raise" and action == "raise":
                action = "raise " + str(opAction[1] * 2)
                myRestChips = lastPhaseMyRestChips - int(opAction[1] * 2)

            elif action == "raise":
                if int(betBigChips(currentBout, alreadyWinChips) * 0.125) > 101:
                    action = "raise " + str(int(betBigChips(currentBout, alreadyWinChips) * 0.125))
                    myRestChips = lastPhaseMyRestChips - (int(betBigChips(currentBout, alreadyWinChips) * 0.125))
                else:
                    action = "raise 101"
                    myRestChips = lastPhaseMyRestChips - 101

            # elif action == "raise":
            #     action = "raise 101"
            #     myRestChips = lastPhaseMyRestChips - 101

            if myRestChips <= 0:
                action = "allin"
                myRestChips = 0

        elif HS < 0.95 and HS >= 0.8 and action is None:

            randomChoice = random.random()

            if randomChoice <= 0.6:

                action = "raise"

                if opAction[0] == "raise":
                    if opAction[1] >= betLine(alreadyWinChips, currentBout, 0.25) and betLine(alreadyWinChips,currentBout,0.25) != betline:
                        action = "fold"

            elif randomChoice > 0.6:
                if opAction[0] == "raise":

                    action = "call"
                    myRestChips = lastPhaseMyRestChips - int(opAction[1])

                    if opAction[1] >= betLine(alreadyWinChips, currentBout, 0.25) and betLine(alreadyWinChips,currentBout,0.25) != betline:
                        action = "fold"

                elif opAction[0] == "check":
                    if opCheckCount >= 1:
                        if random.random() < 0.95:
                            action = "raise " + str(101)
                            myRestChips = lastPhaseMyRestChips - int(101)
                        else:
                            action = "call"
                    else:
                        action = "call"


            if opAction[0] == "raise" and action == "raise":
                action = "raise " + str(opAction[1] * 2)
                myRestChips = lastPhaseMyRestChips - int(opAction[1] * 2)
            elif action == "raise":
                action = "raise 101"
                myRestChips = lastPhaseMyRestChips - 101

            if myRestChips <= 0:
                action = "fold"


        elif HS < 0.8 and HS >= 0.6 and action is None:

            randomChoice = random.random()

            if randomChoice <= 0.5:
                action = "raise"

                if opAction[0] == "raise":

                    if opAction[1] >= betLine(alreadyWinChips, currentBout, 0.25) and betLine(alreadyWinChips,currentBout,0.25) != betline:
                        action = "fold"

            elif randomChoice > 0.5:
                if opAction[0] == "raise":

                    if opAction[1] >= betLine(alreadyWinChips, currentBout, 0.25) and betLine(alreadyWinChips,currentBout,0.25) != betline:
                        action = "fold"
                    elif opAction[1] < betLine(alreadyWinChips,currentBout,0.25):
                        action = "call"
                        myRestChips = lastPhaseMyRestChips - int(opAction[1])
                    elif opAction[1] >= betLine(alreadyWinChips,currentBout,0.25) and HS >= 0.7:
                        action = "call"
                        myRestChips = lastPhaseMyRestChips - int(opAction[1])
                    elif opAction[1] >= betLine(alreadyWinChips,currentBout,0.25):
                        action = "fold"




                elif opAction[0] == "check":
                    if opCheckCount >= 1:
                        if random.random() < 0.95:
                            action = "raise " + str(101)
                            myRestChips = lastPhaseMyRestChips - int(101)
                        else:
                            action = "call"
                    else:
                        action = "call"



            if opAction[0] == "raise" and action == "raise":

                # print("opAction[1] : " + str(opAction[1]))
                # print("betLine : " + str(betLine(alreadyWinChips,currentBout,0.25)))

                if opAction[1] < betLine(alreadyWinChips,currentBout,0.25):
                    action = "raise " + str(opAction[1] * 2)
                    myRestChips = lastPhaseMyRestChips - int(opAction[1] * 2)
                elif opAction[1] >= betLine(alreadyWinChips,currentBout,0.25) and HS >= 0.7:
                    action = "call"
                    myRestChips = lastPhaseMyRestChips - int(opAction[1])
                elif opAction[1] >= betLine(alreadyWinChips,currentBout,0.25):
                    action = "fold"

            elif action == "raise":
                action = "raise 101"
                myRestChips = lastPhaseMyRestChips - 101

            if myRestChips <= 0:
                action = "fold"



        elif HS < 0.6 and HS >= 0.5 and action is None:


            if opAction[0] == "raise":

                # print("opAction[1] : " + str(opAction[1]))
                # print("betLine : " + str(betLine(alreadyWinChips,currentBout,0.25)))

                if opAction[1] < betLine(alreadyWinChips,currentBout,0.25):
                    action = "call"
                    myRestChips = lastPhaseMyRestChips - int(opAction[1])
                elif opAction[1] >= betLine(alreadyWinChips,currentBout,0.25):
                    action = "fold"

            elif opAction[0] == "check":
                if opCheckCount >= 1:
                    if random.random() < 0.95:
                        action = "raise " + str(101)
                        myRestChips = lastPhaseMyRestChips - int(101)
                    else:
                        action = "call"
                else:
                    action = "call"

            if myRestChips <= 0:
                action = "fold"

        # 如果对方check过多，下比较小的注吓唬对手 todo：没动作问题？
        elif HS < 0.5 and HS >= 0.1 and action is None:
            if opAction[0] == "check":
                if opCheckCount >= 1:
                    if random.random() < 0.95:
                        action = "raise " + str(101)
                        myRestChips = lastPhaseMyRestChips - int(101)
                    else:
                        action = "call"
            else:
                action = "fold"


        elif HS < 0.5 and action is None:
            if opAction[0] == "check":
                action = "call"
            else:
                action = "fold"


        if action is None:
            action = "fold"


        if myCount >= 1 and HS >= 0.5 and "raise" in action:
            # myCount >1 时行为最高只有call，如果行为为raise 则先还原剩余筹码量
            myRestChips = myRestChips + opAction[1] * 2

            if opAction[0] == "raise":
                if opAction[1] < betLine(alreadyWinChips,currentBout,0.25):
                    action = "call"
                    myRestChips = lastPhaseMyRestChips - int(opAction[1])
                elif opAction[1] >= betLine(alreadyWinChips,currentBout,0.25):

                    if opAction[1] >= betLine(alreadyWinChips,currentBout,0.5) and myCount == 1 and betLine(alreadyWinChips,currentBout,0.5) != betline:
                        if HS >=0.95:
                            action = "call"
                            myRestChips = lastPhaseMyRestChips - int(opAction[1])
                        else:
                            action = "fold"

                    elif HS >= 0.7:
                        action = "call"
                        myRestChips = lastPhaseMyRestChips - int(opAction[1])
                    elif HS < 0.7:
                        action = "fold"

            elif opAction[0] == "check":
                if opCheckCount >= 1:
                    if random.random() < 0.95:
                        action = "raise " + str(101)
                        myRestChips = lastPhaseMyRestChips - int(101)
                    else:
                        action = "call"
                else:
                    action = "call"

            if myRestChips <= 0:
                if HS >= 0.95:
                    action = "allin"
                else:
                    action = "fold"

        myCount = myCount + 1

        print("myAction: " + action)
        sk.send(action.encode())


    elif position == "BIGBLIND":


        if myCount == 0:


            if HS >= 0.95 and action is None:

                randomChoice = random.random()



                if randomChoice <= 0.9:

                    if int(betBigChips(currentBout, alreadyWinChips) * 0.125) > 101:
                        action = "raise " + str(int(betBigChips(currentBout, alreadyWinChips) * 0.125))
                        myRestChips = lastPhaseMyRestChips - (int(betBigChips(currentBout, alreadyWinChips) * 0.125))
                    else:
                        action = "raise 101"
                        myRestChips = lastPhaseMyRestChips - 101


                    # action = "raise 101"
                    # myRestChips = lastPhaseMyRestChips - 101

                elif randomChoice > 0.9:
                    action = "check"


            elif HS < 0.95 and HS >= 0.8 and action is None:

                randomChoice = random.random()

                if randomChoice <= 0.6:
                    action = "raise 101"
                    myRestChips = lastPhaseMyRestChips - 101
                elif randomChoice > 0.6:
                    action = "check"


            elif HS < 0.8 and HS >= 0.6 and action is None:

                randomChoice = random.random()

                if randomChoice <= 0.5:
                    action = "raise 101"
                    myRestChips = lastPhaseMyRestChips - 101
                elif randomChoice > 0.5:
                    action = "check"



            elif HS < 0.6 and HS >= 0.5 and action is None:

                action = "check"


            elif HS < 0.5 and action is None:

                # 先不弃牌
                action = "check"



            if action is None:
                action = "fold"


            myCount = myCount + 1

            print("myAction: " + action)
            sk.send(action.encode())

        else:

            if opAction[0] == "allin" and action is None:
                if HS >= 0.95:
                    action = "call"
                    myRestChips = 0
                else:
                    action = "fold"

            if HS >= 0.9 and action is None:

                randomChoice = random.random()

                if randomChoice <= 0.9:
                    action = "raise"

                    if opAction[1] >= betLine(alreadyWinChips, currentBout, 0.25) and myCount == 1 and betLine(alreadyWinChips, currentBout, 0.25) != betline:
                        if HS < 0.95:
                            action = "fold"

                elif randomChoice > 0.9:
                    if opAction[0] == "raise":
                        action = "call"
                        # 大盲注在做第二次行为时对方只有raise
                        myRestChips = lastPhaseMyRestChips - int(opAction[1])

                        if opAction[1] >= betLine(alreadyWinChips, currentBout, 0.25) and myCount == 1 and betLine(alreadyWinChips, currentBout, 0.25) != betline:
                            if HS < 0.95:
                                action = "fold"


                if opAction[0] == "raise" and action == "raise":
                    action = "raise " + str(opAction[1] * 2)
                    myRestChips = lastPhaseMyRestChips - int(opAction[1] * 2)


                if myRestChips <= 0:
                    action = "allin"
                    myRestChips = 0

            elif HS < 0.9 and HS >= 0.8 and action is None:

                randomChoice = random.random()

                if randomChoice <= 0.6:

                    action = "raise"

                    if opAction[1] >= betLine(alreadyWinChips, currentBout, 0.25) and myCount == 1 and betLine(alreadyWinChips, currentBout, 0.25) != betline:
                        action = "fold"

                elif randomChoice > 0.6:
                    if opAction[0] == "raise":
                        action = "call"
                        # 大盲注在做第二次行为时对方只有raise
                        myRestChips = lastPhaseMyRestChips - int(opAction[1])

                        if opAction[1] >= betLine(alreadyWinChips, currentBout, 0.25) and myCount == 1 and betLine(alreadyWinChips, currentBout, 0.25) != betline:
                            action = "fold"


                if opAction[0] == "raise" and action == "raise":
                    action = "raise " + str(opAction[1] * 2)
                    myRestChips = lastPhaseMyRestChips - int(opAction[1] * 2)


                if myRestChips <= 0:
                    action = "fold"


            elif HS < 0.8 and HS >= 0.6 and action is None:

                randomChoice = random.random()

                if randomChoice <= 0.5:

                    action = "raise"

                    if opAction[1] >= betLine(alreadyWinChips, currentBout, 0.25) and myCount == 1 and betLine(alreadyWinChips, currentBout, 0.25) != betline:
                        action = "fold"

                elif randomChoice > 0.5:
                    if opAction[0] == "raise":

                        if opAction[1] >= betLine(alreadyWinChips, currentBout, 0.25) and myCount == 1 and betLine(alreadyWinChips, currentBout, 0.25) != betline:
                            action = "fold"
                        elif opAction[1] < betLine(alreadyWinChips,currentBout,0.25):
                            action = "call"
                            myRestChips = lastPhaseMyRestChips - int(opAction[1])
                        elif opAction[1] >= betLine(alreadyWinChips,currentBout,0.25) and HS >= 0.7:
                            action = "call"
                            myRestChips = lastPhaseMyRestChips - int(opAction[1])
                        elif opAction[1] >= betLine(alreadyWinChips,currentBout,0.25):
                            action = "fold"


                if opAction[0] == "raise" and action == "raise":

                    # print("opAction[1] : " + str(opAction[1]))
                    # print("betLine : " + str(betLine(alreadyWinChips, currentBout, 0.25)))

                    if opAction[1] < betLine(alreadyWinChips,currentBout,0.25):
                        action = "raise " + str(opAction[1] * 2)
                        myRestChips = lastPhaseMyRestChips - int(opAction[1] * 2)
                    elif opAction[1] >= betLine(alreadyWinChips,currentBout,0.25) and HS >= 0.7:
                        action = "call"
                        myRestChips = lastPhaseMyRestChips - int(opAction[1])
                    elif opAction[1] >= betLine(alreadyWinChips,currentBout,0.25):
                        action = "fold"

                if myRestChips <= 0:
                    action = "fold"


            elif HS < 0.6 and HS >= 0.5 and action is None:

                if opAction[0] == "raise":

                    # print("opAction[1] : " + str(opAction[1]))
                    # print("betLine : " + str(betLine(alreadyWinChips, currentBout, 0.25)))

                    if opAction[1] < betLine(alreadyWinChips,currentBout,0.25):
                        action = "call"
                        myRestChips = lastPhaseMyRestChips - int(opAction[1])
                    elif opAction[1] >= betLine(alreadyWinChips,currentBout,0.25):
                        action = "fold"

                if myRestChips <= 0:
                    action = "fold"


            elif HS < 0.5 and action is None:
                action = "fold"


            if action is None:
                action = "fold"

            if myCount >= 1 and HS >= 0.5 and "raise" in action:
                # 先还原所剩筹码
                myRestChips = myRestChips + opAction[1] * 2

                if opAction[0] == "raise":
                    if opAction[1] < betLine(alreadyWinChips,currentBout,0.25):
                        action = "call"
                        myRestChips = lastPhaseMyRestChips - int(opAction[1])
                    elif opAction[1] >= betLine(alreadyWinChips,currentBout,0.25):

                        if opAction[1] >= betLine(alreadyWinChips, currentBout, 0.5) and myCount == 1 and betLine(alreadyWinChips, currentBout, 0.5) != betline:
                            if HS >= 0.95:
                                action = "call"
                                myRestChips = lastPhaseMyRestChips - int(opAction[1])
                            else:
                                action = "fold"

                        elif HS >= 0.7:
                            action = "call"
                            myRestChips = lastPhaseMyRestChips - int(opAction[1])
                        elif HS < 0.7:
                            action = "fold"

                if myRestChips <= 0:
                    if HS >= 0.95:
                        action = "allin"
                    else:
                        action = "fold"





            myCount = myCount + 1

            print("myAction: " + action)
            sk.send(action.encode())


#河牌阶段的决策
def doRiver(sk,opAction,alreadyWinChips,currentBout):

    global myCount,myRestChips

    # 最终行为
    action = None


    # 经过模拟之后得到的手牌强度
    HS = handStrength(handCards,boardCards)
    print("HS:" + str(HS))

    #    开始做决策
    if position == "SMALLBLIND":


        if opAction[0] == "allin" and action is None:
            if HS >= 0.95:
                action = "call"
                myRestChips = 0
            else:
                action = "fold"

        if HS >= 0.95 and action is None:
            if opAction[0] == "raise":
                if (opAction[1] * 2) > (betBigChips(currentBout,alreadyWinChips)):
                    action = "raise " + str(opAction[1] * 2)
                    myRestChips = lastPhaseMyRestChips - int(opAction[1] * 2)
                else:
                    action = "raise " + str(betBigChips(currentBout,alreadyWinChips))
                    myRestChips = lastPhaseMyRestChips - (betBigChips(currentBout,alreadyWinChips))

            elif opAction[0] == "check":
                action = "raise " + str(betBigChips(currentBout,alreadyWinChips))
                myRestChips = lastPhaseMyRestChips - (betBigChips(currentBout,alreadyWinChips))

            if myRestChips <= 0:
                action = "allin"
                myRestChips = 0

        elif HS >= 0.9 and action is None:
            if opAction[0] == "raise":
                # 输太多后的视情况下大注
                if judgeLoseMuch(alreadyWinChips, currentBout) and (opAction[1] * 2) >= betBigChips(currentBout,alreadyWinChips):
                    action = "raise " + str(opAction[1] * 2)
                    myRestChips = lastPhaseMyRestChips - int(opAction[1] * 2)

                elif judgeLoseMuch(alreadyWinChips, currentBout):
                    action = "raise " + str(betBigChips(currentBout, alreadyWinChips))
                    myRestChips = lastPhaseMyRestChips - (betBigChips(currentBout, alreadyWinChips))

                else:
                    if int(betBigChips(currentBout, alreadyWinChips) * 0.25) > 101 and (opAction[1] * 2) >= int(betBigChips(currentBout, alreadyWinChips) * 0.25):
                        action = "raise " + str(opAction[1] * 2)
                        myRestChips = lastPhaseMyRestChips - int(opAction[1] * 2)

                    elif int(betBigChips(currentBout, alreadyWinChips) * 0.25) > 101:
                        action = "raise " + str(int(betBigChips(currentBout, alreadyWinChips) * 0.25))
                        myRestChips = lastPhaseMyRestChips - int(betBigChips(currentBout, alreadyWinChips) * 0.25)
                    else:
                        action = "raise " + str(opAction[1] * 2)
                        myRestChips = lastPhaseMyRestChips - int(opAction[1] * 2)


            elif opAction[0] == "check":
                if judgeLoseMuch(alreadyWinChips, currentBout):
                    action = "raise " + str(betBigChips(currentBout, alreadyWinChips))
                    myRestChips = lastPhaseMyRestChips - (betBigChips(currentBout, alreadyWinChips))

                else:
                    if int(betBigChips(currentBout, alreadyWinChips) *0.25) > 101:
                        action = "raise " + str(int(betBigChips(currentBout, alreadyWinChips) *0.25))
                        myRestChips = lastPhaseMyRestChips - int(betBigChips(currentBout, alreadyWinChips) *0.25)
                    else:
                        action = "raise 101"
                        myRestChips = lastPhaseMyRestChips - 101

            if myRestChips <= 0:
                action = "allin"
                myRestChips = 0

        elif HS < 0.9 and HS >= 0.8 and action is None:

            randomChoice = random.random()

            if randomChoice <= 0.1:
                if opAction[0] == "raise":

                    action = "call"
                    myRestChips = lastPhaseMyRestChips - int(opAction[1])

                    # if opAction[1] < betLine(alreadyWinChips, currentBout, 0.25):
                    #     action = "call"
                    #     myRestChips = lastPhaseMyRestChips - opAction[1]
                    # elif opAction[1] >= betLine(alreadyWinChips, currentBout, 0.25):
                    #     action = "fold"

                    if opAction[1] >= betLine(alreadyWinChips, currentBout, 0.25) and betLine(alreadyWinChips,currentBout,0.25) != betline:
                        if HS < 0.85:
                            action = "fold"

                elif opAction[0] == "check":
                    if opCheckCount >= 1:
                        if random.random() < 0.95:
                            action = "raise " + str(101 + round(random.random(),2))
                            myRestChips = lastPhaseMyRestChips - int(101)
                        else:
                            action = "call"
                    else:
                        action = "call"

            elif randomChoice > 0.1:

                action = "raise"

                if opAction[0] == "raise":
                    if opAction[1] >= betLine(alreadyWinChips, currentBout, 0.25) and betLine(alreadyWinChips,currentBout,0.25) != betline:
                        if HS < 0.85:
                            action = "fold"

            if opAction[0] == "raise" and action == "raise":

                if opAction[1] < betLine(alreadyWinChips, currentBout, 0.25):

                    if int(betBigChips(currentBout, alreadyWinChips) * 0.125) > 101 and (opAction[1] * 2) >= int(betBigChips(currentBout, alreadyWinChips) * 0.125):
                        action = "raise " + str(opAction[1] * 2)
                        myRestChips = lastPhaseMyRestChips - int(opAction[1] * 2)
                    elif int(betBigChips(currentBout, alreadyWinChips) * 0.125) > 101:
                        action = "raise " + str(int(betBigChips(currentBout, alreadyWinChips) * 0.125))
                        myRestChips = lastPhaseMyRestChips - int(betBigChips(currentBout, alreadyWinChips) * 0.125)
                    else:
                        action = "raise " + str(opAction[1] * 2)
                        myRestChips = lastPhaseMyRestChips - int(opAction[1] * 2)


                    # action = "raise " + str(opAction[1] * 2)
                    # myRestChips = lastPhaseMyRestChips - opAction[1] * 2



                elif opAction[1] >= betLine(alreadyWinChips, currentBout, 0.25):

                    action = "call"
                    myRestChips = lastPhaseMyRestChips - int(opAction[1])

                    # action = "fold"

            elif action == "raise":
                if int(betBigChips(currentBout, alreadyWinChips) * 0.125) > 101:
                    action = "raise " + str(int(betBigChips(currentBout, alreadyWinChips) * 0.125))
                    myRestChips = lastPhaseMyRestChips - int(betBigChips(currentBout, alreadyWinChips) * 0.125)
                else:
                    action = "raise 101"
                    myRestChips = lastPhaseMyRestChips - 101

            if myRestChips <= 0:
                action = "allin"
                myRestChips = 0

        elif HS < 0.8 and HS >= 0.7 and action is None:

            randomChoice = random.random()

            if randomChoice <= 0.5:

                if opAction[0] == "raise":
                    if opAction[1] >= betLine(alreadyWinChips, currentBout, 0.25) and betLine(alreadyWinChips,currentBout,0.25) != betline:
                        action = "fold"
                    elif opAction[1] < betLine(alreadyWinChips, currentBout, 0.25) or betLine(alreadyWinChips, currentBout, 0.25) == betline:
                        action = "call"
                        myRestChips = lastPhaseMyRestChips - int(opAction[1])

                elif opAction[0] == "check":
                    if opCheckCount >= 1:
                        if random.random() < 0.95:
                            action = "raise " + str(101)
                            myRestChips = lastPhaseMyRestChips - int(101)
                        else:
                            action = "call"
                    else:
                        action = "call"


            elif randomChoice > 0.5:
                action = "raise"

                if opAction[0] == "raise":
                    if opAction[1] >= betLine(alreadyWinChips, currentBout, 0.25) and betLine(alreadyWinChips,currentBout,0.25) != betline:
                        action = "fold"


            if opAction[0] == "raise" and action == "raise":
                if opAction[1] < betLine(alreadyWinChips,currentBout,0.25):
                    action = "raise " + str(opAction[1] * 2)
                    myRestChips = lastPhaseMyRestChips - int(opAction[1] * 2)
                elif opAction[1] >= betLine(alreadyWinChips,currentBout,0.25):

                    action = "call"
                    myRestChips = lastPhaseMyRestChips - int(opAction[1])

                    # if opAction[1] > getWinMinChips(currentBout):
                    #     action = "fold"

                    # action = "fold"

            elif action == "raise":
                action = "raise 101"
                myRestChips = lastPhaseMyRestChips - 101


            # if opAction[0] == "raise":
            #     if opAction[1] >= getWinMinChips(currentBout):
            #         action = "fold"

            if myRestChips <= 0:
                action = "allin"
                myRestChips = 0


        elif HS < 0.7 and HS >= 0.45 and action is None:


            if opAction[0] == "raise":
                if (opAction[1] < betLine(alreadyWinChips, currentBout,0.25)):
                    action = "call"
                    myRestChips = lastPhaseMyRestChips - int(opAction[1])
                elif opAction[1] >= betLine(alreadyWinChips, currentBout,0.25):
                    action = "fold"

            elif opAction[0] == "check":
                if opCheckCount >= 1:
                    if random.random() < 0.95:
                        action = "raise " + str(101)
                        myRestChips = lastPhaseMyRestChips - int(101)
                    else:
                        action = "call"
                else:
                    action = "call"

            if myRestChips <= 0:
                action = "fold"

        # 如果对方check过多，下比较小的注吓唬对手
        if HS < 0.45 and HS >= 0.1 and action is None:
            if opAction[0] == "check":
                if opCheckCount >= 1:
                    if random.random() < 0.95:
                        action = "raise " + str(101)
                        myRestChips = lastPhaseMyRestChips - int(101)
                    else:
                        action = "call"
                else:
                    action = "call"
            else:
                action = "fold"

        elif HS < 0.45 and action is None:
            if opAction[0] == "check":
                action = "call"
            else:
                action = "fold"

        if action is None:
            action = "fold"

        if myCount >= 1 and HS >= 0.45 and "raise" in action:
            myRestChips = myRestChips + opAction[1] * 2
            if opAction[0] == "raise":
                if opAction[1] < betLine(alreadyWinChips, currentBout, 0.25):
                    action = "call"
                    myRestChips = lastPhaseMyRestChips - int(opAction[1])
                elif opAction[1] >= betLine(alreadyWinChips, currentBout, 0.25):

                    if opAction[1] >= betLine(alreadyWinChips,currentBout,0.5) and myCount == 1 and betLine(alreadyWinChips,currentBout,0.5) != betline:
                        if HS >= 0.95:
                            action = "call"
                            myRestChips = lastPhaseMyRestChips - int(opAction[1])
                        else:
                            action = "fold"

                    elif HS >= 0.8 or betLine(alreadyWinChips, currentBout, 0.25) == betline:
                        action = "call"
                        myRestChips = lastPhaseMyRestChips - int(opAction[1])
                    else:
                        action = "fold"

            elif opAction[0] == "check":
                if opCheckCount >= 1:
                    if random.random() < 0.9:
                        action = "raise " + str(101)
                        myRestChips = lastPhaseMyRestChips - int(101)
                    else:
                        action = "call"
                else:
                    action = "call"

            if myRestChips <= 0:
                if HS >= 0.8:
                    action = "allin"
                else:
                    action = "fold"





        myCount = myCount + 1

        print("myAction: " + action)
        sk.send(action.encode())


    elif position == "BIGBLIND":

        if myCount == 0:


            if HS >= 0.95 and action is None:

                action = "raise " + str(betBigChips(currentBout,alreadyWinChips))
                myRestChips = lastPhaseMyRestChips - (int(betBigChips(currentBout,alreadyWinChips)))

                if myRestChips <= 0:
                    action = "allin"
                    myRestChips = 0


            elif HS >= 0.9  and action is None:

                # 输太多后的视情况下大注
                if judgeLoseMuch(alreadyWinChips,currentBout):
                    action = "raise " + str(betBigChips(currentBout,alreadyWinChips))
                    myRestChips = lastPhaseMyRestChips - (int(betBigChips(currentBout,alreadyWinChips)))

                else:
                    if int(betBigChips(currentBout, alreadyWinChips) * 0.25) > 101:
                        action = "raise " + str(int(betBigChips(currentBout, alreadyWinChips) * 0.25))
                        myRestChips = lastPhaseMyRestChips - int(betBigChips(currentBout, alreadyWinChips) *0.25)
                    else:
                        action = "raise 101"
                        myRestChips = lastPhaseMyRestChips - 101

                if myRestChips <= 0:
                    action = "allin"
                    myRestChips = 0


            elif HS >= 0.8 and HS < 0.9 and action is None:

                randomChoice = random.random()

                if randomChoice <= 0.1:
                    action = "check"

                elif randomChoice > 0.1:
                    if int(betBigChips(currentBout, alreadyWinChips) *0.125) > 101:
                        action = "raise " + str(int(betBigChips(currentBout, alreadyWinChips) *0.125))
                        myRestChips = lastPhaseMyRestChips - int(betBigChips(currentBout, alreadyWinChips) *0.125)
                    else:
                        action = "raise 101"
                        myRestChips = lastPhaseMyRestChips - 101

                if myRestChips <= 0:
                    action = "allin"
                    myRestChips = 0

            elif HS < 0.8 and HS >= 0.7 and action is None:
                randomChoice = random.random()

                if randomChoice <= 0.5:
                    action = "check"
                elif randomChoice > 0.5:
                    action = "raise 101"
                    myRestChips = lastPhaseMyRestChips - 101

                if myRestChips <= 0:
                    action = "allin"
                    myRestChips = 0

            elif HS < 0.7 and HS >= 0.45 and action is None:
                action = "check"


            # 先不弃牌
            elif HS < 0.45 and action is None:
                action = "check"




            if action is None:
                action = "fold"


            myCount = myCount + 1

            print("myAction: " + action)
            sk.send(action.encode())

        else:

            if opAction[0] == "allin" and action is None:
                if HS >= 0.95:
                    action = "call"
                    myRestChips = 0
                else:
                    action = "fold"


            if HS >= 0.9  and action is None:
                if opAction[0] == "raise":
                    # 输太多后的视情况下大注
                    if judgeLoseMuch(alreadyWinChips, currentBout) and (opAction[1] * 2) >= betBigChips(currentBout,alreadyWinChips):
                        action = "raise " + str(opAction[1] * 2)
                        myRestChips = lastPhaseMyRestChips - int(opAction[1] * 2)

                    elif judgeLoseMuch(alreadyWinChips, currentBout):
                        action = "raise " + str(betBigChips(currentBout, alreadyWinChips))
                        myRestChips = lastPhaseMyRestChips - (int(betBigChips(currentBout, alreadyWinChips)))

                    else:
                        action = "raise " + str(opAction[1] * 2)
                        myRestChips = lastPhaseMyRestChips - int(opAction[1] * 2)


                if myRestChips <= 0:
                    action = "allin"
                    myRestChips = 0

            elif HS < 0.9 and HS >= 0.8 and action is None:
                randomChoice = random.random()

                if randomChoice <= 0.1:

                    action = "call"
                    myRestChips = lastPhaseMyRestChips - int(opAction[1])

                    if opAction[1] >= betLine(alreadyWinChips, currentBout, 0.25) and betLine(alreadyWinChips,currentBout,0.25) != betline:
                        if HS < 0.85:
                            action = "fold"

                    # if opAction[1] < betLine(alreadyWinChips, currentBout, 0.25):
                    #     action = "call"
                    #     myRestChips = lastPhaseMyRestChips - opAction[1]
                    # elif opAction[1] >= betLine(alreadyWinChips, currentBout, 0.25):
                    #     action = "fold"

                elif randomChoice > 0.1:
                    action = "raise"

                    if opAction[1] >= betLine(alreadyWinChips, currentBout, 0.25) and betLine(alreadyWinChips,currentBout,0.25) != betline:
                        if HS < 0.85:
                            action = "fold"

                if opAction[0] == "raise" and action == "raise":

                    if opAction[1] < betLine(alreadyWinChips, currentBout, 0.25):
                        action = "raise " + str(opAction[1] * 2)
                        myRestChips = lastPhaseMyRestChips - int(opAction[1] * 2)
                    elif opAction[1] >= betLine(alreadyWinChips, currentBout, 0.25):
                        action = "call"
                        myRestChips = lastPhaseMyRestChips - int(opAction[1])

                        # action = "fold"

                if myRestChips <= 0:
                    action = "allin"
                    myRestChips = 0


            elif HS < 0.8 and HS >= 0.7 and action is None:
                randomChoice = random.random()

                if randomChoice <= 0.5:
                    if opAction[0] == "raise":

                        # action = "call"
                        if opAction[1] >= betLine(alreadyWinChips, currentBout, 0.25) and betLine(alreadyWinChips,currentBout,0.25) != betline:
                            action = "fold"
                        elif opAction[1] < betLine(alreadyWinChips, currentBout, 0.25) or betLine(alreadyWinChips, currentBout, 0.25) == betline:
                            action = "call"
                            myRestChips = lastPhaseMyRestChips - int(opAction[1])



                elif randomChoice > 0.5:

                    action = "raise"

                    if opAction[1] >= betLine(alreadyWinChips, currentBout, 0.25) and betLine(alreadyWinChips,currentBout,0.25) != betline:
                        action = "fold"


                if opAction[0] == "raise" and action == "raise":
                    if opAction[1] < betLine(alreadyWinChips,currentBout,0.25):
                        action = "raise " + str(opAction[1] * 2)
                        myRestChips = lastPhaseMyRestChips - int(opAction[1] * 2)
                    elif opAction[1] >= betLine(alreadyWinChips,currentBout,0.25):

                        action = "call"
                        myRestChips = lastPhaseMyRestChips - int(opAction[1])

                        # if opAction[1] > getWinMinChips(currentBout):
                        #     action = "fold"

                        # action = "fold"


                # if opAction[0] == "raise":
                #     if opAction[1] >= getWinMinChips(currentBout):
                #         action = "fold"


                if myRestChips <= 0:
                    action = "allin"
                    myRestChips = 0



            elif HS < 0.7 and HS >= 0.45 and action is None:
                if opAction[0] == "raise":
                    if opAction[1] < betLine(alreadyWinChips, currentBout, 0.25):
                        action = "call"
                        myRestChips = lastPhaseMyRestChips - int(opAction[1])
                    elif opAction[1] >= betLine(alreadyWinChips, currentBout, 0.25):
                        action = "fold"


                if myRestChips <= 0:
                    action = "fold"

            elif HS < 0.45 and action is None:
                action = "fold"

            if action is None:
                action = "fold"

            if myCount >= 1 and HS >= 0.45 and "raise" in action:
                myRestChips = myRestChips + opAction[1] * 2
                if opAction[0] == "raise":
                    if opAction[1] < betLine(alreadyWinChips, currentBout, 0.25):
                        action = "call"
                        myRestChips = lastPhaseMyRestChips - int(opAction[1])
                    elif opAction[1] >= betLine(alreadyWinChips, currentBout, 0.25):

                        if opAction[1] >= betLine(alreadyWinChips, currentBout, 0.5) and myCount == 1 and betLine(alreadyWinChips, currentBout, 0.5) != betline:
                            if HS >= 0.95:
                                action = "call"
                                myRestChips = lastPhaseMyRestChips - int(opAction[1])
                            else:
                                action = "fold"
                        elif HS >= 0.8 or betLine(alreadyWinChips, currentBout, 0.25) == betline:
                            action = "call"
                            myRestChips = lastPhaseMyRestChips - int(opAction[1])
                        else:
                            action = "fold"

#todo:持续fold牌的原因
                if myRestChips <= 0:
                    if HS >= 0.8:
                        action = "allin"
                    else:
                        action = "fold"



            myCount = myCount + 1

            print("myAction: " + action)
            sk.send(action.encode())
