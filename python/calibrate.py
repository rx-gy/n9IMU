#!/usr/bin/python
import serial
import sys
import re
import math
from string import atof
from time import sleep
from time import localtime


ser_imu = serial.Serial( '/dev/ttyUSB0',1000000 )
newline = re.compile( '\n' )
count = 0
xcal50 = [0]*50
xcal100 = [0]*100
xcal1000 = [0]*1000
while  1 :
	data = ser_imu.readline()

	if data == 'S\n':
		temp = ser_imu.readline()
		gyrx = ser_imu.readline()
		gyry = ser_imu.readline()
		gyrz = ser_imu.readline()
		
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
			xcal100[ count%100 ] = xcal/100.0
			xcal1000[ count%1000 ] = xcal/1000.0

			if count >= 1000:
				count = 0
				sum=0
				for n in xcal50:
					sum+=n
				print '50 Average:\t%f' % sum
				sum = 0
				for n in xcal100:
					sum+=n
				print '100 Average:\t%f' % sum
				sum = 0
				for n in xcal1000:
					sum+=n
				print '1000 Average:\t%f' % sum



