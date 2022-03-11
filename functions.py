import os,sys,re,socket,json,threading
from config import Config 
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

import base64
# from block import Block 
# from transaction import Transaction 




class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def exitNoobcash(error_code, msg):
    d = {
        'error_code' : error_code , 
        'msg' : msg
    }
    print(f"{bcolors.FAIL}{json.dumps(d, indent=2)}{bcolors.ENDC}")
    quit()

def inform(msg):
    print(f"{bcolors.HEADER}{msg}{bcolors.ENDC}")

def informProblem(msg):
    print(f"{bcolors.FAIL}{msg}{bcolors.ENDC}")

def boldInform(msg):
    print(f"{bcolors.BOLD}{bcolors.HEADER}{msg}{bcolors.ENDC}{bcolors.ENDC}")



def getAllLanIPs():
    full_results = [re.findall('^[\w\?\.]+|(?<=\s)\([\d\.]+\)|(?<=at\s)[\w\:]+', i) for i in os.popen('arp -a')]
    final_results = [dict(zip(['HOSTNAME', 'LAN_IP', 'MAC_ADDRESS'], i)) for i in full_results]
    final_results = [{**i, **{'LAN_IP':i['LAN_IP'][1:-1]}} for i in final_results]
    return [  f['LAN_IP'] for f in final_results ]




def attemptBootstrapConnection(client_socket: socket, config : Config):
    boldInform("Noobcash client started")
    inform("Trying to connect to bootstrap node socket server")
    try:
        client_socket.connect((config.bootstrap_node_host, config.bootstrap_node_port))
    except socket.error as e:
        client_socket.close()
        exitNoobcash(1, "Cannot connect to bootstrap node at {}:{}".format(config.bootstrap_node_host , config.bootstrap_node_port) )
    inform(f"Connected through TCP at {config.bootstrap_node_host}:{config.bootstrap_node_port}")



def generateInitialkey():
    key = rsa.generate_private_key(backend=default_backend(), public_exponent=65537, \
    key_size=2048)
    return key

def publicKeyBytes(initial_key):
    public_key = initial_key.public_key().public_bytes(serialization.Encoding.OpenSSH, \
    serialization.PublicFormat.OpenSSH)
    return public_key

def bytesFromPublicKeyObj(public_key_obj):
    public_key = public_key_obj.public_bytes(serialization.Encoding.OpenSSH, \
    serialization.PublicFormat.OpenSSH)
    return public_key


def privateKeyBytes(initial_key):
    pem = initial_key.private_bytes(encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.TraditionalOpenSSL,
    encryption_algorithm=serialization.NoEncryption())
    return pem



def publicKeyFromBytes(public_key_bytes):
    loaded_public_key = serialization.load_ssh_public_key(
            public_key_bytes,
            backend=default_backend()
        )
    return loaded_public_key


def createMessageSignature(msg , key):
    signature = key.sign(
    msg,
    padding.PSS(
        mgf=padding.MGF1(hashes.SHA256()),
        salt_length=padding.PSS.MAX_LENGTH
    ),
    hashes.SHA256()
    )
    return signature

def signatureBytesToStr(signature_bytes):
    signature_b64 = base64.b64encode(signature_bytes)
    signature_str = signature_b64.decode('utf-8')
    return signature_str

def signatureStrToBytes(signature_str):
    signature_b64 = signature_str.encode('utf-8')
    signature_bytes = base64.b64decode(signature_b64)
    return signature_bytes


def verifyMessage(message ,  signature , public_key ):
    status = {'error_code' : 0 , 'message' : 'Verified successfully'}
    try:
        public_key.verify(
        signature,
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
        )
    except:
        exc_type, _ , _ = sys.exc_info()
        message = exc_type.__name__
        status['error_code'] , status['message']  = 1 , message    
    finally:        
        return status


def startBootstrapSocketServer(server_socket):
    while True:
        server_socket.accept()



    
    

