import socket

class UDP:
    
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.connect((host, port))
        
    def send(self, message):
        try:
            self.socket.send(str(message))
            #print "'%s' sent" % message
        except Exception, e:
            print e
    
    def close(self):
        self.socket.close()