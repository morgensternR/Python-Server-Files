#%%
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#Real time graphing and Subscriber
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib.dates as mdates
import zmq
import ujson

def demogrify(topicmsg):
    """ Inverse of mogrify() """
    topicmsg = topicmsg.decode()
    json0 = topicmsg.find('{')
    topic = topicmsg[0:json0].strip()
    msg = ujson.loads(topicmsg[json0:])
    return topic, msg 

# Make Subscriber to Publisher with 'graph' set topic...

port = "5556"
context = zmq.Context()
socket = context.socket(zmq.SUB)   
socket.connect('tcp://132.163.53.82:%s' %port)
topicfilter = "graph"
socket.setsockopt_string(zmq.SUBSCRIBE, topicfilter)


# Create figure for plotting
fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)
topic, messagedata = demogrify(socket.recv())



sensors_list = {}
for key in messagedata:
    if key not in 'TIME':
        sensors_list[key] = []   
xs = []
# This function is called periodically from FuncAnimation

def animate(i, xs, sensor_list, pts):
    #loops in while till new data
    topic, messagedata = demogrify(socket.recv())
    
    # Add x and y to lists
    xs.append(mdates.epoch2num(messagedata['TIME']))
    xs = xs[-pts:]
    ax.clear()
    
    
    for key in messagedata:
        
        if key not in 'TIME':
            
            sensor_list[key].append(messagedata[key])
            sensor_list[key] = sensor_list[key][-pts:]
            line = ax.plot_date(xs, sensor_list[key], linestyle = '--', label = key)
        else:
            pass
        
    #print(sensor_list)
    # Draw x and y lists
    
    #line = ax.plot_date(xs, ys)

# Format plot
    # Choose your xtick format string
    date_fmt = '%d-%m-%y %H:%M:%S'
    
    # Use a DateFormatter to set the data to the correct format.
    date_formatter = mdates.DateFormatter(date_fmt)
    ax.xaxis.set_major_formatter(date_formatter)
    
    # Sets the tick labels diagonal so they fit easier.
    fig.autofmt_xdate()

    plt.title('Diode Sensor Data')
    plt.ylabel('Voltage (V)')
    ax.grid()
    ax.legend(bbox_to_anchor=(1.01, 1.0), loc='upper left')
    return #line

# Set up plot to call animate() function periodically
ani = FuncAnimation(fig, animate, fargs=(xs, sensors_list, 1000), interval=10000, blit=False)

plt.show()
