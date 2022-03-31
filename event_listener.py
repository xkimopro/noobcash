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
            if len(self.cached_messages) > 0 and not self.node.mining and self.node.all_false(): 
                print("Popping message from cached messages queue instead of socket")
                m = self.cached_messages.pop()
            else:     
                i += 1
                conn, _ = self.server_socket.accept()
                final = ''
                data = conn.recv(1024)
                final = data
                while len(data) == 1024:
                    data = conn.recv(1024)
                    final += data
                if len(final) != 0:
                    try:
                        m = self.node.messaging.parseToMessage(final)
                    except Exception as e:
                        print("Exception in parseToMessage" + str(e))
                        print(final)                
                
            block = m.parseBroadcastBlock() 
            transaction = m.parseBroadcastTransaction()
            conflict_id = m.parseRequestPrevHashAndLength()
            blockchain_request = m.parseRequestBlockchainFromNode()
            hash_length = m.parseSendPrevHashAndLength()
            blockchain_block = m.parseSendBlockchainBlock()
            transaction_utxos = m.parseSendTransactionListAndUtxos()
            continue_flag = m.parseSendContinue()


            if not self.node.all_false(): #we have a conflict
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
                        else: 
                            print("Valid block discarded.")                    
                            if block.previous_hash != self.node.blockchain.get_latest_blocks_hash():
                                print("Previous hash mismatch. Received block belongs to a different blockchain initializing consensus algorithm")
                                print("Lock acquired for conflict resolution")
                                self.node.resolve_conflicts()
                if transaction is not None:
                    self.cached_messages.append(m)
                if conflict_id is not None:
                    self.node.conflict_occured[int(conflict_id)] = True
                    print("Received request to vote for conflict resolution by node" + str(conflict_id) + " currently not in conflict mode")
                    self.node.send_hash_length(conflict_id,False)
                if continue_flag is not None:  # a conflict was solved
                    print("Lets continue. Problem solved")
                    print("My list before is: ", self.node.conflict_occured)
                    print("My flag is: ", continue_flag)
                    self.node.conflict_occured[int(continue_flag)] = False
                    print("My list is: ", self.node.conflict_occured)
                if blockchain_request is not None:
                    request_id = blockchain_request
                    print("blockchain_requested from node #" + str(request_id))
                    if self.node.conflict_occured[int(self.node.id)] == False:
                        self.node.send_blockchain(request_id)
                    else:
                        if self.node.id > request_id:
                            self.node.send_blockchain(request_id)
                            self.node.conflict_occured[int(self.node.id)] = False
                            self.node.broadcast_continue()
                            self.node.votes = {}
                        else:
                            pass
                if hash_length is not None:
                    print("In resolving conflict mode.")
                    (id, length, current_hash) = hash_length
                    key = str(length) + ' ' + str(current_hash)
                    val = id
                    print("Received conflict resolution vote of length: "+str(length)+"by node"+ str(id))
                    self.node.add_vote(key,val)

                if blockchain_block is not None:
                    print("In resolving conflict mode.")
                    block = Block.parseNewBlock(blockchain_block)
                    print("Received blockchain block with index "+str(block.index)+" for conflict resolution by node"+ str(id))
                    if block.index == 0:
                        print("Discarding my blockchain receiving new one")
                        self.node.discard_current_blockchain()
                    self.node.add_blockchain_block(block)

                if transaction_utxos is not None:
                    print("In resolving conflict mode.")
                    print("Received Transaction list and utxos for conflict resolution by node"+ str(id))
                    (dicted_transactions, utxos) = transaction_utxos
                    print("RECEIVED UTXOS")
                    print(utxos)
                    self.node.list_of_transactions = [ Transaction.parseNewTransaction(t, True) for t in dicted_transactions ]                    
                    self.node.utxos = utxos
                    self.node.conflict_occured[int(self.node.id)] = False
                    self.node.broadcast_continue()
                    self.node.votes = {}
            else: #we good no conflict
                if hash_length is not None:
                    print("Error hash length")
                if blockchain_request is not None:
                    print("Error blockchain request")
                if blockchain_block is not None:
                    print("Error blockchain_block")
                if transaction_utxos is not None:
                    print("Error transaction_utxos")
                if continue_flag is not None:
                    print("Error continue_flag")
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
                        else: 
                            print("Valid block discarded.")                    
                            if block.previous_hash != self.node.blockchain.get_latest_blocks_hash():
                                print("Previous hash mismatch. Received block belongs to a different blockchain initializing consensus algorithm")
                                print("Lock acquired for conflict resolution")
                                self.node.resolve_conflicts()
                if transaction is not None:
                    if not self.node.mining:
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
                if conflict_id is not None:
                    self.node.conflict_occured[int(conflict_id)] = True
                    print("Received request to vote for conflict resolution by node" + str(conflict_id) + " currently not in conflict mode")
                    print("My list is: ", self.node.conflict_occured)
                    self.node.send_hash_length(conflict_id,False)
