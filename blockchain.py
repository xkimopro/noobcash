from block import Block
import functions
import time, random,traceback

class blockchain:
    
    def __init__(self, ):
        self.block_list = []
        self.prev_time = time.time()
        self.time_to_add_new_block = []
    			
		
	
    def validate_blockchain():
        pass
		#calculate self.hash


    def add_block(self, new_block):
        new_time = time.time()
        self.time_to_add_new_block.append(new_time - self.prev_time)
        self.prev_time = new_time
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
	