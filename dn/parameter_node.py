import queue
import threading

from dn import server_node as sn


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
            while not node.net_state:
                node.create_conn()

    def _notify_clients(self):
        for port, ip in self.ip_set.items():
            node: sn.ServerNode = self.server_nodes[port]
            node.start_send_loss()

    def _create_threads(self):
        '''
        针对每个客户节点创建对应的服务节点
        :return:
        '''
        for port, ip in self.ip_set.items():
            # 接收队列的锁
            rec_queue_lock = threading.Lock()
            self.rec_locks[port] = rec_queue_lock
            # 发送队列的锁
            send_queue_lock = threading.Lock()
            self.rec_locks[port] = send_queue_lock
            # 接收队列，每个work对应一个接收队列
            rec_data = queue.Queue()
            self.rec_queues[port] = rec_data
            # 发送队列，每个work对应一个发送队列
            send_data = queue.Queue()
            self.send_queues[port] = send_data
            # 创建收发线程
            thread_list = []
            rec_thread = sn.ServerRecBaseThread(1, "服务端接受线程", self.server_nodes[port], rec_data, rec_queue_lock)
            thread_list.append(rec_thread)
            send_thread = sn.ServerSendBaseThread(2, "服务端发送线程", self.server_nodes[port], send_data, send_queue_lock)
            thread_list.append(send_thread)
            self.server_nodes[port].set_thread_list(thread_list)

        # 每个参数节点创建一个负责计算平均梯度的线程
        self.calc_loss_thread = CalcAverageLoss(3, "计算平均梯度线程", self.ip_set, self.send_queues, self.rec_queues,
                                                self.rec_locks)

    def _start_threads(self):
        for port, ip in self.ip_set.items():
            server_node: sn.ServerNode = self.server_nodes[port]
            server_node.run_thread()

    def _start_calc_loss_thread(self):
        self.calc_loss_thread.start()


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
        print("start the thread:" + self.thread_name)

    def run(self):
        while True:
            while self._check_rec_list():  # 所有计算节点已经发送数据到参数节点
                send_loss = self._calc_average_loss()  # 计算均值
                self._send_new_loss(send_loss)  # 给所有计算节点发送新的loss

    def _check_rec_list(self):
        '''
        判断所有的接受队列是否为空，不为空返回True，发送数据。为空，返回False，不发送数据
        :return:
        '''
        for port, ip in self.ip_set.items():
            if self.rec_data_list[port].empty():
                return False
        return True

    def _calc_average_loss(self):
        sum_w = 0
        sum_b = 0
        for port, ip in self.ip_set.items():
            self.rec_lock_list[port].acquire()
            if not self.rec_data_list[port].empty():
                data = self.rec_data_list[port].get()
                if data is not None:
                    sum_w += data['w']
                    sum_b += data['b']
            self.rec_lock_list[port].release()

        average_loss = dict()
        average_loss['w'] = sum_w / 3
        average_loss['b'] = sum_b / 3
        print("new  loss：", average_loss)
        return average_loss

    def _send_new_loss(self, new_loss):
        for port, ip in self.ip_set.items():
            self.send_data_list[port].put(new_loss)
