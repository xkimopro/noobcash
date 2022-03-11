from threading import Thread
from messaging import *
from block import Block

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
            data = conn.recv(2048)
            
            m = self.node.messaging.parseToMessage(data)
            
            block = m.parseBroadcastBlock() 
            if block is not None:
                block = Block.parseNewBlock(block)
                if block.is_genesis():
                    self.node.utxos[0] = block.list_of_transactions[0].transaction_outputs[0]
                    self.node.blockchain.add_block(block)
                    print(self.node.utxos)
                    print("\n\n\n")
                    self.node.blockchain.print_blockchain()
                else:
                    pass
                    
                
                