#!/usr/bin/python3

import socket , json, sys , os , select
from config import Config
import threading , time
from threading import Thread

from messaging import *
from classes import *
from functions import *




client_thread_count = 0
client_list = []
noobcash_phase = "entering"
client_threads_stop = False

config = Config('config.json')

my_key = generateInitialkey()
my_public_key = my_key.public_key()
my_public_key_bytes = publicKeyBytes(my_key)

def markClientAsAcknowledged():
    global  client_list
    my_thread_id = threading.get_ident()
    for index , c in enumerate(client_list):
        if c.thread_id == my_thread_id:  c.setAcknowledged()

def nodeReceivedList():
    global  client_list
    my_thread_id = threading.get_ident()
    for index , c in enumerate(client_list):
        if c.thread_id == my_thread_id:  
            c.received_nodes_list = True

def checkClientsForAcknowledgment():
    global  client_list, noobcash_phase
    for c in client_list:
        print(c)
        if not c.acknowledged: 
            client_threads_stop = True
            exitNoobcash(3, "Noobcash clients failed to acknowledge assignment phase")

    noobcash_phase = "broadcasting"
    inform("All clients have acknowledged assignment phase initiation")
    inform("No nodes should exit the blockchain from now on and then")
    inform("Starting broadcast")

def checkAllClientsReceivedList():
    global  client_list, noobcash_phase
    for c in client_list:
        if not c.received_nodes_list: 
            return

    inform("All clients received node list through broadcast")



def gracefulClientExit():
    global client_thread_count, client_list
    client_thread_count -= 1
    my_thread_id = threading.get_ident()
    for index , c in enumerate(client_list):
        if c.thread_id == my_thread_id:  client_list.pop(index)
    inform(f"Client with thread id {str(my_thread_id)} exited")
    

class BackgroundTasks(threading.Thread):
    def run(self,*args,**kwargs):
        while True:
            time.sleep(2)
            print("Nodes List")
            for c in client_list: print(c)
            print()

# Uncomment below to do start  background task thread
# t = BackgroundTasks()
# t.start()

class ThreadedClient(threading.Thread):

    def __init__(self, connection : socket , client_obj : Node):
        Thread.__init__(self)
        self._running = True
        self.connection = connection
        self.client_obj = client_obj
        self.messaging = Messaging(self.connection, my_key)

    def terminate(self):
        self._running = False

    def run(self, *args, **kwargs):

        connection = self.connection
        self.messaging.serverGreetingClient(my_public_key_bytes)
        self.client_obj.setThreadId()
        greeting_reply = connection.recv(2048)
        m = self.messaging.parseToMessage(greeting_reply)
        start_assignment_sent = False
        node_list_sent = False

        if m.isClientReplyToGreeting():
            inform(f"Noobcash client connected at {self.client_obj.node_host}:{self.client_obj.node_port} assigned thread_id {threading.get_ident()}")
            self.client_obj.setPublicKey(m.payload['public_key'])                
            while True:
                connection.setblocking(0)
                ready = select.select([connection], [], [], 1)
                
                if ready[0]:                        # Client node sent data
                    data = connection.recv(2048)
                    print(data)
                    if not data:  break # Connection stopped by client
                    m = self.messaging.parseToMessage(data)

                    if noobcash_phase == "assignment":
                        if m.isStartAssignmentPhaseAck():
                            inform(self.client_obj.node_str() + " acknowledged")
                            markClientAsAcknowledged()
                        else:
                            inform(self.client_obj.node_str() + " refused acknowledgement")
                            
                    elif noobcash_phase == "broadcasting":
                        if m.isSendNodesListAck() and m.isAuthenticated(self.client_obj.public_key): 
                            nodeReceivedList()     
                    else:
                        pass

                else:                           # No data from client node yet
                    if client_threads_stop: break

                    if noobcash_phase == "broadcasting":
                        if not node_list_sent: 
                            dict_list = convertToSend(client_list)
                            self.messaging.sendNodesList(dict_list)
                            node_list_sent = True
                        else:
                            self.messaging.sendBlockchainStarted()
                            time.sleep(0.5) 
                            continue

                    if noobcash_phase == "assignment" and not start_assignment_sent: 
                        self.messaging.startAssignmentPhase(config)
                        start_assignment_sent = True    
        else:
            inform(f"Non noobcash client tried to connect")
            
        gracefulClientExit()
        connection.close()



with socket.socket() as server_socket:
    server_host , server_port = config.bootstrap_node_ip , config.bootstrap_node_port
    try:
        server_socket.bind((server_host, server_port))
    except socket.error as e:
        print(str(e))
        os.execv("./noobcash_client.py", sys.argv)

    boldInform(f"Noobcash bootstrap node started at {config.bootstrap_node_ip}:{config.bootstrap_node_port}")
    boldInform("Waitiing for a Connection....")
    server_socket.listen(5)

    while True:
        if noobcash_phase == "entering":
            client_conn, address = server_socket.accept()
            client_thread_count += 1
            client_obj = Node(address[0] , address[1], client_thread_count )
            client_list.append(client_obj)
            new_t = ThreadedClient(client_conn, client_obj)
            new_t.start()
            if (client_thread_count == config.nodes - 1):   # Subtract 1 for bootstrap node
                time.sleep(0.4)
                print("Initiating assignment phase...")
                noobcash_phase = "assignment"
        elif noobcash_phase == "broadcasting":
            time.sleep(1)
            checkAllClientsReceivedList()
        else:
            time.sleep(1)
            checkClientsForAcknowledgment()




