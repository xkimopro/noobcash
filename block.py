from transaction import Transaction
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import json,time,base64

from config import Config
from functions import *

config = Config()

class Block:
	def __init__(self, index=0, nonce=0, list_of_transactions=[], previous_hash=1, timestamp=time.time(), current_hash=''):
		self.index = index
		self.nonce = nonce
		self.list_of_transactions = list_of_transactions
		self.previous_hash = previous_hash
		self.timestamp = timestamp
		self.current_hash = current_hash
		if self.current_hash ==  '': 
			self.current_hash=self.generate_hash().decode()


	def is_genesis(self,):
		return self.index == 0 and self.nonce == 0 and len(self.list_of_transactions) == 1 and self.previous_hash == 1


	def block_to_dict(self):			
		
		dicted_transactions = []
		for transaction in self.list_of_transactions:
			dicted_transactions.append(transaction.toDict())
		d = dict(
			index = self.index ,
			nonce = self.nonce ,
			list_of_transactions = dicted_transactions,
			previous_hash = self.previous_hash,
			timestamp = self.timestamp , 
			current_hash = self.current_hash
  		)
		return d

  
	def __repr__(self,):
		return json.dumps(self.block_to_dict(), indent=4)

	def generate_hash(self):
		str_repr = self.__repr__()
		digest = hashes.Hash(hashes.SHA256(), default_backend())
		digest.update(str_repr.encode('utf-8'))
		final_digest = digest.finalize()
		return base64.b64encode(final_digest)
	

	def is_hash_accepted(self,):
		for i in range(config.difficulty):
			if self.current_hash[i] != '0':
				return False
		return True



	@staticmethod
	def parseNewBlock(block_str):
		block_dict = json.loads(block_str)
		index = block_dict['index']
		nonce = block_dict['nonce']
		list_of_transactions = block_dict['list_of_transactions']
		lst = [ Transaction.parseNewTransaction(t, True) for t in list_of_transactions ]  		
		previous_hash = block_dict['previous_hash']
		timestamp = block_dict['timestamp']
		current_hash = block_dict['current_hash']    
		return Block(index,nonce,lst,previous_hash,timestamp,current_hash)