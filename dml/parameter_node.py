import queue
import threading

from dml import dml_base_thread as dbt
from dml import server_node as sn

module = __import__("dml.dml_base_thread")


class ParameterServer:
    calc_loss_thread: dbt.CalcAverageLoss

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
        self._init_send_rec_queues()  # 创建用于接受数据的队列
        self.create_send_rec_threads()  # 每个通信节点创建两个进程（负责收、发）
        self.create_avg_calc_thread()  # 创建参数服务器用于计算机平均梯度或者loss的线程
        self._start_send_rec_threads()  # 开启进程
        self._notify_clients()  # 通知所有的计算节点可以开始发送数据
        self._start_avg_calc_thread()  # 开启计算平均梯度的线程

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

    def _init_send_rec_queues(self):
        for port, ip in self.ip_set.items():
            # 接收队列的锁
            rec_queue_lock = threading.Lock()
            self.rec_locks[port] = rec_queue_lock
            # 发送队列的锁
            send_queue_lock = threading.Lock()
            self.send_locks[port] = send_queue_lock
            # 接收队列，每个work对应一个接收队列
            rec_data = queue.Queue()
            self.rec_queues[port] = rec_data
            # 发送队列，每个work对应一个发送队列
            send_data = queue.Queue()
            self.send_queues[port] = send_data

    # 允许被子类重载
    def create_send_rec_threads(self):
        '''
        针对每个客户节点创建对应的服务节点
        :return:
        '''
        for port, ip in self.ip_set.items():
            thread_list = []
            rec_thread = dbt.ServerRecBaseThread("服务端接受线程")
            rec_thread.init_para(self.server_nodes[port], self.rec_queues[port], self.rec_locks[port])
            thread_list.append(rec_thread)
            send_thread = dbt.ServerSendBaseThread("服务端发送线程")
            send_thread.init_para(self.server_nodes[port], self.send_queues[port], self.send_locks[port])
            thread_list.append(send_thread)
            self.server_nodes[port].set_thread_list(thread_list)

    # 允许被子类重载
    def create_avg_calc_thread(self):
        # 每个参数节点创建一个负责计算平均梯度的线程
        self.calc_loss_thread = dbt.CalcAverageLoss("计算平均梯度线程")
        self.calc_loss_thread.init_para(self.ip_set, self.send_queues, self.rec_queues, self.rec_locks,
                                        self.clients_num)

    def _start_send_rec_threads(self):
        for port, ip in self.ip_set.items():
            server_node: sn.ServerNode = self.server_nodes[port]
            server_node.run_thread()

    def _start_avg_calc_thread(self):
        self.calc_loss_thread.start()
