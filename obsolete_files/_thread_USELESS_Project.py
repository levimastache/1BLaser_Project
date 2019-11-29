#SEE /etc/rc.local FOR BOOTUP COMMANDS

from Measure_and_File import *
from WebServer import *
import _thread
#from _thread import *	#WORKED WHEN FILES STILL CALLED FUNCTIONS

web = WebServer()
board_boy = Measurer_and_Filer()

try:
  _thread.start_new_thread( board_boy.measure_and_file, () )
  _thread.start_new_thread( web.serve, () )
except:
  print ("Error: unable to start threads")

while 1:
  pass
