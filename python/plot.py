import numpy as np
import pylab as py
 
def plot_data(data):
  py.clf()
  py.plot(data)
  py.show()
  py.savefig("data-%.8d.png"%counter)
 
if __name__ == "__main__":
  counter = 0
  while True:
    try:
      tmp = raw_input().strip().split()
      data = np.array(tmp, dtype=np.double)
    except EOFError:
      print "Input has terminated! Exiting"
      exit()
    except ValueError:
      print "Invalid input, skipping.  Input was: %s"%tmp
      continue
 
    print "Plotting plot number %d"%counter
    plot_data(data)
    counter += 1
