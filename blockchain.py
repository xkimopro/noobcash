from block import Block
import functions
import time, random,traceback

class blockchain:
    
    def __init__(self, ):
        self.block_list = []

    def add_block(self, new_block):
        self.block_list.append(new_block)        

    
    def print_blockchain(self,):
        for block in self.block_list:
            print(block)
            print("\n\n")
            
    def get_latest_blocks_hash(self,):
        latest_block = self.block_list[-1]
        return latest_block.current_hash
            
    def get_latest_blocks_index(self,):
        latest_block = self.block_list[-1]
        return latest_block.index
	