#!/usr/bin/python3

from re import I, T
import socket , json, sys , os , select
from threading import Thread
import time

from messaging import *
from functions import *
from config import Config
from node import *

from event_listener import EventListeningThread


config = Config()


with socket.socket() as server_socket:
    try:
        server_socket.bind((config.bootstrap_node_host, config.bootstrap_node_port))
    except socket.error as e:
        exitNoobcash(1,"Cannot start noobcash as bootstrap node")  

    boldInform(f"Noobcash bootstrap node started at {config.bootstrap_node_host}:{config.bootstrap_node_port}")
    bootstrap_node = Node(True, config)
    bootstrap_node.messaging = Messaging(None, bootstrap_node.wallet.key)
    server_socket.listen(5)

    # 2) to cli
    attemptCliConnection(bootstrap_node, config)
    m = bootstrap_node.messaging.cliInitMessage(bootstrap_node.id,config.cli_client_node_host, config.cli_client_node_port)
    inform("Send my credentials to cli")

    for i in range(config.nodes - 1):
        client_conn, address = server_socket.accept()
        client_init = client_conn.recv(8192)
        client_init_msg = bootstrap_node.messaging.parseToMessage(client_init)    
        public_key_bytes , host, port = client_init_msg.parseClientInitMessage()
        bootstrap_node.register_node_to_ring(client_conn, public_key_bytes, host, port)
        
    bootstrap_node.broadcast_ring()

    # Close Temp Connections
    bootstrap_node.close_client_temp_connections()

    # Start Event Listening Thread
    event_listening_thread = EventListeningThread(bootstrap_node, server_socket)
    event_listening_thread.start()
    
    
    time.sleep(1)
    
    
    bootstrap_node.create_and_broadcast_genesis_block()
    for i in range(config.nodes - 1):
        initial_client_transaction = bootstrap_node.create_transaction(i+1,100)

    while True:
        # Initiate your socket to connect to cli 
        with socket.socket() as cli_server_socket:
            try:
                cli_server_socket.bind((config.cli_client_node_host, config.cli_client_node_port))
            except socket.error as e:
                exitNoobcash(1,"Cli Client cannot start its socket server at specified port")  
            
            cli_server_socket.listen(5)
            
            # # Start Event Listening Thread
            # cli_event_listening_thread = EventListeningThread(bootstrap_node, cli_server_socket)
            # cli_event_listening_thread.start()

            while True:
                time.sleep(1)
        
    
    
    