# Uses Bluez for Linux
#
# sudo apt-get install bluez python-bluez
# 
# Taken from: https://people.csail.mit.edu/albert/bluez-intro/x232.html
# Taken from: https://people.csail.mit.edu/albert/bluez-intro/c212.html

import bluetooth
import sys,time

# assumes the https://github.com/pimoroni/mlx90640-library is installed in the pi home directory 
sys.path.insert(0, "/home/pi/mlx90640-library-master/python/build/lib.linux-armv7l-2.7")
import MLX90640 as mlx

client_sock = '' 
server_sock = ''
frameNo=0;

# setup Bluetooth socket
def setupSocketServer():
  global client_sock, server_sock, channel, address
  print( "Setting up socket")
  server_sock=bluetooth.BluetoothSocket( bluetooth.RFCOMM )
  channel = 1
  server_sock.bind(("",channel))

# listen on Bluetooth socket
def listernSocket():
  global client_sock, server_sock, channel, address
  server_sock.listen(1)
  client_sock,address = server_sock.accept()
  print ("Accepted connection from " + str(address))

# close Bluetooth socket
def closeSocket():
  global client_sock, server_sock, channel, address
  client_sock.close()
  server_sock.close()

# Setup the MLX device
def setupMLX():    
  global mlx
  mlx.setup(16) # Parameter is the fps, either 1, 2, 4, 8, 16, 32 or 64

# Read a frame from the mlx sensor and send it down the socket
# each pixel is first converted to a 2-byte short int by multiply temperature
# value by 100. This looses some of the top end of the servers range which
# is effectively -327.68 to 327.67.
# The bytes are send in two blocks of 16*24 pixels, so each block is 768 bytes
# This seems to be a size which can be written in one chunk at a time 
# so the client can read a specific number of bytes
def readAndSendFrame():
    global mlx,server_sock
    t0 = time.clock()*1000
    frame = mlx.get_frame()
    t1 = time.clock()*1000
    #v_min = min(frame)
    #v_max = max(frame)
    #print("min %.1f max %.1f" % (v_min,v_max),"frame",int(t1-t0))
    ss=""
    for xh in range(0,32,16):
        t2 = time.clock()*1000
        ba = bytearray()
        for xl in range(0,16):
            x = xh + xl
            for y in range(24):
                val = frame[32*(23-y) + x]
                sh = int(val*100)
                if sh>32767: sh = 32767
                if sh<-32768: sh = -32768
                ba.extend(struct.pack("h",sh))
        t3 = time.clock()*1000
        client_sock.send(bytes(ba))
        t4 = time.clock()*1000
        #print("build data",int(t3-t2),"send",int(t4-t3))

# The main loop waits for some data from the client, which is ignored.
# It then sends a frame of data
def mainLoop():
    global client_sock, server_sock, channel, address
    try:
        while 1:
            data = client_sock.recv(1024)
            print( "Request", data)
            readAndSendFrame()
    except:
        e = sys.exc_info()
        print ("Error")
        print (e)
        server_sock.close()
        client_sock.close()
        setupSocketServer()
        listernSocket()
        mainLoop()

setupMLX()
setupSocketServer()
listernSocket()
mainLoop()
