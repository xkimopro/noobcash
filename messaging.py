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

    def isServerGreetingClient(self,):
        return self.code == 1 and self.payload['message'] == 'serverGreetingClient'

    def isClientReplyToGreeting(self,):
        return self.code == 2 and self.payload['message'] == 'clientReplyToGreeting'

    def isStartAssignmentPhase(self,):
        return self.code == 3 and self.payload['message'] == 'startAssignmentPhase'
    
    def isStartAssignmentPhaseAck(self,):
        return self.code == 4 and self.payload['message'] == 'startAssignmentPhaseAck'
    
    def isSendNodesList(self,):
        return self.code == 5 and self.payload['message'] == 'sendNodesList'
    
    def isSendNodesListAck(self,):
        return self.code == 6 and self.payload['message'] == 'sendNodesListAck'

    



class Messaging:
    def __init__(self,connection,key):
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



    def serverGreetingClient(self, public_key_bytes):
        message = {
            'code' : 1,
            'payload' : {
                'message' : 'serverGreetingClient',
                'public_key' : public_key_bytes.decode()
            }
        }
        self.connection.send(str.encode(json.dumps(message)))


    def clientReplyToGreeting(self, public_key):
        message = {
            'code' : 2,
            'payload' : {
                'message' : 'clientReplyToGreeting',
                'public_key' : public_key.decode('utf-8')
            }
        }
        self.connection.send(str.encode(json.dumps(message)))

    def startAssignmentPhase(self, config):
        message = {
            'code' : 3,
            'payload' : {
                'message' : 'startAssignmentPhase',
                'nodes' : config.nodes
            }
        }
        self.connection.send(str.encode(json.dumps(message)))
    
    def startAssignmentPhaseAck(self, ):
        message = {
            'code' : 4,
            'payload' : {
                'message' : 'startAssignmentPhaseAck'
            }
        }
        self.connection.send(str.encode(json.dumps(message)))
    
    def sendNodesList(self, nodes_list ):
        payload = {
                'message' : 'sendNodesList' ,
                'nodes_list' : nodes_list 
        }
        signature_bytes = createMessageSignature(json.dumps(payload).encode('utf-8'),self.key)
        signature_str = signatureBytesToStr(signature_bytes)
        message = {
            'code' : 5,
            'payload' : payload,
            'signature' : signature_str
        }
        self.connection.send(str.encode(json.dumps(message)))
    
    def sendNodesListAck(self):
        payload = {
                'message' : 'sendNodesListAck' ,
        }
        signature_bytes = createMessageSignature(json.dumps(payload).encode('utf-8'),self.key)
        signature_str = signatureBytesToStr(signature_bytes)
        message = {
            'code' : 6,
            'payload' : payload ,
            'signature' : signature_str
        }
        self.connection.send(str.encode(json.dumps(message)))
    
    def sendBlockchainStarted(self):
        message = {
            'code' : 7,
            'payload' : {
                'message' : 'blockchain started' ,
            }
        }
        self.connection.send(str.encode(json.dumps(message)))

        

            


        







