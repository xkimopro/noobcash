from netifaces import interfaces, ifaddresses, AF_INET
import socket
import sys

def local_ip():    
    with socket.socket() as client_socket:
        for ifaceName in interfaces():
            for i in ifaddresses(ifaceName).setdefault(AF_INET, [{'addr':'No IP addr'}]):
                if i['addr'].startswith('192') or i['addr'].startswith('172') : return i['addr']
       
class Config:
    nodes = 5
    localnet = False
    block_capacity = 5
    noobcash_ports_range = [44440,44450]
    bootstrap_node_port = 44439
    bootstrap_node_host = '192.168.0.1'
    client_node_port = 44441
    client_node_host = local_ip()
    difficulty = 4
