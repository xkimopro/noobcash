from config import Config

from functions import *
# from transaction import Transaction
    
class Wallet:

        def __init__(self, host, port):
                self.key = generateInitialkey()
                self.public_key = self.key.public_key()
                self.public_key_bytes = publicKeyBytes(self.key)     
                self.host = host 
                self.port = port 
                self.transactions = []