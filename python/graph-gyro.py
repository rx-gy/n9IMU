from tkCommonDialog import *
import Queue
import math, random, threading, time
import serial, sys, re
from string import atof

class graphUI:

	def __init__(self, root, queue, endcommand):
		self.gf = self.makeGraph(root)
		self.cf = self.makeControls(root,endcommand)
		self.queue = queue
		self.gf.pack()
		self.cf.pack()
		self.x = 0
		self.data = None
		self.bg = "#002"
		#self.Reset()

	def makeGraph(self, frame):
		self.sw = 1000
		self.h = 400
		self.top = 2
		gf = Canvas(frame, width=self.sw, height=self.h+10,
					bg="#002", bd=0, highlightthickness=0)
		gf.p = PhotoImage(width=2*self.sw, height=self.h)
		self.item = gf.create_image(0, self.top, image=gf.p, anchor=NW)
		return(gf)

	def makeControls(self, frame, endcommand):
		cf = Frame(frame, borderwidth=1, relief="raised")
		#Button(cf, text="Run", command=self.Run).grid(column=2, row=2)
		#Button(cf, text="Stop", command=self.Stop).grid(column=4, row=2)
		Button(cf, text="Reset", command=endcommand).grid(column=6, row=2)
		self.xoff = Label(cf, text="x: 0")
		self.yoff = Label(cf, text="y: 0")
		self.zoff = Label(cf, text="z: 0")
		self.temp = Label(cf, text="t: 0")
		self.xoff.grid(column=2, row=4, columnspan=5)
		self.yoff.grid(column=2, row=5, columnspan=5)
		self.zoff.grid(column=2, row=6, columnspan=5)
		self.temp.grid(column=2, row=7, columnspan=5)
		return(cf)


	def processIncoming(self):
		"""
		Handle all the messages currently in the queue (if any).
		"""
		while self.queue.qsize():
			try:
				msg = self.queue.get(0)
				# Check contents of message and do what it says
				# As a test, we simply print it
				self.scrollGraph( msg[0], msg[1], msg[2] )
			except Queue.Empty:
				pass

	def scrollGraph(self, data, offset, colors, bar=""):   # Scroll the strip, add new data
		self.xoff.config(text='x:%s' % offset[0])
		self.yoff.config(text='y:%s' % offset[1])
		self.zoff.config(text='z:%s' % offset[2])
		self.temp.config(text='t:%i deg' % offset[3])
		self.x = (self.x + 1) % self.sw			   # x = double buffer position
		bg = bar if bar else self.bg
		self.gf.p.tk.call(self.gf.p, 'put', bg, '-to', self.x, 0,
				  self.x+1, self.h)
		self.gf.p.tk.call(self.gf.p, 'put', bg, '-to', self.x+self.sw, 0,
				  self.x+self.sw+1, self.h)
		self.gf.coords(self.item, -1-self.x, self.top)  # scroll to just-written column
		if not self.data:
			self.data = data
		for d in range(len(data)):
			if type(self.data[d]) != type('str'):
				y0 = int((self.h-1) * (1.0-self.data[d]))   # plot all the data points
			if type(data[d]) != type('str'):
				y1 = int((self.h-1) * (1.0-data[d]))   # plot all the data points
			self.gf.p.put(colors[d], (self.x+self.sw,y0))
			self.gf.p.put(colors[d], (self.x,y1))
			#y0 = int((self.h-1) * (1.0-self.data[d]))   # plot all the data points
			#y1 = int((self.h-1) * (1.0-data[d]))
			#ya, yb = sorted((y0, y1))
			#for y in range(ya, yb+1):				   # connect the dots
			#	self.gf.p.put(colors[d], (self.x,y))
			#	self.gf.p.put(colors[d], (self.x+self.sw,y))
		self.data = data			# save for next call



