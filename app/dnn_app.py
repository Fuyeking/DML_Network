#!/usr/bin/env python
# encoding: utf-8
'''
@author: yeqing
@contact: 474387803@qq.com
@software: pycharm
@file: dnn_app.py
@time: 2019/4/1 9:19
@desc:
'''
import dml.dml_base_thread as dbt
import dml.parameter_node as pn


class LossAverageThread(dbt.CalcAverageLoss):
    def __init__(self, thread_name):
        super(LossAverageThread, self).__init__(thread_name)

    def _calc_average_loss(self):
        sum_w = 0.0
        for port, ip in self.ip_set.items():
            self.rec_lock_list[port].acquire()
            if not self.rec_data_list[port].empty():
                data = self.rec_data_list[port].get()
                if data is not None:
                    sum_w += data['Loss']
            self.rec_lock_list[port].release()

        average_loss = dict()
        average_loss['Loss'] = sum_w / self.num
        print("new  loss：", average_loss)
        return average_loss


class LossParameterNode(pn.ParameterServer):
    def __init__(self, ip_set, num):
        super(LossParameterNode, self).__init__(ip_set, num)

    # 允许被子类重载
    def create_avg_calc_thread(self):
        # 每个参数节点创建一个负责计算平均梯度的线程
        self.calc_loss_thread = LossAverageThread("Loss计算平均梯度线程")
        self.calc_loss_thread.init_para(self.ip_set, self.send_queues, self.rec_queues, self.rec_locks,
                                        self.clients_num)
