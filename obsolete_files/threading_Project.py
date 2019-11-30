#SEE /etc/rc.local FOR BOOTUP COMMANDS

from Measure_and_File import *
from WebServer import *
import threading

web = WebServer()
board_boy = Measurer_and_Filer()

class myThread (threading.Thread):
   def __init__(self, threadID): #, name):
      threading.Thread.__init__(self)
      self.threadID = threadID
      #self.name = name
   def run(self):
     try:
       if self.threadID == 1:
         print ("Starting measuring_and_filing")
         board_boy.measure_and_file()
       elif self.threadID == 2:
         print ("Starting web_serving")
         web.serve()
     except:
       print ("Error: unable to start threads")

# Create new threads
measuring_and_filing = myThread(1)
web_serving = myThread(2)

# Start new Threads
measuring_and_filing.start()
web_serving.start()
print ("Number of active threads: ", threading.activeCount() )

