import sys,math,time,struct
import tkinter as tk
import bluetooth,socket
import time
from datetime import datetime

# mac address for server
piMac = 'B8:27:EB:B1:D2:E5'

# number of pixels per sensor pixel
IMAGE_SCALE=16

# Size of data block
BLOCK_SIZE=24*16*2
# colours for interpolation
NUM_COLORS = 7
color = [ [0,0,0], [0,0,1], [0,1,0], [1,1,0], [1,0,0], [1,0,1], [1,1,1]]

# min and max for temperature range 
min_temp = 5.0
max_temp = 50.0

# bins for recording histogram
bins = [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0]

# mouse coordinated for pixel sampling
mouse_x = -1
mouse_y = -1

# time of last frame 
last_time = time.perf_counter_ns()//1000000

# number of current frame for plotting
pageNo = 1
# tag of current page for plotting
currentTag = "page1"

# mouse click stores position for sampling
def mouseClick(event):
	global mouse_x,mouse_y
	print("mouse",event.x,event.y)
	mouse_x = event.x
	mouse_y = event.y

# set bounds for temperature range
def setBounds():
	global min_temp,max_temp,minVar,maxVar
	min_temp = minVar.get()
	max_temp = maxVar.get()

# Build the UI
def setupUI():
	global mw,c,mirrorFlag,tk,sampleValue,minVar,maxVar,min_temp,max_temp

	mw = tk.Tk()
	mw.title('infrared camera sensor')

	sampleValue = tk.DoubleVar()

	minVar = tk.DoubleVar()
	minVar.set(min_temp)
	
	maxVar = tk.DoubleVar()
	maxVar.set(max_temp)
	mirrorFlag = tk.BooleanVar()

	c = tk.Canvas(mw,width=1024,height=384)
	c.pack(side=tk.TOP,fill=tk.BOTH,expand=1)
	c.bind("<Button-1>",mouseClick)

	frm = tk.Frame()
	frm.pack()

	tk.Label(frm,text="Temp").pack(side=tk.LEFT)
	tf0 = tk.Entry(frm,width=10,textvariable = sampleValue)
	tf0.pack(side=tk.LEFT)

	tk.Label(frm,text="Min").pack(side=tk.LEFT)
	tf1 = tk.Entry(frm,width=10,textvariable=minVar)
	tf1.pack(side=tk.LEFT)

	tk.Label(frm,text="Max").pack(side=tk.LEFT)
	tf2 = tk.Entry(frm,width=10,textvariable=maxVar)
	tf2.pack(side=tk.LEFT)
	
	setBut = tk.Button(frm,text='Set', command=setBounds)
	setBut.pack(side=tk.LEFT,padx=5)

	C1 = tk.Checkbutton(frm, text = "Mirror", variable = mirrorFlag, onvalue = True, offvalue = False)
	C1.pack(side=tk.LEFT)

	close = tk.Button(frm,text='Quit', command=shutdown)
	close.pack(side=tk.LEFT)

# Find the colour for a specific value
# Heatmap code borrowed from: http://www.andrewnoske.com/wiki/Code_-_heatmaps_and_color_gradients
# Returns the tuple ( hex value for colour in format #ff00ff, red int value, green int value, blue int value) 
def getColour(val):
	fractBetween = 0;
	vmin = min_temp;
	vmax = max_temp;
	v =  (val -vmin)/(vmax - vmin);
	if(v <= 0):
		idx1=idx2=0
	elif(v >= 1):
		idx1=idx2=NUM_COLORS-1
	else:
		v = v * (NUM_COLORS-1);
		idx1 = math.floor(v);
		idx2 = idx1+1;
		fractBetween = v - float(idx1);
		
	ir = int((( (color[idx2][0] - color[idx1][0]) * fractBetween) + color[idx1][0]) * 255.0);
	ig = int((( (color[idx2][1] - color[idx1][1]) * fractBetween) + color[idx1][1]) * 255.0);
	ib = int((( (color[idx2][2] - color[idx1][2]) * fractBetween) + color[idx1][2]) * 255.0);

	col = "#%02x%02x%02x" % (ir,ig,ib)
	return (col,ir,ig,ib)

