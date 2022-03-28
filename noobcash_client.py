#!/usr/bin/python3

import socket , json , os , time,sys
from functions import *
from config import Config


from messaging import *
from node import *    

from event_listener import EventListeningThread

config = Config()

config.client_node_port = int(sys.argv[1])
config.cli_client_node_port = int(sys.argv[2])

# config.client_node_host = socket.gethostbyname(socket.gethostname())
config.client_node_host = '127.0.0.1'

# Send credentials 
with socket.socket() as client_socket: 
    client_node = Node(False, config)
    # 1) to bootstrap
    attemptBootstrapConnection(client_socket, config)
    client_node.messaging = Messaging(client_socket,client_node.wallet.key)
    m = client_node.messaging.clientInitMessage(client_node.wallet.public_key_bytes,client_node.wallet.host, client_node.wallet.port)    
    inform("Send my credentials to bootstrap")
    m = client_node.messaging.parseToMessage(client_socket.recv(8192))
    ring = json.loads(m.parseBootstrapSendRing())
    client_node.parse_ring(ring)

    # 2) to cli
    attemptCliConnection(client_socket, config)
    m = client_node.messaging.cliInitMessage(client_node.id,config.cli_client_node_host, config.cli_client_node_port)
    inform("Send my credentials to cli")
  
    
# Initiate your socket to connect to bootstrap   
with socket.socket() as server_socket:
    try:
        server_socket.bind((config.client_node_host, config.client_node_port))
    except socket.error as e:
        exitNoobcash(1,"Client cannot start its socket server at specified port")  
    
    server_socket.listen(5)
    
    # Start Event Listening Thread
    event_listening_thread = EventListeningThread(client_node, server_socket)
    event_listening_thread.start()
    
    if True:
        # Initiate your socket to connect to cli 

        time.sleep(1)
        # Initiate your socket to connect to cli 
        with socket.socket() as cli_server_socket:
            try:
                cli_server_socket.bind((config.cli_client_node_host, config.cli_client_node_port))
            except socket.error as e:
                exitNoobcash(1,"Cli Client cannot start its socket server at specified port")  
            
            cli_server_socket.listen(5)
            
            # # Start Event Listening Thread
            # cli_event_listening_thread = EventListeningThread(client_node, cli_server_socket)
            # cli_event_listening_thread.start()

            while True:
                time.sleep(1)




