import os, json
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

from functions import *


class Transaction:

    def __init__(self, sender_address, receiver_address, amount , transaction_inputs , transaction_outputs=[] ,transaction_id=None,signature=None):


        ##set
        self.sender_address = sender_address            #To public key του wallet από το οποίο προέρχονται τα χρήματα
        self.receiver_address = receiver_address# To public key του wallet στο οποίο θα καταλήξουν τα χρήματα
        self.amount = amount #το ποσό που θα μεταφερθεί        
        self.transaction_inputs = transaction_inputs
        self.transaction_outputs = transaction_inputs
        self.transaction_id = self.generateHash() if transaction_id is None else transaction_id #το hash του transaction
        self.signature = signature 


    
    def transactionStrRepr(self):
        d = dict(
            sender_address = self.sender_address ,
            receiver_address = self.receiver_address ,
            amount = self.amount,
            transaction_inputs = self.transaction_inputs,
            transaction_outputs = self.transaction_outputs 
        )
        return json.dumps(d)


    def generateHash(self):
        str_repr = self.transactionStrRepr()
        digest = hashes.Hash(hashes.SHA256(), default_backend())
        digest.update(str_repr.encode('utf-8'))
        final_digest = digest.finalize()
        return base64.b64encode(final_digest)

    def toDict(self):
        d = dict(
            sender_address = self.sender_address ,
            receiver_address = self.receiver_address ,
            amount = self.amount,
            transaction_inputs = self.transaction_inputs,
            transaction_outputs = self.transaction_outputs,
            transaction_id = self.transaction_id ,
            signature = self.signature 
        )
        return d

    def signTransaction(self, key): 
        """
        Sign transaction with private key
        """
        signature_bytes = createMessageSignature(self.transaction_id , key)
        signature = signatureBytesToStr(signature_bytes)
        self.signature = signature



    def verifyTransaction(self, all_addresses):
        if self.sender_address not in all_addresses or self.receiver_address not in all_addresses:
            raise Exception("Invalid wallet address for sender or receiver")
        if self.sender_address == self.receiver_address:
            raise Exception("Sender, Receiver cannot be of the same address")
        if self.amount <= 0:
            raise Exception("Transaction amount cannot be negative or zero")

               
        transaction_id = self.generateHash()
        if transaction_id != self.transaction_id:
            raise Exception("Invalid transaction_id")



    def __repr__(self) -> str:
        inform("Printing transaction")
        print('sender_address: '+ self.sender_address)
        print('receiver_address: '+ self.receiver_address)
        print('amount: '+ str(self.amount))
        print('transaction_inputs: '+ str(self.transaction_inputs))
        print('transaction_outputs: '+ str(self.transaction_outputs))
        print('transaction_id: '+ str(self.transaction_id))
        print('signature: '+ str(self.signature))
        return ""
        

    @staticmethod
    def fromDict(d):
        keys = ['sender_address','receiver_address','amount','transaction_inputs','transaction_outputs','transaction_id','signature']
        if set(d.keys()) != set(keys):
            raise Exception("Missing or unmatched dictionary keys")
        return Transaction( d['sender_address'],
                     d['receiver_address'],
                     d['amount'],
                     d['transaction_inputs'],
                     d['transaction_outputs'],
                     d['transaction_id'], 
                     d['signature'] 
        )
        















