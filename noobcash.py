#!/usr/bin/python3

import socket , json, sys
from functions import *
from config import Config
import os
from _thread import *
import threading , time
from threading import Thread




class BackgroundTasks(threading.Thread):
    def run(self,*args,**kwargs):
        while True:
            print(threading.enumerate())
            time.sleep(1)


# Background job
t = BackgroundTasks()
t.start()



class ThreadedClient(threading.Thread):

    def __init__(self, client_conn, client_obj):
        Thread.__init__(self)

    def run(*args, **kwargs):
        while True:
            print("I am thread" + str(get_ident()))
            time.sleep(1)



config = Config('config.json')
client_list = []



class Client:
    def __init__(self, client_host, client_port, client_thread):
        print("New client connected from:  {}:{} , assigned thread #{}".format(client_host , client_port, client_thread)) 
        self.client_host = client_host
        self.client_port = client_port
        self.client_thread = client_thread





def threaded_client(connection, client_obj):
    connection.send(str.encode('Welcome to the Server'  ))
    while True:
        data = connection.recv(2048)
        reply = 'Server Says: ' + data.decode('utf-8')
        if not data: break
        connection.sendall(str.encode(reply))
    connection.close()


with socket.socket() as server_socket:
    server_host = config.bootstrap_node_ip
    server_port = config.bootstrap_node_port
    ThreadCount = 0
    try:
        server_socket.bind((server_host, server_port))
    except socket.error as e:
        print(str(e))
        os.execv("./noobcash_client.py", sys.argv)

    print('Waitiing for a Connection..')
    server_socket.listen(5)

    while True:
        
        client_conn, address = server_socket.accept()
        ThreadCount += 1
        client_obj = Client(address[0] , address[1], ThreadCount)
        client_list.append(client_obj)
        new_t = ThreadedClient(client_conn, client_obj)
        new_t.start()
        # start_new_thread(threaded_client, (client_conn, client_obj ,  ))

