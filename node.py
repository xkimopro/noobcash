from wallet import Wallet
import socket ,time
from transaction import Transaction
from block import Block
from blockchain import blockchain
from functions import *

class Node:
    
    def __init__(self, is_bootstrap, config):
        
        self.utxos = {}
        self.blockchain = blockchain()
        self.messaging = None
        self.list_of_transactions = []
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
            
            pass


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
        
 
    def add_block_to_blockchain(self, block):
        block_transactions = block.transactions_
        for t in block_transactions:
            pass
            
 
    def create_transaction(self, receiver_id, amount):
        # self, sender_address, receiver_address, amount , transaction_inputs , transaction_outputs=[] ,transaction_id=None,signature=None
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
        self.utxos[self.id] = [utxo_sender]   
        self.utxos[receiver_id].append(utxo_receiver)
        # add trans to list
        self.broadcast_transaction(new_transaction)
        # print(new_transaction)


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
        print("SUCCESS!!")
        if self.config.block_capacity == len(self.list_of_transactions):
            # mine block
            # self.mine_block()
            pass
		



    def mine_block(self,):

        pass


	# def valid_proof(.., difficulty=MINING_DIFFICULTY):

	# #concencus functions

	# def valid_chain(self, chain):
	# 	#check for the longer chain accroose all nodes


	# def resolve_conflicts(self):
	# 	#resolve correct chain