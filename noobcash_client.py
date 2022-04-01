#!/usr/bin/python3

import socket , json , os , time,sys, time
from functions import *
from config import Config
from messaging import *
from node import *    
from event_listener import EventListeningThread
from cli_listener import CliListeningThread

from benchmark import Benchmark

config = Config()
 
config.client_node_port = int(sys.argv[1]) 

clear_my_log_file()


# Send credentials to bootstrap
with socket.socket() as client_socket:
    client_node = Node(False, config)
    attemptBootstrapConnection(client_socket, config)
    client_node.messaging = Messaging(client_socket,client_node.wallet.key)
    client_node.messaging.clientInitMessage(client_node.wallet.public_key_bytes,client_node.wallet.host, client_node.wallet.port)
    # time.sleep(8)    
    inform("Send my credentials to bootstrap")
    m = client_node.messaging.parseToMessage(client_socket.recv(8192000))
    ring = json.loads(m.parseBootstrapSendRing())
    client_node.parse_ring(ring)
  
    
# Initiate your socket to connect to bootstrap   
with socket.socket() as server_socket:
    try:
        server_socket.bind((config.client_node_host, config.client_node_port))
    except socket.error as e:
        exitNoobcash(1,"Client cannot start its socket server at specified port")  
    
    server_socket.listen(5)
    
    start_time = time.time()

    event_listening_thread = EventListeningThread(client_node, server_socket)
    event_listening_thread.start()
    
    time.sleep(5)
    
    # benchmark = Benchmark(client_node,start_time)
    # benchmark.start()

    cli_listening_thread = CliListeningThread(client_node, server_socket)
    cli_listening_thread.start()

    while True:
        time.sleep(1)
