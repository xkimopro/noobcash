from threading import Thread
import traceback
import sys
# from functions import *
import fileinput




class CliListeningThread(Thread):
    
    def __init__(self, node ,  server_socket):
        Thread.__init__(self)
        self._running = True
        self.node = node
        self.server_socket = server_socket
        self.cached_messages = []

    def terminate(self):
        pass

    def run(self, *args, **kwargs):
        # choice = input()
        while True:

            help_message = '''
                
            Available commands:
            * "t [recepient_address] [amount]"                        Send amount NBC to recepient node
            * "view"                                                  View transactions of the latest block
            * "balance"                                               View balance of each wallet (last validated block)
            * "help"                                                  stdout_print this help message
            * "file"                                                  Read from file transactions
            * "exit" 
                                                                    Exit client 
            '''
            print("====================")
            print(" WELCOME TO NOOBCASH")
            print("====================")
            print("Enter an action! Type help for more specific info")
            while True:
                
                choice = input()
                # print(choice)
                if choice.startswith('t'):
                    info = choice.split()
                
                    self.node.mutex.acquire()
                    self.node.create_transaction(int(info[1]), int(info[2]))

                # View last transaction
                elif choice == 'view':
                    print(self.node.view_transactions())

                # Balance
                elif choice == 'balance':
                    balance = 0
                    for utxo in self.node.utxos[self.node.id]:
                        balance += utxo['amount']
                    print("My balance is: ", balance)

                # Help
                elif choice == 'help':
                    print(help_message)

                elif (choice == 'exit'):
                    sys.exit(0)

                else:
                    print("Invalid action")
                print("Enter an action! Type help for more specific info")
