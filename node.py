from wallet import Wallet
import socket ,time
from transaction import Transaction
from block import Block
from blockchain import blockchain
from functions import *
import signal, os, threading


class Node:
    
    def __init__(self, is_bootstrap, config):
        
        self.utxos = {}
        self.blockchain = blockchain()
        self.messaging = None
        self.list_of_transactions = []
        
        self.stop_miner_thread = False 
        self.miner_broadcasting = False
        
        self.resolving_confilct = False
        self.votes = {}

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
                        temp_socket.connect((node['host'], node['port']))
                        self.messaging.connection = temp_socket
                        self.messaging.broadcastBlock(block)
                    except socket.error as e:
                        print("Could not connect to %s:%d" % (node['host'], node['port']))
 
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

        self.broadcast_transaction(new_transaction)

        # change utxos through add transaction to the block
        self.add_transaction_to_block(new_transaction)



    def validate_transaction(self, transaction): # use of signature and NBCs balance
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
        # print(sender_utxos)
        budget = 0
        for txin_id in transaction_dict['transaction_inputs']:
            found = False

            for utxo in sender_utxos:
                # print(utxo['who'])
                # print(transaction_dict['sender_address'])
                if utxo['id'] == txin_id and utxo['who'] == transaction_dict['sender_address']:
                    found = True
                    budget += utxo['amount']
                    sender_utxos.remove(utxo)
                    break

            if not found:
                raise Exception('missing transaction inputs')

        if sender_utxos != []:
            raise Exception('forgot a utxo')

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
        print("Transaction " +transaction.transaction_id+ "validated")
        if self.config.block_capacity == len(self.list_of_transactions):
            # mine block
            print("Starting mining process")
            miner_thread = MinerThread(self)
            miner_thread.start()                  

    def mine_block(self,):
        timestamp = time.time()
        previous_hash = self.blockchain.get_latest_blocks_hash()
        index = self.blockchain.get_latest_blocks_index() + 1
        nonce = 0
        while True:
            if self.stop_miner_thread: 
                self.stop_miner_thread = False 
                quit()                         
            block = Block(index=index, nonce=nonce, list_of_transactions=self.list_of_transactions, previous_hash=previous_hash, timestamp=timestamp, current_hash='')
            if block.is_hash_accepted():
                if self.stop_miner_thread: 
                    self.stop_miner_thread = False 
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
                        return False
            else: return False    
            # Check if contents have been tampered
            # Hash must be generated with current_hash = ''
            temp = block.current_hash
            block.current_hash = ''
            if block.generate_hash().decode() != temp: 
                return False            
            # Remember to reassign the verified hash!
            block.current_hash = temp
            # Check if hash fullfills mining difficulty criteria
            if not block.is_hash_accepted(): return False
            return True                        
        else: return False
        
        
	# def valid_chain(self, chain):
	# 	#check for the longer chain accross all nodes

    def broadcast_chain_request(self,):
        for node in self.ring:
            if not self.is_myself(node): 
                with socket.socket() as temp_socket:                
                    try:
                        temp_socket.connect((node['host'], node['port']))
                        self.messaging.connection = temp_socket
                        self.messaging.requestPrevHashAndLength(self.id)
                    except socket.error as e:
                        print("Could not connect to %s:%d" % (node['host'], node['port']))

    def resolve_conflicts(self):
        # Ask nodes for longer chain
        self.resolving_confilct = True
        self.broadcast_chain_request()
        pass
    
    def send_hash_length(self,conflict_id):
        id = self.id
        length = len(self.blockchain.block_list)
        current_hash = self.blockchain.get_latest_blocks_hash()
        for node in self.ring:
            if node['id'] == conflict_id: 
                with socket.socket() as temp_socket:                
                    try:
                        temp_socket.connect((node['host'], node['port']))
                        self.messaging.connection = temp_socket
                        self.messaging.sendPrevHashAndLength(id, length, current_hash)
                        break
                    except socket.error as e:
                        print("Could not connect to %s:%d" % (node['host'], node['port']))
    
    def add_vote(self, key, val):
        if self.resolving_confilct:
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
                max_votes = -1
                for len_hash in self.votes:
                    if int(len_hash.split(' ')[0]) == max_len: max_votes = max(len(self.votes[len_hash]),max_votes)
                for len_hash in self.votes:
                    if len(self.votes[len_hash]) == max_votes: request_id = self.votes[len_hash][0]                              
                self.request_longest_blockchain(request_id)
                        
        else:
            print("Received a vote for a hash and length while not in resolve conflict phase") 
               
    def request_longest_blockchain(self,request_id):
        for node in self.ring:
            if node['id'] == request_id: 
                with socket.socket() as temp_socket:                
                    try:
                        temp_socket.connect((node['host'], node['port']))
                        self.messaging.connection = temp_socket
                        self.messaging.requestBlockchainFromNode(self.id)
                        break
                    except socket.error as e:
                        print("Could not connect to %s:%d" % (node['host'], node['port']))
    
    def send_blockchain(self, request_id):
        for node in self.ring:
            if node['id'] == request_id: 
                for block in self.blockchain.block_list:
                    with socket.socket() as temp_socket:                
                        try:
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
        mined_block = self.parent_node.mine_block()
        self.parent_node.miner_broadcasting = True
        # Add to yourself first
        self.parent_node.blockchain.add_block(mined_block)
        self.parent_node.list_of_transactions = []
        # Then broadcast to others 
        self.parent_node.broadcast_block(mined_block)
        self.parent_node.miner_broadcasting = False
        