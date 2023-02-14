#%%
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#Real time graphing and Subscriber
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
import time
import numpy as np
from matplotlib.cm import get_cmap
import matplotlib.dates as mdates
import zmq
import ujson
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import pandas


def receive_data(socket, topicfilter):
    return ujson.loads(socket.recv().decode().split(topicfilter)[1].strip()) 

# Make Subscriber to Publisher with 'graph' set topic...

print('Starting SUB Socket')
port = "5556"
context = zmq.Context()
socket = context.socket(zmq.SUB)   
socket.RCVTIMEO = -1
socket.connect('tcp://132.163.53.82:%s' %port)
topicfilter = 'graph'
socket.setsockopt_string(zmq.SUBSCRIBE, topicfilter)

print('Starting Plotting Window')
app = QtGui.QApplication([])
win = pg.GraphicsLayoutWidget(show=True, title="Basic plotting examples")
win.resize(1000,600)
win.setWindowTitle('pyqtgraph example: Plotting')
# Enable antialiasing for prettier plots
pg.setConfigOptions(antialias=True)
p6 = win.addPlot(title="Updating plot")
p6.addLegend()

sensor_data = receive_data(socket, topicfilter)
print('Importing current Log File')
log_file = pandas.read_csv('L:/ryan_python/Python_Server_Logger/thermometry_log.csv')


def init(log_file):
    curves = {}
    color_map = get_cmap('hsv', len(sensor_data) - 1)
    idx = 0
    for key in log_file:
        if key != 'TIME':
            curves[key] = p6.plot(log_file['TIME'], log_file[key], name = key, pen = (np.array(color_map(idx))*255).astype(int) )
            idx += 1
    p6.enableAutoRange('xy', True)
    return curves

#Making curve dictionary with sensor keys and plot values
print('Plotting current Log file')
curves = init(log_file)

def update(data):
    global curves 
    '''
    try:
        title, data = demogrify(socket.recv())
    except:
        data = None
    '''    
    if data is not None:
        for key in curves:
            curve = curves[key]
            x, y = np.append(curve.getData()[0], data['TIME']), np.append(curve.getData()[1], data[key])
        
            curve.setData(x,y)
    

## Start Qt event loop unless running in interactive mode or using pyside.
class get_data_thread(pg.QtCore.QThread): #Starts QThread for data polling
    newData = pg.QtCore.Signal(dict) #Defines signal data type
    def run(self):
        while True:
            sensor_data = receive_data(socket, topicfilter)
            # do NOT plot data from here!
            self.newData.emit(sensor_data) #Emits signal to new.connect(slot)
            
data_getter = get_data_thread()
data_getter.newData.connect(update) #Emits signal to update slot
data_getter.start()#Starts thread

if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_() #Starts own thread for GUI


