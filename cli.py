import sys

from config import Config


from messaging import *
from node import *    

from event_listener import EventListeningThread

config = Config()

help_message = '''
            
Available commands:
* "t [recepient_address] [amount]"                        Send `amount` NBC to `recepient` node
* "view"                                                  View transactions of the latest block
* "balance"                                               View balance of each wallet (last validated block)
* "help"                                                  Print this help message
* "exit"                                                  Exit client 
'''


PORT = config.cli_node_port
IP = config.cli_node_host
URL = 'http://' + str(IP) + ':' + str(PORT) + "/"


# if len(sys.argv) < 3 or len(sys.argv) > 3:
#     print("Invalid inputs! Please Type the command as: python cli.py <PORT> <IP>")
#     sys.exit(0)


with socket.socket() as cli_server_socket:
    try:
        cli_server_socket.bind((IP, PORT))
    except socket.error as e:
        exitNoobcash(1,"Cannot start noobcash as bootstrap node")  

    boldInform(f"Noobcash cli master node started at {IP}:{PORT}")
    messaging = Messaging(None,)
    cli_server_socket.listen(5)

    for i in range(10):
        client_conn, address = cli_server_socket.accept()
        client_init = client_conn.recv(8192)
        if len(client_init) != 0:
            client_init_msg = messaging.parseToMessage(client_init)  
            id , host, port = client_init_msg.parseCliInitMessage()
            print("id:",id, " host:", host, " port:", port)
        else:
            print(client_init)
    #     bootstrap_node.register_node_to_ring(client_conn, public_key_bytes, host, port)
        
    # bootstrap_node.broadcast_ring()

    # # Close Temp Connections
    # bootstrap_node.close_client_temp_connections()

    # # Start Event Listening Thread
    # event_listening_thread = EventListeningThread(bootstrap_node, server_socket)
    # event_listening_thread.start()
    
    
    time.sleep(1)

print("====================")
print(" WELCOME TO NOOBCASH")
print("====================")

while (1):
    print("Enter an action! Type help for more specific info")
    choice = input()

    # Transaction
    if choice.startswith('t'):
        print("hello1")

    # View last transaction
    elif choice == 'view':
        print("hello2")
    # Balance
    elif choice == 'balance':
        print("hello3")

    # Help
    elif choice == 'help':
        print(help_message)

    elif (choice == 'exit'):
        sys.exit(0)

    else:
        print("Invalid action")
