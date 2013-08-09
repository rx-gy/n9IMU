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
		self.fps = Label(cf, text="0 fps")
		self.fps.grid(column=2, row=4, columnspan=5)
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
				#print msg
				self.scrollGraph( msg[0], msg[1], msg[2] )
				#self.scrollGraph(self.gf.p,
					#(0.25+y1,   0.25, 0.7+y2,   0.6,	 0.7,   0.8),
					#( '#ff4', '#f40', '#4af', '#080', '#0f0', '#080'),
					# "" if t % 65 else "#088")
			except Queue.Empty:
				pass

	def scrollGraph(self, data, colors, bar=""):   # Scroll the strip, add new data
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
			y0 = int((self.h-1) * (1.0-self.data[d]))   # plot all the data points
			y1 = int((self.h-1) * (1.0-data[d]))
			ya, yb = sorted((y0, y1))
			for y in range(ya, yb+1):				   # connect the dots
				self.gf.p.put(colors[d], (self.x,y))
				self.gf.p.put(colors[d], (self.x+self.sw,y))
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
		self.master.after(100, self.periodicCall)

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
		xcal50 = [0]*50
		ycal50 = [0]*50
		zcal50 = [0]*50
		sum = 0

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
					xcal = -1 * (gyrx/temp)
					ycal = -1 * (gyry/temp)
					zcal = -1 * (gyrz/temp)
					count += 1

					xcal50[ count%50 ] = xcal/50.0
					ycal50[ count%50 ] = ycal/50.0
					zcal50[ count%50 ] = zcal/50.0

					if count >= 50:
						count = 0
						sumx=0
						sumy=0
						sumz=0
						for n in xcal50:
							sumx+=n
						for n in ycal50:
							sumy+=n
						for n in zcal50:
							sumz+=n

						sumx = sumx*10 + 0.5
						sumy = sumy*10 + 0.7
						sumz = sumz*10 + 0.5

						if (1 <= sumx):
							sumx = 1 
						if (sumx <= -1):
							sumyx = -1
						if (1 <= sumy):
							sumy = 1
						if (sumy <= -1):
							sumy = -1
						if (1 <= sumz):
							sumz = 1
						if (sumz <= -1):
							sumz = -1

						#y1 = 0.2*math.sin(0.02*math.pi*t)
						#y2 = 0.9*y2 + 0.1*(random.random()-0.5)
						msg = (
							(sumx,   sumy, sumz,   0.75,	 0.5,   0.25),
							( '#ff4', '#f40', '#4af', '#080', '#0f0', '#080'),
							 "" if t % 65 else "#088")
						self.queue.put(msg)
						t += 1
						time.sleep( 0.01 )


	def endApplication(self):
		self.running = 0

rand = random.Random()
root = Tk()

client = ThreadedClient(root)
root.mainloop()

#************************************************

#
#class StripChart:
#
#	def Run(self):
#		self.go = 1
#		for t in threading.enumerate():
#			if t.name == "_gen_":
#				print("already running")
#				return
#		threading.Thread(target=self.do_start, name="_gen_").start()
#
#	def Stop(self):
#		self.go = 0
#		for t in threading.enumerate():
#			if t.name == "_gen_":
#				t.join()
#
#	def Reset(self):
#		self.Stop()
#		self.clearstrip(self.gf.p, '#345')
#
#	def do_start(self):
#		t = 0
#		y2 = 0
#		tx = time.time()
#		while self.go:
#			y1 = 0.2*math.sin(0.02*math.pi*t)
#			y2 = 0.9*y2 + 0.1*(random.random()-0.5)
#			self.scrollstrip(self.gf.p,
#			   (0.25+y1,   0.25, 0.7+y2,   0.6,	 0.7,   0.8),
#			   ( '#ff4', '#f40', '#4af', '#080', '#0f0', '#080'),
#				 "" if t % 65 else "#088")
#
#			t += 1
#			if not t % 100:
#				tx2 = time.time()
#				self.fps.config(text='%d fps' % int(100/(tx2 - tx)))
#				tx = tx2
##			time.sleep(0.001)
#
#	def clearstrip(self, p, color):  # Fill strip with background color
#		self.bg = color			  # save background color for scroll
#		self.data = None			 # clear previous data
#		self.x = 0
#		p.tk.call(p, 'put', color, '-to', 0, 0, p['width'], p['height'])
#
#	def scrollstrip(self, p, data, colors, bar=""):   # Scroll the strip, add new data
#		self.x = (self.x + 1) % self.sw			   # x = double buffer position
#		bg = bar if bar else self.bg
#		p.tk.call(p, 'put', bg, '-to', self.x, 0,
#				  self.x+1, self.h)
#		p.tk.call(p, 'put', bg, '-to', self.x+self.sw, 0,
#				  self.x+self.sw+1, self.h)
#		self.gf.coords(self.item, -1-self.x, self.top)  # scroll to just-written column
#		if not self.data:
#			self.data = data
#		for d in range(len(data)):
#			y0 = int((self.h-1) * (1.0-self.data[d]))   # plot all the data points
#			y1 = int((self.h-1) * (1.0-data[d]))
#			ya, yb = sorted((y0, y1))
#			for y in range(ya, yb+1):				   # connect the dots
#				p.put(colors[d], (self.x,y))
#				p.put(colors[d], (self.x+self.sw,y))
#		self.data = data			# save for next call
#
#def main():
#	root = Tk()
#	root.title("StripChart")
#	app = StripChart(root)
#	root.mainloop()
#
#main()
#
