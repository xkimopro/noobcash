#!/usr/bin/python3

import socket , json, sys , os , select
from functions import *
from config import Config
import threading , time
from threading import Thread
from messaging import *



client_thread_count = 0
client_list = []
noobcash_phase = "entering"
client_threads_stop = False

config = Config('config.json')


def markClientAsAcknowledged():
    global  client_list
    my_thread_id = threading.get_ident()
    for index , c in enumerate(client_list):
        if c.thread_id == my_thread_id:  c.setAcknowledged()


def checkClientsForAcknowledgment():
    global  client_list
    print("CHECKING")
    for c in client_list:
        print(c)
        if not c.acknowledged: 
            client_threads_stop = True
            exitNoobcash(3, "Noobcash clients failed to acknowledge their credentials during assignment phase")

    noobcash_phase = "completed"
    inform("All clients have acknowledged their credentials")
    inform("No nodes should exit the blockchain from now on and then")
    




def gracefulClientExit():
    global client_thread_count, client_list
    client_thread_count -= 1
    my_thread_id = threading.get_ident()
    for index , c in enumerate(client_list):
        if c.thread_id == my_thread_id:  client_list.pop(index)



class Client:
    def __init__(self, client_host, client_port, client_thread):
        print("Incoming connection from  {}:{} , assigned thread #{}".format(client_host , client_port, client_thread)) 
        self.client_host = client_host
        self.client_port = client_port
        self.client_thread = client_thread
        self.acknowledged = False

    def setAcknowledged(self,):
        self.acknowledged = True

    def setThreadId(self, ):
        self.thread_id = threading.get_ident()

    def __str__(self) -> str:
        return f"{self.client_host} , {self.client_port} , {self.thread_id} , #{self.client_thread}"
    
    def client_str(self) -> str:
        return f"{self.client_host} , {self.client_port} , {self.thread_id} , #{self.client_thread}"
        




class BackgroundTasks(threading.Thread):
    def run(self,*args,**kwargs):
        while True:
            time.sleep(2)
            print("Client List")
            for c in client_list: print(c)
            print()
            #Do something every X seconds as a background task
            print("Active Threads")
            for t in threading.enumerate(): print(t)
            print()



# Uncomment below to do start  background task thread
# t = BackgroundTasks()
# t.start()



class ThreadedClient(threading.Thread):

    def __init__(self, connection : socket , client_obj : Client):
        Thread.__init__(self)
        self._running = True
        self.connection = connection
        self.client_obj = client_obj
        self.messaging = Messaging(self.connection)


    def terminate(self):
        self._running = False

    def run(self, *args, **kwargs):

        connection = self.connection
        self.messaging.serverGreetingClient()
        self.client_obj.setThreadId()
        greeting_reply = connection.recv(2048)
        m = self.messaging.parseToMessage(greeting_reply)
        start_assignment_sent = False

        if m.isClientReplyToGreeting():
            inform(f"Noobcash client connected at {self.client_obj.client_host}:{self.client_obj.client_port} assigned thread_id {threading.get_ident()}")
            while True:
                
                connection.setblocking(0)
                ready = select.select([connection], [], [], 1)
                if ready[0]:
                    data = connection.recv(2048)
                    if not data:  break # Connection stopped by client
                    if noobcash_phase == "assignment":
                        m = self.messaging.parseToMessage(data)
                        if m.isStartAssignmentPhaseAck():
                            inform(self.client_obj.client_str() + " acknowledged")
                            markClientAsAcknowledged()
                        else:
                            inform(self.client_obj.client_str() + " refused acknowledgement")
                            
                    else:
                        reply = 'Server Says: ' + data.decode('utf-8')      
                        connection.sendall(str.encode(reply))
                else:
                    if client_threads_stop: break

                    if noobcash_phase == "assignment" and not start_assignment_sent: 
                        self.messaging.startAssignmentPhase()
                        start_assignment_sent = True
                        

                        
                
                
        else:
            inform(f"Non noobcash client tried to connect")
            
            
        gracefulClientExit()
        connection.close()






with socket.socket() as server_socket:
    server_host = config.bootstrap_node_ip
    server_port = config.bootstrap_node_port
    
    
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
            client_obj = Client(address[0] , address[1], client_thread_count )
            client_list.append(client_obj)
            new_t = ThreadedClient(client_conn, client_obj)
            new_t.start()
            if (client_thread_count == config.nodes - 1):   # Subtract 1 for bootstrap node
                time.sleep(0.4)
                print("Initiating assignment phase...")
                noobcash_phase = "assignment"
        else:
            time.sleep(2.5)
            checkClientsForAcknowledgment()