# Plot a pixel
# Side effect is to record the sample mouse value
def plotPixel(x,y,val):
	col = getColour(val)[0]

	if mirrorFlag.get():
		x = 31 - x

	xlow = x*IMAGE_SCALE
	ylow = y*IMAGE_SCALE
	xhigh= (x+1)*IMAGE_SCALE
	yhigh= (y+1)*IMAGE_SCALE
	c.create_rectangle(xlow,ylow,xhigh,yhigh,fill=col,width=0,tag=currentTag)

	if(mouse_x >= xlow and mouse_x < xhigh and mouse_y >= ylow and mouse_y < yhigh ):
		sampleValue.set(val)
		#print("temp",val,mouse_x,mouse_y)

# Read pixels from server and plot them
# Also add data to statistical bin
def readPixels():
	global sock
	min = 600
	max = 0
	
	for xh in range(0,32,16):
		t2 =  time.perf_counter_ns()
		instr = sock.recv(BLOCK_SIZE)
		t3 =  time.perf_counter_ns()

		if(len(instr) != BLOCK_SIZE):
			print("bad length for data",len(instr))
			return
		print(datetime.utcnow().strftime('%T.%f')[:-3],"Read pixels")	
		ba = bytearray(instr)
		it = struct.iter_unpack("h",ba)
		pos = 0
		for data in it:
			xl = pos // 24
			y  = pos  % 24
			pos = pos + 1
			val = data[0]/100
			if val<min: min=val
			if val>max: max=val
			x = xh + xl
			try:
				plotPixel(x,y,val)
				addBinValue(val)
			except:
				print(sys.exc_info()[0])
				print("Error",instr,data)
				return
		
		t4 =  time.perf_counter_ns()


# clear the bins used to record histogram
def clearBins():
	global bins
	global fullData
	
	fullData = []
	for i in range(32):
		bins[i]=0

# add a value to the histogram	
def addBinValue(val):
	global min_temp,max_temp,bins,fullData;
	fullData.append(val)
	
	if(val <=min_temp):
		bins[0] += 1
	elif(val >=max_temp):
		bins[31] +=1
	else:
		frac = (val - min_temp) / (max_temp - min_temp)
		binNo = int(frac*30) + 1
		bins[binNo] += 1

# plot the histogram
def	plotBins():
	global min_temp,max_temp,bins;
	
	fullData.sort()
	length = len(fullData)
	
	for i in range(32):
		xlow = 512 + 20 + i*14+1
		xhigh = 512 + 20 + (i+1)*14+1
		ylow = 384 - 50 - bins[i] / 2 
		yhigh = 384 - 50
		temp = min_temp + (i -1) /30.0 * (max_temp - min_temp)
		col = getColour( temp )[0]
		if bins[i]>0:
			c.create_rectangle(xlow,ylow,xhigh,yhigh,fill=col,width=1,tag=currentTag)
		else:
			c.create_line(xlow,ylow,xhigh,ylow,width=1,tag=currentTag)
		if i>0:
			c.create_text(xlow,yhigh+30,text="%4.1f"%temp,angle=270,anchor="se",tag=currentTag)
	if length>=2:
		c.create_text(522,20,anchor="sw",tag=currentTag,text="Min      %6.2f   Max %6.2f"%(fullData[0],fullData[length-1]))
		c.create_text(522,40,anchor="sw",tag=currentTag,text="Mean    %5.2f"%  (sum(fullData)/length) )
		c.create_text(522,60,anchor="sw",tag=currentTag,text="Median %5.2f"%fullData[int(length/2)] )
		c.create_text(522,80,anchor="sw",tag=currentTag,text="IQR        %5.2f,  %5.2f "%(fullData[int(length/4)],fullData[int(3*length/4)]) )

# establish connection with server
def setupClient():
	global sock,channel
	print("setting up client")
	channel = 1
	sock = bluetooth.BluetoothSocket() # bluetooth.RFCOMM)
	sock.connect((piMac, channel))
	print("connected")

# close connection with server and exit
def shutdown():
	sock.close()
	sys.exit()
	
# draw a frame,
# 
def drawFrame():
	global last_time,currentTag,pageNo,mw
	cur_time = time.perf_counter_ns()//1000000
	#print(cur_time-last_time)
	last_time = cur_time
	
	pageNo = pageNo + 1
	prevTag = currentTag
	currentTag = "page" + str(pageNo)
	
	#print("sending request to server")
	sock.send("hello".encode())
	#print("request sent to server")
	clearBins()
	readPixels()
	plotBins()
	
	c.delete(prevTag) # delete items from previous frame
	
	mw.after(10,drawFrame)

# main code, sets up and starts loop
setupUI()
setupClient()
drawFrame()
mw.mainloop()
