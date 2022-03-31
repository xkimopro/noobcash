from wallet import Wallet
import socket ,time
from transaction import Transaction
from block import Block
from blockchain import blockchain
from functions import *
import signal, os, threading, random
from threading import Thread, Lock

class Node:
    
    def __init__(self, is_bootstrap, config):
        
        self.utxos = {}
        self.blockchain = blockchain()
        self.messaging = None
        self.list_of_transactions = []
        self.timestamp = 0
        self.transactions = 0
        
        self.stop_miner_thread = False 
        self.mining = False
        self.prev_time = time.time()
        self.time_to_add_new_block = []
        self.votes = {}
        self.mutex = Lock()
        self.conflict_occured = []
        self.time = 0



        if is_bootstrap:
            self.current_id_count = 0
            self.config = config
            self.wallet = Wallet(config.bootstrap_node_host , config.bootstrap_node_port)
            self.NBC = config.nodes * 100
            self.ring = [{
                'id' : 0,
                'host' : config.bootstrap_node_host,
                'port' : config.bootstrap_node_port,
                'public_key_bytes' : self.wallet.public_key_bytes.decode(),
                'balance' : self.NBC
            }]
            self.temp_connections_list = []
            self.id = 0
        else: 
            self.id = 0
            self.config = config
            self.wallet = Wallet(config.client_node_host , config.client_node_port)
            self.NBC = 0
            self.ring=[]
            
    def register_node_to_ring(self, temp_conn, public_key_bytes, host, port ):
        self.temp_connections_list.append(temp_conn)
        self.current_id_count += 1
        new_node = {
                'id' : self.current_id_count,
                'host' : host,
                'port' : port,
                'public_key_bytes' : public_key_bytes,
                'balance' : 0
        }
        self.ring.append(new_node)
        
    # add this node to the ring, only the bootstrap node can add a node to the ring after checking his wallet and ip:port address
    def broadcast_ring(self):
        for i in range(len(self.ring)):
            self.conflict_occured.append(False)
        for node in self.ring: 
            self.utxos[node['id']] = []  
        for connection in self.temp_connections_list:
            self.messaging.connection = connection
            self.messaging.bootstrapSendRing(self.ring)            
            
    def is_myself(self, node):
        return node['host'] == self.wallet.host and node['port'] == self.wallet.port    
            
    def parse_ring(self, ring):
        self.ring = ring
        for node in ring:
            if self.is_myself(node):
               self.id = node['id']
            self.utxos[node['id']] = []
        for i in range(len(ring)):
            self.conflict_occured.append(False)          

    def id_from_pub_key(self, pub_key):
        for node in self.ring:
            if node['public_key_bytes'] == pub_key: return node['id']        

    def pub_key_from_id(self, id):
        for node in self.ring:
            if node['id'] == id: return node['public_key_bytes']
    
    def close_client_temp_connections(self,):
        for t in self.temp_connections_list:
            t.shutdown(socket.SHUT_RDWR)

        self.temp_connections_list = []
 
    def broadcast_transaction(self,transaction):
        for node in self.ring:
            if not self.is_myself(node): 
                with socket.socket() as temp_socket:                
                    try:
                        temp_socket.settimeout(12)
                        temp_socket.connect((node['host'], node['port']))
                        self.messaging.connection = temp_socket
                        self.messaging.broadcastTransaction(transaction)
                    except socket.error as e:
                        print("Could not connect to %s:%d" % (node['host'], node['port']))

    def create_and_broadcast_genesis_block(self,):
        genesis_transaction = Transaction(0, self.wallet.public_key_bytes.decode() , self.config.nodes * 100)
        first_utxo = {
            'id' : genesis_transaction.transaction_id, 
            'who' : self.wallet.public_key_bytes.decode(),
            'amount' : self.config.nodes * 100
        }
        genesis_transaction.transaction_outputs = [first_utxo]
        
        self.utxos[self.id] = [first_utxo]
        genesis_transaction.signTransaction(self.wallet.key)    

        genesis_block = Block(list_of_transactions=[genesis_transaction])
        self.blockchain.add_block(genesis_block)
        
        self.broadcast_block(genesis_block)
         
    def broadcast_block(self, block):
        for node in self.ring:
            if not self.is_myself(node): 
                with socket.socket() as temp_socket:                
                    try:
                        temp_socket.settimeout(12)
                        temp_socket.connect((node['host'], node['port']))
                        self.messaging.connection = temp_socket
                        print("Broadcasting block")
                        self.messaging.broadcastBlock(block)
                    except socket.error as e:
                        print("Could not connect to %s:%d" % (node['host'], node['port']))
        print("Finished block broadcasting")
    
    def create_transaction(self, receiver_id, amount):
        # sender_address, receiver_address, amount , transaction_inputs , transaction_outputs=[] ,transaction_id=None,signature=None
        receiver_address = self.pub_key_from_id(receiver_id)
        sender_address = self.wallet.public_key_bytes.decode()
        transactions_inputs = []
        savings = 0
        for prev_utxo in self.utxos[self.id]:
            transactions_inputs.append(prev_utxo['id'])
            savings += prev_utxo['amount']
        if savings < amount:
            raise Exception('not enough money')
        new_transaction = Transaction(sender_address, receiver_address, amount, transactions_inputs)
        utxo_sender = {
            'id' : new_transaction.transaction_id, 
            'who' : sender_address,
            'amount' : savings - amount
        }
        utxo_receiver = {
            'id' : new_transaction.transaction_id, 
            'who' : receiver_address,
            'amount' : amount
        }
        new_transaction.transaction_outputs = [utxo_sender, utxo_receiver]
        new_transaction.signTransaction(self.wallet.key)

        

        print("Transaction with id " + str(new_transaction.transaction_id) + " issued. Now broadcasting. ")
        self.broadcast_transaction(new_transaction)
        print("Transaction with id " + str(new_transaction.transaction_id) + " broadcasted. Now registering to block. ")
        self.timestamp = time.time()
        self.transactions += 1
        stdout_print("transactions number")
        stdout_print(self.transactions)

        # change utxos through add transaction to the block
        self.add_transaction_to_block(new_transaction)
        

    def validate_transaction(self, transaction): # use of signature and NBCs balance
        
        # Check if already in transaction list
        for t in self.list_of_transactions:
            if t.transaction_id == transaction.transaction_id:
                raise Exception("Duplicate transaction received")
        
        transaction_dict = transaction.toDict()
        if transaction_dict['sender_address'] == transaction_dict['receiver_address']:
            raise Exception('sender must be different from recepient')
        found_sender = False
        found_receiver = False
        for peer in self.ring:
            if transaction_dict['sender_address'] == peer['public_key_bytes']:
                found_sender = True
            if transaction_dict['receiver_address'] == peer['public_key_bytes']:
                found_receiver = True
            if found_receiver == True and found_sender == True:
                break
        if found_sender == False:
            raise Exception('unknown sender')
        if found_receiver == False:
            raise Exception('unknown recepient')
        if transaction_dict['amount'] <= 0:
            raise Exception('negative amount')

        if transaction_dict['transaction_id'] != transaction.generateHash():
            print(transaction_dict['transaction_id'])
            print(transaction.generateHash())
            raise Exception('invalid hash')

        # verify signature
        id_bytes = transaction_dict['transaction_id'].encode()
        signature_bytes = signatureStrToBytes(transaction_dict['signature'])
        pub_key_bytes = publicKeyFromBytes(transaction_dict['sender_address'].encode())

        status = verifyMessage(id_bytes, signature_bytes, pub_key_bytes)
        if status['error_code'] == 1:
            print(status['message'])
            raise Exception('invalid signature')

        # verify that transaction inputs are unique
        if len(set(transaction_dict['transaction_inputs'])) != len(transaction_dict['transaction_inputs']):
            raise Exception('duplicate inputs')

        # assert that it is not using itself as input
        if transaction_dict['transaction_id'] in transaction_dict['transaction_inputs']:
            raise Exception('invalid inputs')
        
        # verify that inputs are utxos
        sender_id = self.id_from_pub_key(transaction_dict['sender_address'])
        sender_utxos = self.utxos[sender_id]
        budget = 0
        for txin_id in transaction_dict['transaction_inputs']:   
            found = False
            for utxo in sender_utxos:
                if utxo['id'] == txin_id and utxo['who'] == transaction_dict['sender_address']:
                    found = True
                    budget += utxo['amount']
                    sender_utxos.remove(utxo)
                    break

            if not found:
                raise Exception('missing transaction inputs')

        # verify money is enough
        if budget < transaction_dict['amount']:
            raise Exception('not enough money')
        return True	
    

    def add_transaction_to_block(self, transaction): # if enough transactions  mine
        transaction_dict = transaction.toDict()
        sender_id = self.id_from_pub_key(transaction_dict['sender_address'])
        receiver_id = self.id_from_pub_key(transaction_dict['receiver_address'])
        utxo_sender = transaction_dict['transaction_outputs'][0]
        utxo_receiver = transaction_dict['transaction_outputs'][1]
        
            
        self.utxos[sender_id] = [utxo_sender]   
        self.utxos[receiver_id].append(utxo_receiver)

        self.list_of_transactions.append(transaction)
        self.list_of_transactions.sort(key=lambda x: x.transaction_id)
        print("Transaction " + str(transaction.transaction_id) + " added to list of transactions")
        
        if self.config.block_capacity == len(self.list_of_transactions):
            # mine block
            print("Starting mining process. Benchmarker releasing lock")
            self.mining=True
            miner_thread = MinerThread(self)
            miner_thread.start()
        else:
            self.mutex.release()                  

    def mine_block(self,):
        timestamp = time.time()
        previous_hash = self.blockchain.get_latest_blocks_hash()
        index = self.blockchain.get_latest_blocks_index() + 1
        nonce = 0
        while True:
            if self.stop_miner_thread: 
                print("Stopping nonce")
                
                self.stop_miner_thread = False 
                self.mining = False
                self.mutex.release()
                
                quit()                         
            block = Block(index=index, nonce=nonce, list_of_transactions=self.list_of_transactions, previous_hash=previous_hash, timestamp=timestamp, current_hash='')
            if block.is_hash_accepted():
                if self.stop_miner_thread: 
                    print("Stopping accepted")
                    self.stop_miner_thread = False
                    self.mining = False
                    self.mutex.release() 
                    quit()                         
                print("Found nonce "+str(nonce)+" for block with index " + str(index))
                return block
            nonce += 1

    def valid_proof(self, block):
        previous_hash = self.blockchain.get_latest_blocks_hash()
        current_index = self.blockchain.get_latest_blocks_index() + 1
        if block.previous_hash == previous_hash and current_index == block.index:
            # Check that the contained list of transactions is the same with my list of transactions
            received_list_of_transactions = block.list_of_transactions 
            if len(received_list_of_transactions) == len(self.list_of_transactions):
                for i in range(len(received_list_of_transactions)):
                    if received_list_of_transactions[i] != self.list_of_transactions[i]: 
                        print("Block invalid because: Transactions lists dont match")
                        return False
            else: 
                print("Block invalid because: Transactions lists different length")
                return False    
            # Check if contents have been tampered
            # Hash must be generated with current_hash = ''
            temp = block.current_hash
            block.current_hash = ''
            if block.generate_hash().decode() != temp: 
                print("Block invalid because: Hash mismatch")
                return False            
            # Remember to reassign the verified hash!
            block.current_hash = temp
            # Check if hash fullfills mining difficulty criteria
            if not block.is_hash_accepted(): 
                print("Block invalid because: Hash not accepted (zeroes)")
                return False
            return True                        
        else: 
            print("Block invalid because: Wrong index or previous hash")
            return False
        
    def broadcast_chain_request(self,):
        self.time = time.time()
        for node in self.ring:
            if not self.is_myself(node): 
                with socket.socket() as temp_socket:                
                    try:
                        temp_socket.settimeout(12)
                        temp_socket.connect((node['host'], node['port']))
                        self.messaging.connection = temp_socket
                        self.messaging.requestPrevHashAndLength(self.id)
                    except socket.error as e:
                        print("Could not connect to %s:%d" % (node['host'], node['port']))

    def resolve_conflicts(self):
        # Ask nodes for longer chain
        self.conflict_occured[self.id] = True
        print("NEW CONFLICT",self.conflict_occured)

        self.broadcast_chain_request()
        pass

    def all_false(self,):
        for i in range(len(self.conflict_occured)):
            if self.conflict_occured[i]: 
                return False
        return True
    
    def send_hash_length(self,conflict_id,dont_count_me):
        id = self.id
        length = len(self.blockchain.block_list) if not dont_count_me else 0
        current_hash = self.blockchain.get_latest_blocks_hash()
        for node in self.ring:
            if node['id'] == conflict_id: 
                with socket.socket() as temp_socket:                
                    try:
                        temp_socket.settimeout(12)
                        temp_socket.connect((node['host'], node['port']))
                        self.messaging.connection = temp_socket
                        self.messaging.sendPrevHashAndLength(id, length, current_hash)
                        break
                    except socket.error as e:
                        print("Could not connect to %s:%d" % (node['host'], node['port']))
    
    def add_vote(self, key, val):
        if self.conflict_occured[self.id]:
            if not key in self.votes: self.votes[key] = [val]
            else: self.votes[key].append(val)
            print(self.votes)
            num_votes = 0
            for len_hash in self.votes:
                num_votes += len(self.votes[len_hash]) 
            
            if (num_votes == self.config.nodes - 1):
                max_len = -1
                request_id = -1
                
                for len_hash in self.votes: max_len = max(max_len, int(len_hash.split(' ')[0]))
                print("Decided on max length = " + str(max_len))
                max_votes = -1
                for len_hash in self.votes:
                    if int(len_hash.split(' ')[0]) == max_len: max_votes = max(len(self.votes[len_hash]),max_votes)
                for len_hash in self.votes:
                    if max_len==int(len_hash.split(' ')[0]) and len(self.votes[len_hash]) == max_votes:
                        for id in self.votes[len_hash]:
                            request_id = max(id, request_id)
                self.request_longest_blockchain(request_id)
                print("I WANT blockchain with max length = " + str(max_len) + " from " + str(request_id))               
        else:
            print("Received a vote for a hash and length while not in resolve conflict phase") 
               
    def request_longest_blockchain(self,request_id):
        for node in self.ring:
            if node['id'] == request_id: 
                with socket.socket() as temp_socket:                
                    try:
                        temp_socket.settimeout(12+int(self.id))
                        temp_socket.connect((node['host'], node['port']))
                        self.messaging.connection = temp_socket
                        self.messaging.requestBlockchainFromNode(self.id)
                        break
                    except socket.error as e:
                        print("Could not connect to %s:%d" % (node['host'], node['port']))

    def broadcast_continue(self,):
        for node in self.ring:
            if node['id'] != self.id:
                with socket.socket() as temp_socket:                
                    try:
                        temp_socket.settimeout(12+int(self.id))
                        temp_socket.connect((node['host'], node['port']))
                        self.messaging.connection = temp_socket
                        self.messaging.sendContinue(self.id)
                    except socket.error as e:
                        print("Could not connect to %s:%d" % (node['host'], node['port']))
    
    def send_blockchain(self, request_id):
        print("requestedededed ", request_id)
        for node in self.ring:
            if node['id'] == request_id:
                for block in self.blockchain.block_list:
                    with socket.socket() as temp_socket:                
                        try:
                            temp_socket.settimeout(12+int(self.id))
                            temp_socket.connect((node['host'], node['port']))
                            self.messaging.connection = temp_socket
                            self.messaging.sendBlockchainBlock(block)
                        except socket.error as e:
                            print("Could not connect to %s:%d" % (node['host'], node['port']))

                with socket.socket() as temp_socket:                
                    try:
                        temp_socket.connect((node['host'], node['port']))
                        self.messaging.connection = temp_socket
                        dicted_transactions = []
                        for transaction in self.list_of_transactions:
                            dicted_transactions.append(transaction.toDict())
                        self.messaging.sendTransactionListAndUtxos(dicted_transactions, self.utxos)
                    except socket.error as e:
                        print("Could not connect to %s:%d" % (node['host'], node['port']))
    
    def discard_current_blockchain(self,):
        self.blockchain = blockchain()
    
    def add_blockchain_block(self, block):
        self.blockchain.add_block(block)

    def view_transactions(self,):
        last_block = self.blockchain.block_list[-1]
        dicted_transactions = []
        for transaction in last_block.list_of_transactions:
            dicted_transactions.append(transaction.toDict())
        return dicted_transactions
    
    
    
class MinerThread(threading.Thread):
    
    def __init__(self, parent_node : Node):
        threading.Thread.__init__(self)
        self.parent_node = parent_node
        
    def run(self,*args,**kwargs):
        self.parent_node.prev_time = time.time()
        mined_block = self.parent_node.mine_block()

        if self.parent_node.blockchain.get_latest_blocks_index() != mined_block.index:
            print("Broadcasting newly found block with index " + str(mined_block.index))
            self.parent_node.blockchain.add_block(mined_block)
            self.parent_node.list_of_transactions = []
            self.parent_node.broadcast_block(mined_block)
            new_time = time.time()
            self.parent_node.time_to_add_new_block.append(new_time - self.parent_node.prev_time)
            print(self.parent_node.time_to_add_new_block)
        else:
            print("Someone broadcasted first. Dropping newly found block with index " + str(mined_block.index) )
        self.parent_node.mining = False
        self.parent_node.mutex.release()