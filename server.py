import serial
import zmq
import ujson
import heater_class as h
import diode_class as d
import lockin_class as l


heater_port = serial.Serial('/dev/heaters', timeout = 1 )
diode_port = serial.Serial('/dev/diode', timeout = 1 )
lockin_port =serial.Serial('/dev/lockins', timeout = 1 )


#dt670 = np.loadtxt('DT670.csv', delimiter =',', dtype=float)
#DC2018 = np.loadtxt('DC2018.csv', delimiter =',', dtype=float)
#ROX6951 = np.loadtxt('ROX6951.csv', delimiter =',', dtype=float)

#dt670_func = interp1d(dt670[:,1], dt670[:,0])
#dc2018_func = interp1d(DC2018[:,1], DC2018[:,0])
#rox6951_func = interp1d(ROX6951[:,1], ROX6951[:,0])

daq = zmq.Context()
daq_socket = daq.socket(zmq.REP)
daq_socket.bind("tcp://*:5555")


lockin_object = l.lockin(lockin_port)
diode_object = d.diode(diode_port)
heater_object = h.heater(heater_port)


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#Server
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
print('Server starting \n')

while True:

    message = daq_socket.recv()
    check = False
    if message == b'read all':
        check = True
        diode_data = diode_object.read()
        heater_data = heater_object.read()
        lockin_data = lockin_object.read_all()
        daq_socket.send_json(ujson.dumps( diode_data + heater_data + lockin_data ))
    message = message.split()
    print('Message Received', message)
    if (message[0].lower() == b'read' and len(message[1]) > 3):
        check = True
        if message[1].lower() == b'diode':
            
            daq_socket.send_json(ujson.dumps( diode_object.read() ))
            
        elif message[1].lower() == b'heater':
            
            daq_socket.send_json(ujson.dumps( heater_object.read() ))
            
        elif message[1].lower() == b'lockin':
            if len(message) > 2:
            
                daq_socket.send_json(ujson.dumps( lockin_object.read(message[2].decode(), message[3].decode() ) ))
            else:
                daq_socket.send_json(ujson.dumps( lockin_object.read_all() ))
        else:
            daq_socket.send_json(b'bad command') 
      
    #Heater Write      
    if message[0].lower() == b'lph':
        check = True
        heater_object.write(int(message[1]), int(message[2]), True)
        daq_socket.send_json(bytes('Setting LPH {0} {1}\r\n'.format(message[1], message[2]), encoding = 'utf-8'))
    if message[0].lower() == b'reset':
        check = True
        if type(message[1]) == int:
            heater_object.write(int(message[1]),'r' ,False)
            daq_socket.send_json(bytes('resetting HP {0}\r\n'.format(message[1]), encoding = 'utf-8'))
        elif message[1].lower() == b'all':
            heater_object.write('r', None, False)
            daq_socket.send_json(bytes('resetting All Hps', encoding = 'utf-8'))
    if message[0].lower() == b'i':
        check = True
        heater_object.write(int(message[1]), int(message[2]), False)
        daq_socket.send_json(bytes('Setting I {0} {1}\r\n'.format(message[1], message[2]), encoding = 'utf-8'))

    
    #Lockin Write
    if message[0].lower() == b'bias':
        check = True
        bias_state = lockin_object.write(int(message[1]))
        print(bytes('Bias {0} {1}\r\n'.format(message[1], bias_state), encoding = 'utf-8'))
        daq_socket.send_json(bytes('Bias {0} {1}\r\n'.format(message[1], bias_state), encoding = 'utf-8'))
    #if check == False:
        #daq_socket.send_json(b'bad command') 
        #these arn't in elif statments so this would run at the very end and attempt sending 
        #information when there was anever a request.....but if there's an error in the command sent, 
        #the server will break bc overall nothing is sent back when requested