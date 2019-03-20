import socket
import threading

data_size = 1024


class ServerNode:

    def __init__(self, host, ip_port):
        '''

        :param host: 用于和一个work通信的端口
        :param ip_port: work的IP地址
        '''
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 用于通信的socket
        self.server_socket.bind((host, ip_port))
        self.ready_state = False  # 网络连接状态
        self.__socket_reference_count = 0  # socket会在多个线程中被使用，引用次数，在析构过程中，引用次数为0，便可以直接删除
        self.thread_list = []
        self.client = None

    def __del__(self):
        self.__close_socket()

    def __close_socket(self):
        if self.__socket_reference_count == 0:
            self.server_socket.close()

    def set_thread_list(self, thread_list):
        self.thread_list = thread_list

    def increase_reference_count(self):
        self.__socket_reference_count += 1

    def decrease_reference_count(self):
        self.__socket_reference_count -= 1

    def create_conn(self):
        self.server_socket.listen(5)
        while not self.ready_state:
            self.client, addr = self.server_socket.accept()
            print('client address', addr)
            self.ready_state = True

    def start_send_loss(self):
        self.client.send("OK".encode('utf-8'))

    def rec_data(self, rec_q, rec_lock):
        if self.ready_state:
            data = self.client.recv(data_size)
            if data:
                p = data.decode("utf-8")
                print("接收数据", p)
                rec_lock.acquire()
                rec_q.put(float(p))
                rec_lock.release()

    def send_data(self, send_q, send_lock):
        if self.ready_state:
            send_lock.acquire()
            if not send_q.empty():
                loss = send_q.get()
                print("发送", loss, len(str(loss).encode("utf-8")))
                self.client.send(str(loss).encode("utf-8"))
            send_lock.release()


class ServerRecBaseThread(threading.Thread):
    server_obj: ServerNode

    def __init__(self, thread_id, thread_name, server_obj, rec_q, rec_lock):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.thread_name = thread_name
        self.server_obj = server_obj
        self.rec_q = rec_q
        self.rec_lock = rec_lock
        self.server_obj.increase_reference_count()
        print("开启" + self.thread_name)

    def __del__(self):
        self.server_obj.decrease_reference_count()

    def run(self):
        while True:
            self.rec_data()

    def rec_data(self):
        if self.server_obj.ready_state:
            data = self.server_obj.client.recv(data_size)
            if data:
                p = data.decode("utf-8")
                print("接收数据", p)
                self.rec_lock.acquire()
                self.rec_q.put(float(p))
                self.rec_lock.release()


class ServerSendBaseThread(threading.Thread):
    server_obj: ServerNode

    def __init__(self, thread_id, thread_name, server_obj, send_q, send_lock):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.thread_name = thread_name
        self.server_obj = server_obj
        self.send_q = send_q
        self.send_lock = send_lock
        self.server_obj.increase_reference_count()
        print("开启" + self.thread_name)

    def __del__(self):
        self.server_obj.decrease_reference_count()

    def run(self):
        while True:
            self.send_data()

    def send_data(self):
        if self.server_obj.ready_state:
            self.send_lock.acquire()
            if not self.send_q.empty():
                loss = self.send_q.get()
                print("send:", loss, len(str(loss).encode("utf-8")))
                self.server_obj.client.send(str(loss).encode("utf-8"))
            self.send_lock.release()
