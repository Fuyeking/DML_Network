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

