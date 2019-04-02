from dml import parameter_node as pn
from app import dnn_app as da

def main():
    ip_sets = {12345: "127.0.0.1", 12346: "127.0.0.1"}
    parameter_node = pn.ParameterServer(ip_sets, 2)
    thread = da.LossAverageThread("Loss计算平均梯度线程")
    parameter_node.distributed_dnn(thread)


if __name__ == '__main__':
    main()
