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
from benchmark import Benchmark


config = Config()
    
clear_my_log_file()
    

with socket.socket() as server_socket:
    try:
        server_socket.bind((config.bootstrap_node_host, config.bootstrap_node_port))
    except socket.error as e:
        exitNoobcash(1,"Cannot start noobcash as bootstrap node")  
    print("Noobcash bootstrap node started at ", config.bootstrap_node_host,":",config.bootstrap_node_port)

    bootstrap_node = Node(True, config)
    bootstrap_node.messaging = Messaging(None, bootstrap_node.wallet.key)
    server_socket.listen(5)

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
    start_time = time.time()
    event_listening_thread = EventListeningThread(bootstrap_node, server_socket)
    event_listening_thread.start()
    
    time.sleep(1)
    
    
    bootstrap_node.create_and_broadcast_genesis_block()
    for i in range(config.nodes - 1):
        bootstrap_node.mutex.acquire()
        initial_client_transaction = bootstrap_node.create_transaction(i+1,100)
    
    
    time.sleep(1)
    
    benchmark = Benchmark(bootstrap_node,start_time)
    benchmark.start()

    while True:
        time.sleep(1)
    
    
        # help_message = '''
            
        # Available commands:
        # * "t [recepient_address] [amount]"                        Send `amount` NBC to `recepient` node
        # * "view"                                                  View transactions of the latest block
        # * "balance"                                               View balance of each wallet (last validated block)
        # * "help"                                                  Print this help message
        # * "file"                                                  Read from file transactions
        # * "exit" 
        #                                                           Exit client 
        # '''

        # print("====================")
        # print(" WELCOME TO NOOBCASH")
        # print("====================")

        # while (1):
        #     print("Enter an action! Type help for more specific info")
        #     choice = input()

        #     # Transaction
        #     # t receiver amount
        #     if choice.startswith('t'):
        #         # client_node.create_transaction(receiver_id, amount)
        #         pass

        #     # View last transaction
        #     elif choice == 'view':
        #         print(client_node.view_transactions())

        #     # Balance
        #     elif choice == 'balance':
        #         balance = 0
        #         for utxo in client_node.utxos[client_node.id]:
        #             balance += utxo['amount']
        #         print("My balance is: ", balance)

        #     # Help
        #     elif choice == 'help':
        #         print(help_message)

        #     # elif choice == file:
        #     #     blabla

        #     elif (choice == 'exit'):
        #         sys.exit(0)

        #     else:
        #         print("Invalid action")


