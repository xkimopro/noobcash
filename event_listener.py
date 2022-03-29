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
        i = 0
        while True:     
            i += 1
            conn, _ = self.server_socket.accept()
            data = conn.recv(40960)
            if len(data) != 0:
                # print(data)
                m = self.node.messaging.parseToMessage(data)
                
                block = m.parseBroadcastBlock() 
                transaction = m.parseBroadcastTransaction()
                blockchain = m.parseBroadcastBlockchain()
                conflict = m.parseRequestPrevHashAndLength()
                hash_length = m.parseSendPrevHashAndLength()

                if block is not None:
                    block = Block.parseNewBlock(block)
                    print("Received block #" + str(block.index))
                    if block.is_genesis():
                        print("Block is of genesis type")
                        self.node.utxos[0] = [block.list_of_transactions[0].transaction_outputs[0]]
                        self.node.blockchain.add_block(block)
                    else:
                        is_valid = self.node.valid_proof(block)
                        if is_valid and not self.node.miner_broadcasting:
                            self.node.stop_miner_thread = True 
                            print("Block validated and added to my blockchain. Miner thread stopped for efficiency")
                            self.node.blockchain.add_block(block)
                            self.node.list_of_transactions = []
                            print("Block #"+str(block.index)+" is valid and ready to be added to the blockchain")
                            self.resolve_conflicts()
                        else: 
                            
                            print("Valid block discarded. Checking if received block's previous hash matches current block hash or not")                    
                            if block.previous_hash != self.node.blockchain.get_latest_blocks_hash():
                                print("Previous hash mismatch. Received block belongs to a different blockchain initializing consensus algorithm")
                                self.resolve_conflicts()
                    self.node.blockchain.print_blockchain()

                if transaction is not None:
                    print("Received new transaction")
                    transaction = Transaction.parseNewTransaction(transaction)
                    valid = self.node.validate_transaction(transaction)
                    if valid:
                        print("Transaction validated. Adding to transaction list ( current block under construction )")
                        self.node.add_transaction_to_block(transaction)
                if blockchain is not None:
                    pass
                if conflict is not None:
                    id = self.node.id
                    length = len(self.node.blockchain.block_list)
                    current_hash = self.node.blockchain.get_latest_blocks_hash()
                    self.node.messaging.sendPrevHashAndLength(id,length,current_hash)
                if hash_length is not None:
                    (id, length, current_hash) = hash_length
                    key = str(length) + '_' + str(current_hash)
                    print(key)

                
                