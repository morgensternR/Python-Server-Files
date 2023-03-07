import time
import ujson

class heater:
    def __init__(self, usb_port):
        self.port = usb_port
    
    def read(self):
        heat_meas_dict = {}
        try:
            for i in range(4):
                string = f'mon? {i}\r\n'            
                self.port.write(bytes(string, 'utf-8'))
                temp_data = ujson.loads(self.port.readline())
                key, items = list(temp_data.items())[0]
                heat_meas_dict[key] = items
                time.sleep(0.1)
            for i in range(1,6):
                string = f'lph? {i}\r\n'
                self.port.write(bytes(string, 'utf-8'))
                temp_data = ujson.loads(self.port.readline())
                key, items = list(temp_data.items())[0]
                heat_meas_dict[key] = items
                time.sleep(0.1)
            time.sleep(0.1)
            return heat_meas_dict#element for nestedlist in heat_meas for element in nestedlist]
        except AttributeError:
            message= ujson.loads(self.port.readline())
            while message != dict:
                message= ujson.loads(self.port.readline())
                print(message)
      
    
    def write(self, channel, scale, LPH = False):
        if LPH == True:
            string = 'LPH {0} {1}\r\n'.format(channel, scale) #0-255 @ 4.5V supposed to be 5V...
            self.port.write(bytes(string, encoding='utf8'))
        elif LPH == False:
            if scale == 'r':
                string = 'reset {0}\r\n'.format(channel, scale)
                self.port.write(bytes(string, encoding='utf8'))
            elif channel == 'r':
                for i in range(4):
                    string = 'reset {0}\r\n'.format(i)
                    self.port.write(bytes(string, encoding='utf8'))
                    temp_data = self.port.readlines()
                return temp_data
            else:
                string = 'I {0} {1}\r\n'.format(channel, scale) #Easy scale 0-32 @ 200mV w/ 1ohm resistor
                self.port.write(bytes(string, encoding='utf8'))
        temp_data = self.port.readlines()
        return temp_data
