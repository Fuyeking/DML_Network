# DML_Network
一、构建分布式深度学习的网络模块
1. 集中式（参数服务器-Work模式）

    1.1 参数平均
    
    参数服务器收集各个计算机节点算出的梯度，计算均值，然后通过TCP/IP网络返回计算机节点。
    
    基于数据并行的原理，实现训练的加速
    
    参数服务器（parameter_node）包含多个server_node,每一个server_node负责和一个client_node（负责发送work节点的梯度到参数服务器）通信
    
    parameter_simulator.py:模拟参数服务器
    
    work_simulator*.py:模拟计算节点
  
