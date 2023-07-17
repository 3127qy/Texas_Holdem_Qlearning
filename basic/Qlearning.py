# 定义 Q-learning 算法类
import csv

import numpy as np


class QLearning:
    def __init__(self, learning_rate=0.1, discount_factor=0.9, exploration_rate=0.1, eps_decay=0.):
        self.q_table = dict()  # 初始化 Q 表格
        self.lr = learning_rate  # 学习率
        self.df = discount_factor  # 折扣因子
        self.er = exploration_rate  # 探索率
        self.eps_decay = eps_decay

    def choose_action(self, state, valid_moves):
        # 在当前状态下选择行动
        global action
        if np.random.rand() < self.er:
            # 随机选择一个动作
            action = (valid_moves[np.random.choice(len(valid_moves))],)
            # print("---",action)
        else:
            # 选择 Q 值最大的动作/具有最大行动价值的行动
            state_tuple = tuple(state)
            if state_tuple not in self.q_table:
                # 如果状态没有出现过，则初始化行动价值为0
                self.q_table[state_tuple] = dict()
                for move in valid_moves:
                    self.q_table[state_tuple][move] = 0
            action = max(self.q_table[state_tuple], key=self.q_table[state_tuple].get)
            action = ''.join(action)
            action = (action,)
            # print(action)
        self.er *= (1.0 - self.eps_decay)
        return action

        # 更新Q表格

    def update(self, state, action, next_state, reward, valid_moves, valid_moves1):
        state_tuple = tuple(state)
        action_str = action  # 将 action_list 转换为字符串类型
        next_state_tuple = tuple(next_state)

        if state_tuple not in self.q_table:
            # 如果状态没有出现过，则初始化行动价值为 0
            self.q_table[state_tuple] = dict()
            for move in valid_moves:
                self.q_table[state_tuple][move] = 0
        # print(self.q_table)

        if next_state_tuple not in self.q_table:
            # 如果下一个状态没有出现过，则初始化行动价值为 0
            self.q_table[next_state_tuple] = dict()
            for move in valid_moves1:
                self.q_table[next_state_tuple][move] = 0

        next_state_values = self.q_table[next_state_tuple].values()
        if next_state_values:
            max_next_state_value = max(next_state_values)
        else:
            max_next_state_value = 0
        # 更新行动价值
        # print(self.q_table)
        self.q_table[state_tuple][action_str] += self.lr * (
                reward + self.df * max_next_state_value - self.q_table[state_tuple][action_str])

    def get_valid_moves(self, state):
        # TODO: 根据当前状态，获取可行的动作，返回一个列表
        return state
