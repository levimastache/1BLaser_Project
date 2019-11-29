#SEE /etc/rc.local FOR BOOTUP COMMANDS

from Measure_and_File import *
from WebServer import *
from multiprocessing import *

web = WebServer()
board_boy = Measurer_and_Filer()

#try:
proc1 = Process( target=board_boy.measure_and_file, args=() )
proc1.start()
proc2 = Process( target=web.serve, args=() )
proc2.start()
#except:
  #print ("Error: unable to start processes")
