#%%
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#Logger
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

import zmq 
import ujson
from datetime import date
import time
import csv


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
config = ujson.load(open('diode_config.json', 'r'))
file = open("thermometry_log_{0}.csv".format(date.today(), encoding = 'utf-8'), "a")

with file as csvfile:
    fieldnames = ['TIME']
    for key in config['sensors']:
        fieldnames.append(key)
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    #Run True: Pull Data, Add time stamp to data, Publish data, write data to csv
    while True:
        data = ujson.loads(send_n_receive(b'read diode'))
        data[fieldnames[0]] = time.time()
        #Can't send jsons easily with pub/sub
        Log_Pub_socket.send_string(topic + ' ' +ujson.dumps((data)) )
        #Log_Pub_socket.send_json((topic, data)) This doesnt work
        writer.writerow(data)
        file.flush()
        time.sleep(10)
