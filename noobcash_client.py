#!/usr/bin/python3

import socket , json , os
from functions import *
from config import Config
from _thread import *
from messaging import *







config = Config('config.json')

with socket.socket() as client_socket: 
    attemptBootstrapConnection(client_socket, config)
    greeting = client_socket.recv(1024)
    messaging = Messaging(client_socket)
    m = messaging.parseToMessage(greeting)    
    if m.isServerGreetingClient():
        inform("Greeted by bootstrap node. Replying...")
        messaging.clientReplyToGreeting()

    else:
        exitNoobcash(2,"There is no bootstrap node on the other end of the socket")

    
    inform("Waiting for assignment phase. Waiting for bootstrap to share credentials...")
    while True:
        # Input = input('Say Something: ')
        # client_socket.send(str.encode(Input))
        response = client_socket.recv(1024)
        m = messaging.parseToMessage(response)
        if m.isStartAssignmentPhase():
            inform("Bootstrap node initiated assignment phase")
            messaging.startAssignmentPhaseAck()
            config.client_node_ip , config.client_node_port = client_socket.getsockname()
            print(config.client_node_port)
        
        # print(response.decode('utf-8'))