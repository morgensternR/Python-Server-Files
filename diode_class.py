import ujson
class diode:
    def __init__(self, usb_port):
        self.port = usb_port
    def read(self, num = None):
        if num != None:
            string = f'v? {num}\r\n'
            self.port.write(bytes(string, 'utf-8'))
            
        else:
            self.port.write(bytes('v? 0\r\n', 'utf-8'))
        diode_data = ujson.loads(self.port.readline().decode().strip())
        #print(diode_data)
        return diode_data

