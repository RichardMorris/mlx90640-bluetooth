# Uses Bluez for Linux
#
# sudo apt-get install bluez python-bluez
# 
# Taken from: https://people.csail.mit.edu/albert/bluez-intro/x232.html
# Taken from: https://people.csail.mit.edu/albert/bluez-intro/c212.html

import bluetooth
import sys,struct,time
sys.path.insert(0, "/home/pi/mlx90640-library-master/python/build/lib.linux-armv7l-2.7")

import MLX90640 as mlx

yogaMac = 'B0:FC:36:D0:2F:E0'
client_sock = ''
server_sock = ''

def setupSocketServer():
  global client_sock, server_sock, port, address
  print "seting up socket"
  server_sock=bluetooth.BluetoothSocket( bluetooth.RFCOMM )
  
  port = 1
  server_sock.bind(("",port))

def listernSocket():
  global client_sock, server_sock, port, address
  server_sock.listen(1)
  
  client_sock,address = server_sock.accept()
  print "Accepted connection from " + str(address)
  

def closeSocket():
  global client_sock, server_sock, port, address
  client_sock.close()
  server_sock.close()
  
def sendMessageTo(targetBluetoothMacAddress):
  port = 1
  sock=bluetooth.BluetoothSocket( bluetooth.RFCOMM )
  sock.connect((targetBluetoothMacAddress, port))
  sock.send("hello!!")
  sock.close()
  
def lookUpNearbyBluetoothDevices():
  nearby_devices = bluetooth.discover_devices()
  for bdaddr in nearby_devices:
    print str(bluetooth.lookup_name( bdaddr )) + " [" + str(bdaddr) + "]"
    
def setupMLX():    
  global mlx
  mlx.setup(16)

frameNo=0;

def readAndSendFrame():
    global mlx,server_sock
    t0 = time.clock()*1000
    frame = mlx.get_frame()
    t1 = time.clock()*1000
    v_min = min(frame)
    v_max = max(frame)
    print("min %.1f max %.1f" % (v_min,v_max),"frame",int(t1-t0))
    ss=""
#    client_sock.send("B")
    for xh in range(0,32,16):
        t2 = time.clock()*1000
        ba = bytearray()
        for xl in range(0,16):
            x = xh + xl
            for y in range(24):
                val = frame[32*(23-y) + x]
#            s = "D {:2d} {:2d} {:3.1f}".format(x,y,val)
                s = "%4.1f" % val
                ss = ss + s
                sh = int(val*100)
                if sh>32767: sh = 32767
                if sh<-32768: sh = -32768
                ba.extend(struct.pack("h",sh))
       # print ss
        t3 = time.clock()*1000
        client_sock.send(bytes(ba))
        t4 = time.clock()*1000
        print("build data",int(t3-t2),"send",int(t4-t3))


def mainLoop():
    global client_sock, server_sock, port, address
    try:
        while 1:
            data = client_sock.recv(1024)
            print "Request", data
            readAndSendFrame()
    except:
        e = sys.exc_info()
        print "Error"
        print e
        server_sock.close()
        client_sock.close()
        setupSocketServer()
        listernSocket()
        mainLoop()

setupMLX()
setupSocketServer()
listernSocket()
mainLoop()
