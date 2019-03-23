#!/usr/bin/python
# -*- coding: UTF-8 -*-
# 文件名：work_simulator1.py
import queue
import socket
import threading

data_size = 1024


class WorkerNode:

    def __init__(self):
        """
        """
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.net_ready = False  # 网络连接准备状态
        self.send_queue = queue.Queue()
        self.rec_queue = queue.Queue()
        self.send_lock = threading.Lock()
        self.rec_lock = threading.Lock()
        self.socket_reference_count = 0

    def __del__(self):
        self._close_socket()

    def increase_socket_reference_count(self):
        self.socket_reference_count += 1

    def decrease_socket_reference_count(self):
        self.socket_reference_count -= 1

    def connect(self, host, port):
        self.server_socket.connect((host, port))
        return self.server_socket

    def prepare_net(self):
        while not self.net_ready:
            data = self.server_socket.recv(data_size)
            print(data.decode("utf-8"))
            if data.decode("utf-8") == "OK":
                self.net_ready = True

    def add_send_data(self, data):
        self.send_queue.put(data)

    def get_rec_data(self):
        # self.rec_lock.acquire()
        if not self.rec_queue.empty():
            return self.rec_queue.get()
        # self.rec_lock.release()


def _close_socket(self):
    if self.socket_reference_count == 0:
        self.server_socket.close()
