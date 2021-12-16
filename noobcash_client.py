#!/usr/bin/python3

import socket , json , os
from functions import *
from config import Config
from _thread import *


config = Config('config.json')

with socket.socket() as client_socket: 
    print('Client started')
    print('Trying to connect to socket server')
    try:
        client_socket.connect((config.bootstrap_node_ip, config.bootstrap_node_port))
    except socket.error as e:
        print(str(e))
        quit()
    print('Connected')

    response = client_socket.recv(1024)
    while True:
        Input = input('Say Something: ')
        client_socket.send(str.encode(Input))
        response = client_socket.recv(1024)
        print(response.decode('utf-8'))