import pickle
import tkinter as tk
from time import sleep
from tkinter import messagebox
from basic import Basic, Basic3, BasicTest
import socket
import time

from basic.Qlearning import QLearning

if __name__ == '__main__':

    # 端口连接

    window = tk.Tk()
    window.geometry('700x500')
    window.title("KnighTeam-Texas")

    # 队名A标签
    teamALabel = tk.Label(window, text='队伍A:')
    teamALabel.place(x=80, y=50, anchor='w')

    # 队名A输入框
    teamAName = 'KnighTeam-TP1'
    teamAEntry = tk.Entry(window, width=20)
    teamAEntry.place(x=150, y=50, anchor='w')
    teamAEntry.insert('end', teamAName)

    # 队名B标签
    teamBLabel = tk.Label(window, text='队伍B:')
    teamBLabel.place(x=350, y=50, anchor='w')

    # 队名B输入框
    teamBname = None
    teamB = tk.Entry(window, width=20)
    teamB.place(x=450, y=50, anchor='w')

    # ip地址标签
    ipLabel = tk.Label(window, text='ServerIp:')
    ipLabel.place(x=80, y=80, anchor='w')

    # ip地址输入框
    ipEntry = tk.Entry(window, width=20)
    ipEntry.place(x=150, y=80, anchor='w')
    # ipEntry.insert('end', '39.107.64.16')
    # ipEntry.insert('end','192.168.2.113')
    # ipEntry.insert('end', '140.143.141.67')
    # ipEntry.insert('end','140.143.141.67')
    # ipEntry.insert('end','39.99.159.225')
    # ipEntry.insert('end','39.99.226.85')
    # 121.89.198.136
    # 39.101.150.158
    # 39.101.162.244

    ipEntry.insert('end', '127.0.0.1')

    # ipEntry.insert('end','192.168.2.113')

    # 端口标签
    portLabel = tk.Label(window, text="ServerPort：")
    portLabel.place(x=350, y=80, anchor='w')

    # 端口输入框
    portEntry = tk.Entry(window, width=20)
    portEntry.place(x=450, y=80, anchor='w')
    portEntry.insert('end', '10001')


    def start():
        sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # try:

        sk.connect((ipEntry.get(), int(portEntry.get())))

        message = sk.recv(1024).decode("utf-8")
        # print(message)
        if message == "name":
            # tk.messagebox.showinfo(title='success',message="Connect successfully!")
            print("TeamName: " + teamAEntry.get())
            print("--------------------------------")
            # 发送队名
            sk.send(str(teamAEntry.get()).encode())

            # 记录已经赢下的筹码量
            alreadyWinChips = 0

            # 开始比赛，共70局
            qlearning = QLearning()
            # with open("q_learning2.pkl",'rb') as f:
            #     qlearning=pickle.load(f)
            for i in range(0, 7000):
                i = i % 70

                if i == 0:
                    # 记录已经赢下的筹码量
                    alreadyWinChips = 0

                # while True:
                print("----------- 第" + str(i + 1) + "局 ----------------")

                start = time.time()

                tempWinChips, winLowLimit = Basic3.basic(sk, alreadyWinChips, i + 1,qlearning)

                end = time.time()

                if ((end - start)) >= 60:
                    print("time!!!!!")

                alreadyWinChips += tempWinChips
                print("alreadyWinChips :" + str(alreadyWinChips))

                # 计算稳赢需要的最小筹码量
                winNeedMinChips = ((70 - (i + 1)) * 75 + winLowLimit) - alreadyWinChips

                print("winNeedMinChips :" + str(winNeedMinChips))

                opWinMinChips = ((70 - (i + 1)) * 75) + alreadyWinChips
                print("opWinMinChips :" + str(opWinMinChips))

            with open("q_learning3.pkl", 'wb') as f:
                pickle.dump(qlearning, f)

            with open('q_table3.txt', 'a') as file:
                for state1, action_values in qlearning.q_table.items():
                    file.write(f"{state1}:{action_values}\n")

            # turnCount = 0
            #
            # while turnCount < 70:
            #     message = sk.recv(1024).decode("utf-8")
            #     print(message)
            #     while True:
            #         strs = input()
            #         sk.send(strs.encode())
            #         message = sk.recv(1024).decode("utf-8")
            #         print(message)

        # except Exception as e:
        #23
        #     tk.messagebox.showerror(title='error', message="Error!")


    # start按钮
    startButton = tk.Button(window, text='start', width='6', command=start)
    startButton.place(x=100, y=120, anchor='w')

    start()
    # window.mainloop()
