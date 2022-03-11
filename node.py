from wallet import Wallet
import socket ,time
from transaction import Transaction
from block import Block
from blockchain import blockchain
class Node:
    
    def __init__(self, is_bootstrap, config):
        
        self.utxos = {}
        self.blockchain = blockchain()
        self.messaging = None
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
		

	# def.create_new_block():
    #     pass

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
 
 
    def broadcast_transaction(self):
        for node in self.ring:
            if not self.is_myself(node): 
                with socket.socket() as temp_socket:                
                    try:
                        temp_socket.connect((node['host'], node['port']))
                        self.messaging.connection = temp_socket
                        self.messaging.startAssignmentPhaseAck()
                    except socket.error as e:
                        print("Could not connect to %s:%d" % (node['host'], node['port']))



    def create_and_broadcast_genesis_block(self,):
        genesis_transaction = Transaction(0, self.wallet.public_key_bytes.decode() , self.config.nodes * 100)
        first_utxo = {
            'id' : genesis_transaction.transaction_id, 
            'who' : 0,
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
            
 
    # def create_transaction(receiver_id, amount):
    #     self, sender_address, receiver_address, amount , transaction_inputs , transaction_outputs=[] ,transaction_id=None,signature=None
        
        
        
        # t = Transaction(self.id, receiver_id , amount,  )

           
        #    self.sender_address = id            #To public key του wallet από το οποίο προέρχονται τα χρήματα
        # self.receiver_address = receiver_address# To public key του wallet στο οποίο θα καταλήξουν τα χρήματα
        # self.amount = amount #το ποσό που θα μεταφερθεί        
        # self.transaction_inputs = transaction_inputs
        # self.transaction_outputs = transaction_inputs
        # self.transaction_id = self.generateHash() if transaction_id is None else transaction_id #το hash του transaction
        # self.signature = signature 




	# def validdate_transaction():
	# 	#use of signature and NBCs balance


	# def add_transaction_to_block():
	# 	#if enough transactions  mine



	# def mine_block():





		

	# def valid_proof(.., difficulty=MINING_DIFFICULTY):




	# #concencus functions

	# def valid_chain(self, chain):
	# 	#check for the longer chain accroose all nodes


	# def resolve_conflicts(self):
	# 	#resolve correct chain
