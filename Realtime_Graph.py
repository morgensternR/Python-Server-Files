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
from PyQt5.QtWidgets import QApplication, QWIDGETSIZE_MAX
from pyqtgraph.Point import Point
import pyqtgraph as pg
import pandas
from scipy.interpolate import interp1d

# Make Subscriber to Publisher with 'graph' set topic...       
def receive_data(socket, topicfilter):
    return ujson.loads(socket.recv().decode().split(topicfilter)[1].strip()) 
print('Starting SUB Socket')
port = "5556"
context = zmq.Context()
socket = context.socket(zmq.SUB)   
socket.RCVTIMEO = -1
socket.connect('tcp://132.163.53.82:%s' %port)
topicfilter = 'graph'
socket.setsockopt_string(zmq.SUBSCRIBE, topicfilter)

# Start QtGui application
print('Starting Plotting Window')
app = QtGui.QApplication([])

# Window formatting
win = pg.GraphicsLayoutWidget(show=True, title="Thermometry Plotter")
win.resize(1000,1000)
win.setWindowTitle('Thermometry Realtime Plotter')
label = pg.LabelItem(justify='right')
win.addItem(label)

# Enable antialiasing for prettier plots
pg.setConfigOptions(antialias=True)

# Plot labeling
p0 = win.addPlot(title="Thermometry Realtime + Log")
p0.showGrid(x = True, y = True)
p0.setLabel('left', 'Temperature (K)')
date_axis = pg.DateAxisItem(orientation='bottom')
p0.setAxisItems(({'bottom': date_axis}) )
p0.setLabel('bottom', 'Date and Time (test)')
p0.addLegend()

# Import log file and calibration files. Change directory Here
print('Importing current Log File')
log_file = pandas.read_csv('L:/ryan_python/Python_Server_Logger/thermometry_log.csv')
print('Importing Calibration Files')
dc2018 = np.loadtxt('L:/ryan_python/DC2018.csv',  delimiter =',', dtype=float)
dt670 = np.loadtxt('L:/ryan_python/DT670.csv',  delimiter =',', dtype=float)
dt670_func = interp1d(dt670[:,1], dt670[:,0])
dc2018_func = interp1d(dc2018[:,1], dc2018[:,0])

def init(log_file):
    curves = {}
    color_map = get_cmap('hsv', len(log_file.keys()) - 1)
    idx = 0
    for key in log_file:
        if key != 'TIME':
            color = tuple((np.array(color_map(idx))*255).astype(int))
            if key == '4K' or key == '40K':
                curves[key] = p0.plot(log_file['TIME'], dt670_func(log_file[key]), name = key, pen = color)#, symbol = 'o', symbolSize = 1)
            else:
                curves[key] = p0.plot(log_file['TIME'], dc2018_func(log_file[key]), name = key, pen = color)#, symbol = 'o' , symbolSize = 1)
            idx += 1
    p0.enableAutoRange('xy', False)
    return curves


#Making curve dictionary with sensor keys and plot values
print('Plotting current Log file')
curves = init(log_file)

def update(data):
    global curves 
    if data is not None:
        for key in curves:
            curve = curves[key]
            if key == '4K' or key == '40K':
                x, y = np.append(curve.getData()[0], data['TIME']), np.append(curve.getData()[1], dt670_func(data[key]))
            else:
                x, y = np.append(curve.getData()[0], data['TIME']), np.append(curve.getData()[1], dc2018_func(data[key]))
            
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


#cross hair
vLine = pg.InfiniteLine(angle=90, movable=False)
hLine = pg.InfiniteLine(angle=0, movable=False)
p0.addItem(vLine, ignoreBounds=True)
p0.addItem(hLine, ignoreBounds=True)


vb = p0.vb

def mouseMoved(evt):
    global curves
    pos = evt[0]  ## using signal proxy turns original arguments into a tuple
    if p0.sceneBoundingRect().contains(pos):
        mousePoint = vb.mapSceneToView(pos)
        vLine.setPos(mousePoint.x())
        hLine.setPos(mousePoint.y())
proxy = pg.SignalProxy(p0.scene().sigMouseMoved, rateLimit=60, slot=mouseMoved)



if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_() #Starts own thread for GUI


