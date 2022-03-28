import json, base64

from functions import *

class Message:
    def __init__(self, code = 0 , payload =  { 'message' : 'test' } , signature=None):
        self.code = code
        self.payload = payload 
        self.signature = signature
    
    def print(self,):
        print(self.code)
        print(self.payload)
        print(self.signature)

    def isAuthenticated(self , sender_public_key):
        signature_bytes = signatureStrToBytes(self.signature)
        status = verifyMessage(json.dumps(self.payload).encode('utf-8') , signature_bytes, sender_public_key)   
        if status['error_code'] == 0: return True
        else:
            informProblem(f"Message from {bytesFromPublicKeyObj(sender_public_key).decode()} discarded \n-Reason: {json.dumps(status)}")

    def parseClientInitMessage(self, ):
        if self.code == 0 and self.payload['message'] == 'clientInitMessage':
            return self.payload['public_key_bytes'] , self.payload['host'] , self.payload['port']
        return None

    def parseCliInitMessage(self, ):
        if self.code == 1 and self.payload['message'] == 'cliInitMessage':
            return self.payload['id'] , self.payload['host'] , self.payload['port']
        return None

    def parseBootstrapSendRing(self, ):
        if self.code == 2 and self.payload['message'] == 'bootstrapSendRing':
            return self.payload['ring'] 
        return None 

    def parseBroadcastBlock(self, ):
        if self.code == 3 and self.payload['message'] == 'broadcastNewBlock':
            return self.payload['block'] 
        return None 

    def parseBroadcastTransaction(self, ):
        if self.code == 4 and self.payload['message'] == 'broadcastNewTransaction':
            return self.payload['transaction'] 
        return None 
    
    def parseBroadcastBlockchain(self, ):
        if self.code == 4 and self.payload['message'] == 'broadcastNewBlockchain':
            return self.payload['blockchain'] 
        return None 


class Messaging:
    def __init__(self,connection, key=0):
        self.connection = connection
        self.key = key
    

    def parseToMessage(self , msg):
        data = json.loads(msg)
        code = data['code']
        if 'signature' in data: 
            signature = data['signature']
        else:
            signature = None
        payload = data['payload']
        return Message(code, payload, signature) 



    def clientInitMessage(self, public_key_bytes, host , port):
        message = {
            'code' : 0,
            'payload' : {
                'message' : 'clientInitMessage',
                'public_key_bytes' : public_key_bytes.decode(), 
                'host' : host ,
                'port' : port
            }
        }
        self.connection.send(str.encode(json.dumps(message)))

    def cliInitMessage(self, id, host , port):
        message = {
            'code' : 1,
            'payload' : {
                'message' : 'cliInitMessage',
                'id' : id, 
                'host' : host ,
                'port' : port
            }
        }
        print(str.encode(json.dumps(message)))
        self.connection.send(str.encode(json.dumps(message)))


    def bootstrapSendRing(self, ring):
        message = {
            'code' : 2,
            'payload' : {
                'message' : 'bootstrapSendRing',
                'ring' : json.dumps(ring)
            }
        }  
        self.connection.send(str.encode(json.dumps(message)))
        
    def broadcastBlock(self, block):
        message = {
            'code' : 3,
            'payload' : {
                'message' : 'broadcastNewBlock',
                'block' : str(block)
            }
        }
        self.connection.send(str.encode(json.dumps(message)))
        
    def broadcastTransaction(self, transaction):
        message = {
            'code' : 4,
            'payload' : {
                'message' : 'broadcastNewTransaction',
                'transaction' : str(transaction)
            }
        }
        self.connection.send(str.encode(json.dumps(message)))

    def broadcastBlockchain(self, blockchain):
        message = {
            'code' : 5,
            'payload' : {
                'message' : 'broadcastNewBlockchain',
                'blockchain' : str(blockchain)
            }
        }
        self.connection.send(str.encode(json.dumps(message)))