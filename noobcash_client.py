#!/usr/bin/python3

import socket , json , os , time
from functions import *
from config import Config
from _thread import *

from messaging import *
from classes import *
    

config = Config('config.json')
my_key = generateInitialkey()
my_public_key = my_key.public_key()
my_public_key_bytes = publicKeyBytes(my_key)
nodes_list = []
client_phase = "entering"

# class BackgroundTasks(threading.Thread):
#     def run(self,*args,**kwargs):
#         while True:
#             time.sleep(2)
#             print("Nodes List")
#             for c in nodes_list: print(c)
#             print()


# t = BackgroundTasks()
# t.start ()


def nodeIsMe(node_public_key):
    global my_public_key_bytes
    return my_public_key_bytes.decode('utf-8') == node_public_key 


def addNodesToNodeList(incoming_nodes):
    global nodes_list
    for i in incoming_nodes:
        node_host , node_port = i['node_host'] , i['node_port']
        public_key_bytes, node_thread = i['public_key_bytes'] , i['node_thread']
        if nodeIsMe(public_key_bytes): continue # Discard yourself from node list
        new_node = Node(node_host,node_port,node_thread,public_key_bytes)            
        nodes_list.append(new_node)


with socket.socket() as client_socket: 
    attemptBootstrapConnection(client_socket, config)
    greeting = client_socket.recv(2048)
    messaging = Messaging(client_socket)
    m = messaging.parseToMessage(greeting)    
    if m.isServerGreetingClient():
        inform("Greeted by bootstrap node. Replying...")
        messaging.clientReplyToGreeting(my_public_key_bytes)
    else: exitNoobcash(2,"There is no bootstrap node on the other end of the socket")    
    
    inform("Waiting for assignment phase. Waiting for bootstrap to share credentials...")
    
    bootstrap_node = Node(config.bootstrap_node_ip , config.bootstrap_node_port, 0 , m.payload['public_key'])
    nodes_list.append(bootstrap_node)
    


    while True:
        response = client_socket.recv(2048)
        print(response)
        m = messaging.parseToMessage(response)
        if client_phase == "entering":
            if m.isStartAssignmentPhase():
                inform("Bootstrap node initiated assignment phase")
                bootstrap_nodes = m.payload['nodes']  
                if bootstrap_nodes != config.nodes:
                    exitNoobcash(4, "Number of nodes dont match between client and bootstrap node")

                messaging.startAssignmentPhaseAck()
                config.client_node_ip , config.client_node_port = client_socket.getsockname()
                
            if m.isSendNodesList():
                incoming_nodes = m.payload['nodes_list']
                addNodesToNodeList(incoming_nodes)
                messaging.sendNodesListAck()
                client_phase = "blockchain"
        if client_phase == "blockchain":
            time.sleep(1.5)
            print("Blochchain phase")