#!/usr/bin/python3

import socket , json , os , time,sys
from functions import *
from config import Config

from messaging import *
from node import *    

from event_listener import EventListeningThread

config = Config()
 
config.client_node_port = int(sys.argv[1]) 

# Send credentials to bootstrap
with socket.socket() as client_socket:
    client_node = Node(False, config)
    attemptBootstrapConnection(client_socket, config)
    client_node.messaging = Messaging(client_socket,client_node.wallet.key)
    client_node.messaging.clientInitMessage(client_node.wallet.public_key_bytes,client_node.wallet.host, client_node.wallet.port)    
    inform("Send my credentials to bootstrap")
    m = client_node.messaging.parseToMessage(client_socket.recv(8192))
    ring = json.loads(m.parseBootstrapSendRing())
    client_node.parse_ring(ring)
  
    
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
    
    while True:
        time.sleep(1)
        # help_message = '''
            
        # Available commands:
        # * "t [recepient_address] [amount]"                        Send `amount` NBC to `recepient` node
        # * "view"                                                  View transactions of the latest block
        # * "balance"                                               View balance of each wallet (last validated block)
        # * "help"                                                  Print this help message
        # * "exit"                                                  Exit client 
        # '''

        # print("====================")
        # print(" WELCOME TO NOOBCASH")
        # print("====================")

        # while (1):
        #     print("Enter an action! Type help for more specific info")
        #     choice = input()

        #     # Transaction
        #     if choice.startswith('t'):
        #         print("hello1")

        #     # View last transaction
        #     elif choice == 'view':
        #         print("hello2")
        #     # Balance
        #     elif choice == 'balance':
        #         print("hello3")

        #     # Help
        #     elif choice == 'help':
        #         print(help_message)

        #     elif (choice == 'exit'):
        #         sys.exit(0)

        #     else:
        #         print("Invalid action")


