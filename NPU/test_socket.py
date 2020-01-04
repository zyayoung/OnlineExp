'''
    Simple socket server using threads
'''

import socket
import sys
from threading import *
from urllib.request import urlopen

import numpy as np

HOST = '0.0.0.0'    # Symbolic name meaning all available interfaces
PORT = 3456    # Arbitrary non-privileged port
MASTER_URL = "http://127.0.0.1:8000/exp/add"

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print('Socket created')

#Bind socket to local host and port
s.bind((HOST, PORT))
    
print('Socket bind complete')

#Start listening on socket
s.listen(10)
print('Socket now listening')

#Function for handling connections. This will be used to create threads
def clientthread(conn):
    #Sending message to connected client
    # conn.send('Welcome to the server. Type something and hit enter\n') #send only takes string
    
    #infinite loop so that function do not terminate and thread do not end.
    name = conn.recv(10240).decode()
    print(f"Name: {name}")
    while True:
        
        #Receiving from client
        data = conn.recv(10240)
        data = np.frombuffer(data, dtype=np.uint8).reshape(-1, 5)
        for d in data:
            url = f"{MASTER_URL}?slave_name={name}&trk_id={d[0]}&x={d[1]}&y={d[2]}&w={d[3]}&h={d[4]}"
            upload_thread = Thread(target=urlopen, args=(url,), daemon=True)
            upload_thread.start()
        print(data)
    
        # conn.sendall(reply)
    
    #came out of loop
    conn.close()

try:
    #now keep talking with the client
    while 1:
        #wait to accept a connection - blocking call
        conn, addr = s.accept()
        print('Connected with ' + addr[0] + ':' + str(addr[1]))
        
        #start new thread takes 1st argument as a function name to be run, second is the tuple of arguments to the function.
        t = Thread(target=clientthread, args=(conn,), daemon=True)
        t.start()
except KeyboardInterrupt:
    s.close()