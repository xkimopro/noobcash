import os,re,socket,json

from config import Config 
import threading


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
        client_socket.connect((config.bootstrap_node_ip, config.bootstrap_node_port))
    except socket.error as e:
        client_socket.close()
        exitNoobcash(1, "Cannot connect to bootstrap node at {}:{}".format(config.bootstrap_node_ip , config.bootstrap_node_port) )
    inform(f"Connected through TCP at {config.bootstrap_node_ip}:{config.bootstrap_node_port}")


