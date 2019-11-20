#SEE /etc/rc.local FOR BOOTUP COMMANDS

from Measure_and_File import *
from WebServer import *
import multiprocessing

web = WebServer()
board_boy = Measurer_and_Filer()
print ("Number of cores: ", multiprocessing.cpu_count() )

try:
  proc1 = Process( board_boy.measure_and_file, args=() )
  proc1.start()
  proc2 = Process( web.serve(), args=() )
  proc2.start()
except:
  print ("Error: unable to start processes")
