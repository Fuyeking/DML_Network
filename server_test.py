from dn import parameter_node as pn


def main():
    ip_sets = {12345: "127.0.0.1", 12346: "127.0.0.1", 12347: "127.0.0.1"}
    parameter_node = pn.ParameterServer(ip_sets, 1)
    parameter_node.distributed_dnn()


if __name__ == '__main__':
    main()
