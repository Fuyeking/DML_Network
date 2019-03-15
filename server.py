import threading
import queue
import socket

data_size = 1024


class ServerNode:

    def __init__(self, host, ip_port):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, ip_port))
        self.ready_state = False
        self.socket_reference_count = 0

    def __del__(self):
        self.__close_socket__()

    def __close_socket__(self):
        if self.socket_reference_count == 0:
            self.server_socket.close()

    def create_conn(self):
        self.server_socket.listen(5)
        while not self.ready_state:
            self.client, addr = self.server_socket.accept()
            print('client address', addr)
            self.client.send("OK".encode('utf-8'))
            self.ready_state = True

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
        print("开启" + self.thread_name)

    def run(self):
        while True:
            self.server_obj.rec_data(self.rec_q, self.rec_lock)


class ServerSendThread(threading.Thread):
    server_obj: ServerNode

    def __init__(self, thread_id, thread_name, server_obj, send_q, send_lock):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.thread_name = thread_name
        self.server_obj = server_obj
        self.send_q = send_q
        self.send_lock = send_lock
        print("开启" + self.thread_name)

    def run(self):
        while True:
            self.server_obj.send_data(self.send_q, self.send_lock)


class CalcAverageLoss(threading.Thread):
    def __init__(self, thread_id, thread_name, send_q, rec_q,rec_lock):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.thread_name = thread_name
        self.send_data = send_q
        self.rec_data = rec_q
        self.rec_lock = rec_lock
        print("开启" + self.thread_name)

    def run(self):

        while True:
            self.rec_lock.acquire()
            if not rec_data.empty():
                data = rec_data.get()
                print("收到的梯度", data)
                self.send_data.put(10/40.0)
            self.rec_lock.release()


ip_set = {12345: "127.0.0.1"}

for key, value in ip_set.items():
    rec_queue_lock = threading.Lock()
    send_queue_lock = threading.Lock()
    rec_data = queue.Queue()
    send_data = queue.Queue()
    server = ServerNode(value, key)
    server.create_conn()

    rec_thread = ServerRecThread(1, "服务端接受线程", server, rec_data, rec_queue_lock)
    rec_thread.start()
    calcLoss = CalcAverageLoss(3, "计算平均梯度", send_data, rec_data, rec_queue_lock)
    calcLoss.start()
    send_thread = ServerSendThread(2, "服务端发送线程", server, send_data, send_queue_lock)
    send_thread.start()
