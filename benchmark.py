from functions import *
import time, random,traceback

class Benchmark:
    def __init__(self,node,start_time):
        self.start_time = start_time
        self.node = node
        # self.num_of_nodes = num_of_nodes
        
     
    

    def start(self):
        time.sleep(6)
        file_name = "transactions" + str(self.node.id) + ".txt"
        path = './transactions/10nodes/' + file_name 

        # if self.num_of_nodes == '10':
        #     path = './transactions/10nodes/' + file_name
        # else: 
        #     path = './transactions/5nodes/' + file_name 
        with open(path, 'r') as File:
            Lines = File.readlines()
            time.sleep(int(self.node.id)+1)
            for line in Lines:
                input = line.split()
                amount = int(input[1])
                id = int(input[0][2])
                try:
                    self.node.mutex.acquire()
                    while self.node.all_false() == False:
                        if self.node.conflict_occured[self.node.id] == True:
                            time_temp = time.time()
                            if time_temp - self.node.time > 30:
                                self.node.resolve_conflicts()
                        time.sleep(0.25)
                    print("now to issue",self.node.conflict_occured)
                    print("Issuing transaction from benchmark thread")
                    self.node.create_transaction(id, amount)
                    # stdout_print("Transaction validated")
                    # test = self.node.timestamp - self.start_time
                    # stdout_print(test)
                    
                except Exception as e:
                    stdout_print(str(e))
                    stdout_print(traceback.format_exc())
                    self.node.mutex.release()
                time.sleep(float(random.randint(0,15000))/float(1000))
                # while self.node.resolving_confilct:
                #     time.sleep(0.25)
                
          
            throughput_time = self.node.timestamp - self.start_time
            completed_trans = self.node.transactions
            stdout_print("FINISHED MY TRANSACTIONS!!!")
            stdout_print(self.node.time_to_add_new_block)
            stdout_print(throughput_time)
            stdout_print(completed_trans)

            
        

    