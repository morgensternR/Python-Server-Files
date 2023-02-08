import time

class lockin:
    def __init__(self, usb_port, lockin_count = 4):
        
        self.port = usb_port
        self.lockin_count = range(lockin_count, 8)
        
    def RDSSS(self):
        return self.port.readline().decode().strip().strip('"').strip('\\n')

    def read(self, channel, command):
        #print(command)
        if type(command) != str: 
            print("Proper commands must be string")
            return
        for retry in range(3):
            self.port.flushInput()
            self.port.write(bytes('NAME? {0}\r\n'.format(channel), encoding = 'utf-8'))
            #time.sleep(0.1)
            
            self.RDSSS()#supposed to be echo junk- 
            #Edit Don't need to store it in a varaible, reads junk line to move onto next line
            response = self.RDSSS()
            #print(response)
            #Typically the line of importance to check
            #if blank -> wait longer
            #if traceback -> reload program
            #if lockin check - > cont
            
            #if response == '':
                #time.sleep(3)
                #response = self.RDSSS()
            while_time = time.time()    
            while response == '':
                response = self.RDSSS()  
                if while_time - time.time() > 10:
                    print("it's hanging")
                    break
            if response == 'Traceback (most recent call last):':
                print("importing")
                self.port.write(bytes('import lockin_mux\r\n', encoding = 'utf-8'))
                time.sleep(2)
            data_back = None    
        
            if response == 'lockin {0}'.format(channel):
                #print("comfirmed port")
                self.port.write(bytes('{0} {1}\r\n'.format(command,channel), encoding = 'utf-8'))
                self.RDSSS() #z = RDSSS(self.port)#Supposed to be echo Junk
                data_back = self.RDSSS()
                while data_back == '':
                    data_back = self.RDSSS() 
                    
            if data_back != None and data_back != 'lockin {0}'.format(channel):
                #print('made bad data_back check')
                return data_back#, response
            
            #print('resetting')
            #self.port.write(b'reset')
            #time.sleep(1)
            
        return print("this shit broke")
    
    def write(self, channel = None, command = 'BIAS', value = None):
        
        if (command.upper() == 'BIAS' and value == None):
            bias_state = not int(self.read(channel, 'bias?'))
            self.port.write(bytes('{0} {1} {2}\r\n'.format(command, channel, int(bias_state)), encoding = 'utf-8'))
            return int(bias_state)
        
        self.port.write(bytes('{0} {1} {2}\r\n'.format(command, channel, value), encoding = 'utf-8')) #not sure yet what else I'd care to send
        return int(bias_state)
    
    def read_all(self, command = 'r?'):
        data = []
        for i in self.lockin_count:
            data.append(self.read(i, command))
        return data
    def write_all_bias(self):
        for i in self.lockin_count:
            self.write(self.lockin_count)
            