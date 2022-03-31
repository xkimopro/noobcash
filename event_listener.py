from sqlite3 import Timestamp
from threading import Thread
from messaging import *
from block import Block
from transaction import Transaction
import traceback

class EventListeningThread(Thread):

    def __init__(self, node ,  server_socket):
        Thread.__init__(self)
        self._running = True
        self.node = node
        self.server_socket = server_socket
        self.cached_messages = []

    def terminate(self):
        pass
    
    def run(self, *args, **kwargs):
        i = 0
        while True:
            if len(self.cached_messages) > 0 and not self.node.mining: 
                print("Popping message from cached messages queue instead of socket")
                m = self.cached_messages.pop()
            else:     
                i += 1
                conn, _ = self.server_socket.accept()
                data = conn.recv(4096000)
                if len(data) != 0:
                    try:
                        m = self.node.messaging.parseToMessage(data)
                    except Exception as e:
                        print("Exception in parseToMessage" + str(e))
                        print(data)                
                
                block = m.parseBroadcastBlock() 
                transaction = m.parseBroadcastTransaction()
                conflict_id = m.parseRequestPrevHashAndLength()
                hash_length = m.parseSendPrevHashAndLength()
                blockchain_request = m.parseRequestBlockchainFromNode()
                blockchain_block = m.parseSendBlockchainBlock()
                transaction_utxos = m.parseSendTransactionListAndUtxos()
                if not self.node.resolving_confilct:
                    
                    if block is not None:
                        block = Block.parseNewBlock(block)
                        print("Received block #" + str(block.index))
                        if block.is_genesis():
                            print("Block is of genesis type")
                            self.node.utxos[0] = [block.list_of_transactions[0].transaction_outputs[0]]
                            self.node.blockchain.add_block(block)
                        else:
                            is_valid = self.node.valid_proof(block)
                            if is_valid:
                                self.node.stop_miner_thread = True 
                                print("Block validated and added to my blockchain. Miner thread stopped for efficiency")
                                self.node.blockchain.add_block(block)
                                self.node.list_of_transactions = []
                                print("Block #"+str(block.index)+" is valid and ready to be added to the blockchain")
                                self.node.timestamp = time.time()
                                self.node.transactions = self.node.transactions + 1
                                stdout_print("time is")
                                stdout_print(self.node.timestamp)
                                stdout_print("transactions number")
                                stdout_print(self.node.transactions)
                            else: 
                                print("Valid block discarded.")                    
                                if block.previous_hash != self.node.blockchain.get_latest_blocks_hash():
                                    print("Previous hash mismatch. Received block belongs to a different blockchain initializing consensus algorithm")
                                    self.node.mutex.acquire()
                                    print("Lock acquired for conflict resolution")
                                    self.node.resolve_conflicts()
                    
                    
                        
                        
                    if blockchain_request is not None:
                        request_id = blockchain_request
                        print("blockchain_requested from node #" + str(request_id) )
                        self.node.send_blockchain(request_id)  
                     
                    
                    # If not mining receive messages                
                    if not self.node.mining:
                        
                        if transaction is not None:
                            print("Received new transaction")
                            transaction = Transaction.parseNewTransaction(transaction)
                            try:
                                self.node.mutex.acquire()
                                print("Event listening thread acquired lock")
                                self.node.validate_transaction(transaction)
                                print("Transaction validated. Adding to transaction list ( current block under construction )")
                                self.node.add_transaction_to_block(transaction)
                            except Exception as e:
                                print("Transaction "+transaction.transaction_id+" Invalid.Because " + str(e))
                                print(traceback.format_exc())
                                self.node.mutex.release()     
                    # If currently mining cache transactions
                    else: 
                        print("Currently mining caching packet")
                        self.cached_messages.append(m)
                          
                else:
                    print("In resolving conflict mode.")
                    if hash_length is not None:
                        (id, length, current_hash) = hash_length
                        key = str(length) + ' ' + str(current_hash)
                        val = id
                        print("Received conflict resolution vote of length: "+str(length)+"by node"+ str(id))
                        self.node.add_vote(key,val)

                    if blockchain_block is not None:
                        block = Block.parseNewBlock(blockchain_block)
                        print("Received blockchain block with index "+str(block.index)+" for conflict resolution by node"+ str(id))
                        if block.index == 0:
                            print("Discarding my blockchain receiving new one")
                            self.node.discard_current_blockchain()
                        self.node.add_blockchain_block(block)

                    if transaction_utxos is not None:
                        print("Received Transaction list and utxos for conflict resolution by node"+ str(id))
                        (dicted_transactions, utxos) = transaction_utxos
                        print("RECEIVED UTXOS")
                        print(utxos)
                        self.node.list_of_transactions = [ Transaction.parseNewTransaction(t, True) for t in dicted_transactions ]                    
                        self.node.utxos = utxos
                        self.node.resolving_confilct = False
                        self.node.votes = {}
                        self.node.mutex.release()
                        
                if conflict_id is not None:
                        print("Received request to vote for conflict resolution by node" + str(conflict_id))
                        if not self.node.resolving_confilct:
                            self.node.send_hash_length(conflict_id,False)
                        else:
                            self.node.send_hash_length(conflict_id,True)
                            
                            
                        

                
                