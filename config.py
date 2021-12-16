import json

class Config:

    
    nodes = 5
    localnet = False
    block_capacity = 10
    noobcash_ports_range = [44440,44450]
    bootstrap_node_port = 44440
    bootstrap_node_ip = "127.0.0.1"
    
    def __init__(self, json_file="config.json"):
        self.json_file = json_file
        self.parse_file()


    def parse_file(self,):
        with open(self.json_file, "r") as f:
            data = json.load(f)
            self.nodes = data['nodes']
            self.localnet = data['localnet']
            self.block_capacity = data['block_capacity']
            self.noobcash_ports_range = data['noobcash_ports_range']
            self.bootstrap_node_port = data['bootstrap_node_port']
            self.bootstrap_node_ip = data['bootstrap_node_ip']
