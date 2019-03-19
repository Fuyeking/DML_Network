import threading
import queue
from dn import server_node as sn


class CalcAverageLoss(threading.Thread):
    rec_lock_list: dict
    rec_data_list: dict
    send_data_list: dict

    def __init__(self, thread_id, thread_name, ip_set, send_list, rec_list, rec_lock_list):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.thread_name = thread_name
        self.send_data_list = send_list
        self.rec_data_list = rec_list
        self.rec_lock_list = rec_lock_list
        self.ip_set = ip_set
        print("开启" + self.thread_name)

    def run(self):
        while True:
            while self._check_rec_list():
                send_loss = self._calc_average_loss()
                self._send_new_loss(send_loss)

    def _check_rec_list(self):
        for port, ip in self.ip_set.items():
            if self.rec_data_list[port].empty():
                return False
        return True

    def _calc_average_loss(self):
        sum_loss = 0
        for port, ip in self.ip_set.items():
            self.rec_lock_list[port].acquire()
            if not self.rec_data_list[port].empty():
                sum_loss += self.rec_data_list[port].get()
            self.rec_lock_list[port].release()
            print("梯度总和：", sum_loss)
        average_loss = sum_loss / len(self.ip_set)
        return average_loss

    def _send_new_loss(self, new_loss):
        for port, ip in self.ip_set.items():
            self.send_data_list[port].put(new_loss)


class ParameterServer:
    calc_loss_thread: threading.Thread

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
        self.calc_loss_thread = None

    def distributed_dnn(self):
        self._create_server_nodes()  # 根据计算节点的个数创建对应的通信节点
        self._init_socket_conn()  # 和计算节点建立连接
        self._create_threads()  # 每个通信节点创建两个进程（负责收、发）
        self._start_threads()  # 开启进程
        self._notify_clients()  # 通知所有的计算节点可以开始发送数据
        self._start_calc_loss_thread()  # 开启计算平均梯度的线程

    def _create_server_nodes(self):
        for port, ip in self.ip_set.items():
            server = sn.ServerNode(ip, port)
            self.server_nodes[port] = server

    def _start_send_loss(self):
        self.calc_loss_thread.start()

    def _init_socket_conn(self):
        for port, ip in self.ip_set.items():
            node: sn.ServerNode = self.server_nodes[port]
            while not node.ready_state:
                node.create_conn()

    def _notify_clients(self):
        for port, ip in self.ip_set.items():
            node: sn.ServerNode = self.server_nodes[port]
            node.start_send_loss()

    def _create_threads(self):
        for port, ip in self.ip_set.items():
            rec_queue_lock = threading.Lock()
            self.rec_locks[port] = rec_queue_lock
            send_queue_lock = threading.Lock()
            self.rec_locks[port] = send_queue_lock
            rec_data = queue.Queue()
            self.rec_queues[port] = rec_data
            send_data = queue.Queue()
            self.send_queues[port] = send_data
            thread_list = []
            rec_thread = sn.ServerRecThread(1, "服务端接受线程", self.server_nodes[port], rec_data, rec_queue_lock)
            thread_list.append(rec_thread)
            send_thread = sn.ServerSendThread(2, "服务端发送线程", self.server_nodes[port], send_data, send_queue_lock)
            thread_list.append(send_thread)
            self.server_nodes[port].set_thread_list(thread_list)
        self.calc_loss_thread = CalcAverageLoss(3, "参数服务器计算平均梯度", self.ip_set, self.send_queues, self.rec_queues,
                                                self.rec_locks)

    def _start_threads(self):
        for port, ip in self.ip_set.items():
            thread_list = self.server_nodes[port].thread_list
            for i in range(len(thread_list)):
                thread_list[i].start()

    def _start_calc_loss_thread(self):
        self.calc_loss_thread.start()
