from functions import *
import time, random

class Benchmark:
    def __init__(self,node,start_time ):
        self.start_time = start_time
        self.node = node
        
     
    def start(self):
        time.sleep(6)
        file_name = "transactions" + str(self.node.id) + ".txt"
        path = './transactions/5nodes/' + file_name 
        with open(path, 'r') as File:
            Lines = File.readlines()
            for line in Lines:
                input = line.split()
                amount = int(input[1])
                id = int(input[0][2])
                time.sleep(0.1)
                try:
                    self.node.mutex.acquire()
                    self.node.create_transaction(id, amount)
                    stdout_print("Transaction validated")
                    
                except Exception as e:
                    stdout_print(str(e))
                    self.node.mutex.release()
                
                time.sleep(float(random.randint(250,500))/float(1000))
                                
            throughput_time = self.node.timestamp - self.start_time
            completed_trans = self.node.transactions
            # stdout_print(throughput_time)
            # stdout_print(completed_trans)
            
        

    