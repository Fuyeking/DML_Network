import socket

data_size = 1024


class ServerNode:

    def __init__(self, host, ip_port):
        '''

        :param host: 用于和一个work通信的端口
        :param ip_port: work的IP地址
        '''
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 用于通信的socket
        self.server_socket.bind((host, ip_port))
        self.net_state = False  # 网络连接状态
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
        while not self.net_state:
            self.client, addr = self.server_socket.accept()
            print('client address', addr)
            self.net_state = True

    def start_send_loss(self):
        self.client.send("OK".encode('utf-8'))

    def run_thread(self):
        for i in range(len(self.thread_list)):
            self.thread_list[i].start()
