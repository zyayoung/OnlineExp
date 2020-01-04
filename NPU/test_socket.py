import socket
ip_port = ('0.0.0.0',3456)
sk = socket.socket()
sk.bind(ip_port)
sk.listen(5)

while True:
    print ('server waiting...')
    conn,addr = sk.accept()
    client_data = conn.recv(1024)
    print (str(client_data,'utf8'))
    conn.sendall(b'hello')
    conn.close()
