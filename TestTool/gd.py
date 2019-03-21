#!/usr/bin/env python
# encoding: utf-8
'''
@author: yeqing
@contact: 474387803@qq.com
@software: pycharm
@file: gd.py
@time: 2019/3/19 22:07
@desc:简单的逻辑回归 用于测试分布式的训练效率
'''
import numpy as np

from dn import client_node as cn


# y = wx+b
# e = y - (wx +b)


def calc_gradient(w_curr, b_curr, points, lr_rate):
    '''
    :param w_curr:
    :param b_curr:
    :param points:
    :param lr_rate:
    :return:
    '''
    w_g = 0
    b_g = 0
    n = float(len(points))
    for i in range(0, len(points)):
        x = points[i, 0]
        y = points[i, 1]
        w_g += (-2 / n) * (y - (w_curr * x + b_curr)) * x
        b_g += (-2 / n) * (y - (w_curr * x + b_curr))
    w_new = w_curr - (lr_rate * w_g)
    b_new = b_curr - (lr_rate * b_g)
    return [w_new, b_new]


def gradient_run(w_i, b_i, num_itr, points, lr, send_obj):
    for i in range(num_itr):
        [w, b] = get_weight_b(send_obj)
        w, b = calc_gradient(w, b, points, lr)
        send_obj.add_send_data(create_send_data(w, b))
    return [w, b]


def compute_total_loss(w, b, points):
    total_loss = 0
    for i in range(0, len(points)):
        x = points[i, 0]
        y = points[i, 1]
        total_loss += (y - (w * x + b)) ** 2
    return total_loss / float(len(points))


def create_send_data(w, b):
    data = dict()
    data['w'] = w
    data['b'] = b
    return data


def get_weight_b(client):
    while True:
        data = client.get_rec_data()
        if data is not None:
            print(data)
            return [data['w'], data['b']]


def gd_test(ip, port):
    points = np.genfromtxt("TestTool/data.csv", delimiter=",")
    learning_rate = 0.0001
    initial_b = 0  # initial y-intercept guess
    initial_w = 0  # initial slope guess
    num_iterations = 1000
    # 引入网络通信接口
    client = cn.ClientNode()
    client.connect(ip, port)
    client.prepare_net()
    send_thread = cn.SendThread("计算节点", client)
    rec_thread = cn.RecThread("计算节点", client)
    client.add_send_data(create_send_data(initial_w, initial_b))
    send_thread.start()
    rec_thread.start()
    print("Starting gradient descent at w = {0}, b = {1}, error = {2}"
          .format(initial_w, initial_b,
                  compute_total_loss(initial_w, initial_b, points))
          )
    print("Running...")
    [w, b] = gradient_run(initial_w, initial_b, num_iterations, points, learning_rate, client)
    print("After {0} iterations w = {1}, b = {2}, error = {3}".
          format(num_iterations, w, b,
                 compute_total_loss(w, b, points))
          )


ip = "127.0.0.1"
port = 12345
if __name__ == '__main__':
    gd_test(ip, port)
