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
        self.thread_list = []
        self.client = None

    def __del__(self):
        self.__close_socket__()

    def set_thread_list(self, thread_list):
        self.thread_list = thread_list

    def __close_socket__(self):
        if self.socket_reference_count == 0:
            self.server_socket.close()

    def increase_reference_count(self):
        self.socket_reference_count += 1

    def decrease_reference_count(self):
        self.socket_reference_count -= 1

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


class CalcAverageLoss(threading.Thread):
    def __init__(self, thread_id, thread_name, send_q, rec_q, rec_lock):
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
            if not self.rec_data.empty():
                data = self.rec_data.get()
                print("收到的梯度", data)
                self.send_data.put(10 / 40.0)
            self.rec_lock.release()


class ParameterServer:
    def __init__(self, ip_set, num):
        """

        :type ip_set: dict
        """
        self.ip_set = ip_set
        self.clients_num = num
        self.send_locks = {}
        self.rec_locks = {}
        self.rec_queues = {}
        self.send_queues = {}
        self.server_nodes = {}

    def distributed_dnn(self):
        self._create_server_nodes()
        self._init_socket_conn()
        self._create_threads()
        self._start_threads()
        self._start_send_loss()

    def _create_server_nodes(self):
        for port, ip in self.ip_set.items():
            server = ServerNode(ip, port)
            self.server_nodes[port] = server

    def _init_socket_conn(self):
        for port, ip in self.ip_set.items():
            node: ServerNode = self.server_nodes[port]
            while not node.ready_state:
                node.create_conn()

    def _start_send_loss(self):
        for port, ip in self.ip_set.items():
            node: ServerNode = self.server_nodes[port]
            node.start_send_loss()

    def _create_threads(self):
        for port, ip in self.ip_set.items():
            rec_queue_lock = threading.Lock()
            thread_list = []
            send_queue_lock = threading.Lock()
            rec_data = queue.Queue()
            send_data = queue.Queue()
            rec_thread = ServerRecThread(1, "服务端接受线程", self.server_nodes[port], rec_data, rec_queue_lock)
            thread_list.append(rec_thread)
            calc_loss = CalcAverageLoss(3, "计算平均梯度", send_data, rec_data, rec_queue_lock)
            thread_list.append(calc_loss)
            send_thread = ServerSendThread(2, "服务端发送线程", self.server_nodes[port], send_data, send_queue_lock)
            thread_list.append(send_thread)
            self.server_nodes[port].set_thread_list(thread_list)

    def _start_threads(self):
        for port, ip in self.ip_set.items():
            thread_list = self.server_nodes[port].thread_list
            for i in range(len(thread_list)):
                thread_list[i].start()


def main():
    ip_sets = {12345: "127.0.0.1", 12346: "127.0.0.1"}
    parameter_node = ParameterServer(ip_sets, 1)
    parameter_node.distributed_dnn()


if __name__ == '__main__':
    main()
