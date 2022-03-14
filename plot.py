import zmq
import time
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as a

# create the zmq client and listen on port 1234
socket = zmq.Context(zmq.REP).socket(zmq.SUB)
socket.setsockopt_string(zmq.SUBSCRIBE, '')
socket.connect('tcp://127.0.0.1:8899')

# n_animals, females, plants, sense, stamina                
df = np.array([[0, 0, 0, 0, 0]])

# create plot
plt.ion() # <-- work in "interactive mode"
fig, ax = plt.subplots(ncols=2, nrows=2)

while True:
    arr = socket.recv_pyobj()
    df = np.vstack((df, arr))

    ax[0][0].plot(df[1:, 0], color='black')
    ax[0][0].plot(df[1:, 1], color='gray')
    ax[0][0].set_ylabel('population / female population')

    ax[0][1].plot(df[1:, 2], color='limegreen') 
    ax[0][1].set_ylabel('vegetation')
    
    ax[1][0].plot(df[1:, 3], color='tomato')
    ax[1][0].set_ylabel('average sense')
    
    ax[1][1].plot(df[1:, 4], color='royalblue')
    ax[1][1].set_ylabel('average stamina')
    
    # if len(df) > 50:
    #     df = df[1:]

    plt.tight_layout()
    plt.show()
    plt.pause(1) # <-- sets the current plot until refreshed

    # time.sleep(.1)