class ThreadedClient:
	"""
	Launch the main part of the GUI and the worker thread. periodicCall and
	endApplication could reside in the GUI part, but putting them here
	means that you have all the thread controls in a single place.
	"""
	def __init__(self, master):
		"""
		Start the GUI and the asynchronous threads. We are in the main
		(original) thread of the application, which will later be used by
		the GUI. We spawn a new thread for the worker.
		"""
		self.master = master

		# Create the queue
		self.queue = Queue.Queue()

		# Set up the GUI part
		self.gui = graphUI(master, self.queue, self.endApplication)

		self.running = 1

		# Start the periodic call in the GUI to check if the queue contains
		# anything
		self.periodicCall()

		# Set up the thread to do asynchronous I/O
		# More can be made if necessary
		self.thread1 = threading.Thread(target=self.workerThread1)
		self.thread1.daemon = True
		self.thread1.start()


	def periodicCall(self):
		"""
		Check every 100 ms if there is something new in the queue.
		"""
		self.gui.processIncoming()
		if not self.running:
			# This is the brutal stop of the system. You may want to do
			# some cleanup before actually shutting it down.
			import sys
			sys.exit(1)
		self.master.after(10, self.periodicCall)

	def workerThread1(self):
		"""
		This is where we handle the asynchronous I/O. For example, it may be
		a 'select()'.
		One important thing to remember is that the thread has to yield
		control.
		"""
		t = 0
		y2 = 0
		ser_imu = serial.Serial( '/dev/ttyUSB0',1000000 )
		newline = re.compile( '\n' )
		count = 0
		flen = 750
		xcalf = [0]*flen
		ycalf = [0]*flen
		zcalf = [0]*flen
		sum = 0
		xx = [1]*10
		yy = [1]*10
		zz = [1]*10
		tt = [1]*10

		xmod = 0
		ymod = 0
		zmod = 0
		tmod = 0

		while self.running:
			# To simulate asynchronous I/O, we create a random number at
			# random intervals. Replace the following 2 lines with the real
			# thing.
			#time.sleep(rand.random() * 0.3)

			try:
				data = ser_imu.readline()
			except OSError:
				print "GOT OSError"

			if data == 'S\n':
				try:
					temp = ser_imu.readline()
					gyrx = ser_imu.readline()
					gyry = ser_imu.readline()
					gyrz = ser_imu.readline()
				except OSError:
					print "GOT OSError"
					temp = '1'
					gyrx = '0'
					gyry = '0'
					gyrz = '0'
				
				try:
					temp = atof(newline.sub( '', temp ))
					gyrx = atof(newline.sub( '', gyrx ))
					gyry = atof(newline.sub( '', gyry ))
					gyrz = atof(newline.sub( '', gyrz ))
				except ValueError:
					pass
				else:

					for i in range(flen-1):
						xcalf[i] = xcalf[i+1] 
						ycalf[i] = ycalf[i+1] 
						zcalf[i] = zcalf[i+1] 

					temp = 35 + (temp + 13200)/280.0
					xcalf[flen-1] = gyrx/14.375 
					ycalf[flen-1] = gyry/14.375
					zcalf[flen-1] = gyrz/14.375

					sumx = 0
					sumy = 0 
					sumz = 0

					for n in xcalf:
						sumx += n
					for n in ycalf:
						sumy += n
					for n in zcalf:
						sumz += n
					sumx/=flen
					sumy/=flen
					sumz/=flen


#					print 'sumx: %f' %sumx
#					print 'sumy: %f' %sumy
#					print 'sumz: %f' %sumz
#					print 'temp: %f' %temp
					


					temp /= 10.0

					sx = sumx
					sy = sumy
					sz = sumz
					t = temp

					sumx += xmod
					sumy += ymod
					sumz += zmod
					temp += tmod

					
					if (1 <= sumx):
						xmod = -1*sx + 0.5
						sumx = 1 
					if (sumx <= 0):
						xmod = -1*sx + 0.5
						sumyx = 0
					if (1 <= sumy):
						ymod = -1*sy + 0.5
						sumy = 1
					if (sumy <= 0):
						ymod = -1*sy + 0.5
						sumy = 0
					if (1 <= sumz):
						zmod = -1*sz + 0.5
						sumz = 1
					if (sumz <= 0):
						zmod = -1*sz + 0.5
						sumz = 0
					if (temp <= 0):
						tmod = -1*t + 0.5
						temp = 0
					if (1 <= temp):
						tmod = -1*t + 0.5
						temp = 1

				msg = (
					(sumx,   sumy, sumz,   0.75,	 temp,   0.25),
					( xmod, ymod, zmod, t*10.0 ),
					( '#ff4', '#f40', '#4af', '#080', '#0f0', '#080'),
					 #"" if t % 65 else "#088")
					 "")
				self.queue.put(msg)
				t += 1
				#time.sleep( 0.08 )


	def endApplication(self):
		self.running = 0

rand = random.Random()
root = Tk()

client = ThreadedClient(root)
root.mainloop()

