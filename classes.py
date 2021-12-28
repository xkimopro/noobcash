import threading

from functions import *

class Node:
    def __init__(self, node_host, node_port, node_thread , payload_public_key=None):
        print("Incoming connection from  {}:{} , assigned thread #{}".format(node_host , node_port, node_thread)) 
        self.node_host = node_host
        self.node_port = node_port
        self.node_thread = node_thread
        self.public_key = publicKeyFromBytes(payload_public_key.encode('utf-8')) if payload_public_key is not None else None# Unicode -> Bytes and Bytes -> RSAPublicKey
        self.public_key_bytes = bytesFromPublicKeyObj(self.public_key) if payload_public_key is not None else None
        self.acknowledged = False
        self.received_nodes_list = False
        self.thread_id = threading.get_ident()

    def setAcknowledged(self,):
        self.acknowledged = True
    
    def setThreadId(self, ):
        self.thread_id = threading.get_ident()

    def setPublicKey(self,public_key): 
        self.public_key = publicKeyFromBytes(public_key.encode('utf-8'))
        self.public_key_bytes = public_key.encode('utf-8')

    def __str__(self) -> str:
        return f"{self.node_host} , {self.node_port} , {self.thread_id} , #{self.node_thread}, pub_key:{self.public_key} , Received node list {self.received_nodes_list}"
    
    def node_str(self) -> str:
        return f"{self.node_host} , {self.node_port} , {self.thread_id} , #{self.node_thread}, pub_key:{self.public_key} , Received node list {self.received_nodes_list}"



def convertToSend(client_list):
    dict_list = []
    for c in client_list: 
        t = {}
        t['node_host'] , t['node_port'] = c.node_host , c.node_port
        t['public_key_bytes'] ,t['node_thread'] = c.public_key_bytes.decode(), c.node_thread
        dict_list.append(t)
    return dict_list
          

