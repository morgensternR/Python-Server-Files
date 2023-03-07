#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#Logger
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

import zmq 
import ujson
from datetime import date
import time
import csv
import os

# Socket to talk to Server
Logger = zmq.Context()
logging_socket = Logger.socket(zmq.REQ)
logging_socket.connect("tcp://localhost:5555")        
def send_n_receive(message):    
    logging_socket.send(bytes(message))
    return logging_socket.recv_json()

# Socket to start Publisher  
port = "5556"
Logger_Publisher = zmq.Context()
Log_Pub_socket = Logger_Publisher.socket(zmq.PUB)
Log_Pub_socket.bind("tcp://132.163.53.82:%s" % port)#address to linux box
topic = 'graph'

# Read config json (diode in this case), build csv with header
config_diode = ujson.load(open('diode_config.json', 'r'))
config_heater = ujson.loads(open('heater_config.json', 'r'))

file = open("thermometry_log.csv", "a")

with file as csvfile:
    fieldnames = ['TIME']
    for key in config_diode['sensors']:
        fieldnames.append(key)
    for key in config_heater['heaters']:
        fieldnames.append(key)
        
    if os.stat("thermometry_log.csv").st_size == 0:
        print('Data log is empty, Creating Header \n' )
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
    else:
        print('Data log is Not empty, Just appending \n')
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    #Run True: Pull Data, Add time stamp to data, Publish data, write data to csv
    while True:
        data = ujson.loads(send_n_receive(b'read all'))
        data[fieldnames[0]] = time.time()
        #Can't send jsons easily with pub/sub
        Log_Pub_socket.send_string(topic + ' ' +ujson.dumps((data)) )
        #Log_Pub_socket.send_json((topic, data)) This doesnt work
        writer.writerow(data)
        file.flush()
        time.sleep(10)
