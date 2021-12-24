import json


class Message:
    def __init__(self, code = 0 , payload =  { 'message' : 'test' } ):
        self.code = code
        self.payload = payload 
    
    def print(self,):
        print(self.code)
        print(self.payload)

    def isServerGreetingClient(self,):
        return self.code == 1 and self.payload['message'] == 'serverGreetingClient'

    def isClientReplyToGreeting(self,):
        return self.code == 2 and self.payload['message'] == 'clientReplyToGreeting'

    def isStartAssignmentPhase(self,):
        return self.code == 3 and self.payload['message'] == 'startAssignmentPhase'
    
    def isStartAssignmentPhaseAck(self,):
        return self.code == 4 and self.payload['message'] == 'startAssignmentPhaseAck'




class Messaging:
    def __init__(self,connection):
        self.connection = connection
    

    def parseToMessage(self , msg):
        data = json.loads(msg)
        code = data['code']
        payload = data['payload']
        return Message(code, payload)



    def serverGreetingClient(self, ):
        message = {
            'code' : 1,
            'payload' : {
                'message' : 'serverGreetingClient'
            }
        }
        self.connection.send(str.encode(json.dumps(message)))


    def clientReplyToGreeting(self, ):
        message = {
            'code' : 2,
            'payload' : {
                'message' : 'clientReplyToGreeting'
            }
        }
        self.connection.send(str.encode(json.dumps(message)))

    def startAssignmentPhase(self, ):
        message = {
            'code' : 3,
            'payload' : {
                'message' : 'startAssignmentPhase'
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

        

            


        







