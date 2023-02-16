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
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
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
#pg.setConfigOptions(useOpenGL=True) #Tried adding this line to fix FPS issue WRT line width. Didn't help. Also disables antialiasing 


# Window formatting
win = pg.GraphicsLayoutWidget(show=True, title="Thermometry Plotter")
win.resize(1000,1000)
win.setWindowTitle('Thermometry Realtime Plotter')

# Enable antialiasing for prettier plots
pg.setConfigOptions(antialias=True)

# Plot labeling
p0 = win.addPlot(title="Thermometry Realtime + Log", row = 0, col = 0)
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
    line_width = 1 #1 is default, Anything bigger than 1 causes massive FPS issues https://github.com/pyqtgraph/pyqtgraph/issues/533
    for key in log_file:
        if key != 'TIME':
            color = tuple((np.array(color_map(idx))*255).astype(int))
            if key == '4K' or key == '40K':
                curves[key] = p0.plot(log_file['TIME'], dt670_func(log_file[key]), name = key, pen = {'color': color, 'width' : line_width} )#, symbol = 'o', symbolSize = 1)
            else:
                curves[key] = p0.plot(log_file['TIME'], dc2018_func(log_file[key]), name = key, pen = {'color': color, 'width' : line_width} )#, symbol = 'o' , symbolSize = 1)
            idx += 1
    p0.enableAutoRange('xy', False)
    return curves


#Making curve dictionary with sensor keys and plot values
print('Plotting current Log file')
curves = init(log_file)


# create a QGraphicsProxy Widget so we can add it to the plots
#   It will contain a widget with a bunch of labels and a button
proxy = QtWidgets.QGraphicsProxyWidget()

# create a widget (w) that will be actual contain all the labels and buttons
w = QtWidgets.QWidget()
# create a layout for the widget
layout = QtWidgets.QGridLayout()
w.setLayout(layout)
# create button and labels... add them to w
button = QtWidgets.QPushButton('button')
labels_dict = {}
for key in curves:# 
    label = QtWidgets.QLabel(f'{key}:')
    labels_dict[key] = label

layout.addWidget(button, 0, 0)
row = 1
for label in labels_dict:
    layout.addWidget(labels_dict[label], row, 0)
    row = row+1
# Set proxy to be the widget w
proxy.setWidget(w)
# add proxy widget to graphics layout widget
p1 = win.addItem(proxy)




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
p0.addItem(vLine, ignoreBounds=True)
vb = p0.vb

def find_largest_index_less_than(data, x_value):
    try:
        indices = np.where(data<x_value)[0]
        array_data_values_less_than_5 = data[indices]
        index_of_largest_Value = array_data_values_less_than_5.argmax()
        index_of_largest_Value_in_OG_Data = indices[index_of_largest_Value]
        return index_of_largest_Value_in_OG_Data
    except:
        return len(data)-1



def mouseMoved(evt):
    global curves, labels
    pos = evt[0]  ## using signal proxy turns original arguments into a tuple
    if p0.sceneBoundingRect().contains(pos):
        mousePoint = vb.mapSceneToView(pos)
        index = find_largest_index_less_than(curves['4K'].getData()[0], mousePoint.x())
        x_value = curves['4K'].getData()[0][index]
        
        for label in labels_dict:
            y_value = curves[label].getData()[1][index]
            labels_dict[label].setText(f"{label}: {y_value:.2f} ")
        vLine.setPos(x_value)
        
proxy = pg.SignalProxy(p0.scene().sigMouseMoved, rateLimit=60, slot=mouseMoved)




if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_() #Starts own thread for GUI



