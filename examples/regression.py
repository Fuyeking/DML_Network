#!/usr/bin/env python
# encoding: utf-8
'''
@author: yeqing
@contact: 474387803@qq.com
@software: pycharm
@file: regression.py
@time: 2019/3/27 15:55
@desc:
'''
import matplotlib.pyplot as plt
import torch
import torch.nn.functional as F

import dml.dml_base_thread as dbt
import dml.worker_node as wn

# torch.manual_seed(1)    # reproducible
x = torch.unsqueeze(torch.linspace(-1, 1, 100), dim=1)  # x data (tensor), shape=(100, 1)
y = x.pow(2) + 0.2 * torch.rand(x.size())  # noisy y data (tensor), shape=(100, 1)


# torch can only train on Variable, so convert them to Variable
# The code below is deprecated in Pytorch 0.4. Now, autograd directly supports tensors
# x, y = Variable(x), Variable(y)

# plt.scatter(x.data.numpy(), y.data.numpy())
# plt.show()


class Net(torch.nn.Module):
    def __init__(self, n_feature, n_hidden, n_output):
        super(Net, self).__init__()
        self.hidden = torch.nn.Linear(n_feature, n_hidden)  # hidden layer
        self.predict = torch.nn.Linear(n_hidden, n_output)  # output layer

    def forward(self, x):
        x = F.relu(self.hidden(x))  # activation function for hidden layer
        x = self.predict(x)  # linear output
        return x


def regress_test(ip, port):
    net = Net(n_feature=1, n_hidden=10, n_output=1)  # define the network
    print(net)  # net architecture

    optimizer = torch.optim.SGD(net.parameters(), lr=0.2)
    loss_func = torch.nn.MSELoss()  # this is for regression mean squared loss
    #client = wn.WorkerNode()
    #client.connect(ip, port)
    #client.prepare_net()
    #send_thread = dbt.WorkBaseSendThread("计算节点", client)
    #rec_thread = dbt.WorkBaseRecThread("计算节点", client)
    #send_thread.start()
    #rec_thread.start()

    plt.ion()  # something about plotting
    x_data = []
    y_data = []
    for name, param in net.named_parameters():
        print(name, param.data.grad)
    for t in range(300):
        prediction = net(x)  # input x and predict based on x
        loss = loss_func(prediction, y)  # must be (1. nn output, 2. target)
        optimizer.zero_grad()  # clear gradients for next train
        loss.backward()  # back propagation, compute gradients
        #client.add_send_data(dict(net.named_parameters()))
        optimizer.step()  # apply gradients

        if t % 5 == 0:
            # plot and show learning process
            x_data.append(t / 5)
            y_data.append(loss.data.numpy())
            plt.cla()
            plt.scatter(x.data.numpy(), y.data.numpy())
            plt.plot(x.data.numpy(), prediction.data.numpy(), 'r-', lw=5)
            plt.text(0.5, 0, 'Loss=%.4f' % loss.data.numpy(), fontdict={'size': 20, 'color': 'red'})
            plt.pause(0.1)
    plt.clf()
    print("x_data", x_data)
    print("y_data", y_data)
    plt.plot(x_data, y_data, 'g-', lw=5)
    plt.ioff()
    plt.show()


port = 12345
ip = "127.0.0.1"
if __name__ == '__main__':
    regress_test(ip, port)
