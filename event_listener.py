from threading import Thread
from messaging import *
from block import Block
from transaction import Transaction

class EventListeningThread(Thread):

    def __init__(self, node ,  server_socket):
        Thread.__init__(self)
        self._running = True
        self.node = node
        self.server_socket = server_socket

    def terminate(self):
        pass


    def run(self, *args, **kwargs):
        while True:     
            conn, _ = self.server_socket.accept()
            data = conn.recv(4096)
            
            m = self.node.messaging.parseToMessage(data)
            
            block = m.parseBroadcastBlock() 
            transaction = m.parseBroadcastTransaction()
            blockchain = m.parseBroadcastBlockchain()  
            if block is not None:
                block = Block.parseNewBlock(block)
                print("Received block #" + str(block.index))
                if block.is_genesis():
                    self.node.utxos[0] = [block.list_of_transactions[0].transaction_outputs[0]]
                    self.node.blockchain.add_block(block)
                    self.node.blockchain.print_blockchain()
                else:
                    valid_block = self.node.valid_proof(block)
                    if (valid_block):
                        print("Block #"+str(block.index)+" is valid and ready to be added to the blockchain")
                    
            if transaction is not None:
                transaction = Transaction.parseNewTransaction(transaction)
                valid = self.node.validate_transaction(transaction)
                if valid:
                    self.node.add_transaction_to_block(transaction)
            if blockchain is not None:
                pass
                
                