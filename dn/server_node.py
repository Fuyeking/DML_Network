import threading
import socket

data_size = 1024


class ServerNode:

    def __init__(self, host, ip_port):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, ip_port))
        self.ready_state = False
        self.__socket_reference_count = 0
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


class ServerRecThread(threading.Thread):
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
            self.server_obj.rec_data(self.rec_q, self.rec_lock)


class ServerSendThread(threading.Thread):

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
            self.server_obj.send_data(self.send_q, self.send_lock)
