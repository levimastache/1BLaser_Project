import time	#Import built-in libraries for time-keeping and file-managing
import datetime
import os
#from sh import sudo, mount

import board	#Import libraries for hardware connections
import busio
from digitalio import DigitalInOut, Direction
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import adafruit_character_lcd.character_lcd as charlcd

from matplotlib import pyplot as plt	#Import libraries for plotting
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure


#Declare hardware variable connections
# - pin numbers change for PiZeroW
led_0 = DigitalInOut(board.D23)
led_0.direction = Direction.OUTPUT
led_1 = DigitalInOut(board.D18)
led_1.direction = Direction.OUTPUT
sleep_pin = DigitalInOut(board.D26)
sleep_pin.direction = Direction.INPUT

spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs = DigitalInOut(board.D8)
mcp = MCP.MCP3008(spi, cs)
chan0 = AnalogIn(mcp, MCP.P0)
chan1 = AnalogIn(mcp, MCP.P1)

lcd_columns = 16
lcd_rows = 2
lcd0_rs = DigitalInOut(board.D24)
lcd0_en = DigitalInOut(board.D25)
lcd0_d4 = DigitalInOut(board.D21)
lcd0_d5 = DigitalInOut(board.D20)
lcd0_d6 = DigitalInOut(board.D16)
lcd0_d7 = DigitalInOut(board.D12)
lcd0 = charlcd.Character_LCD_Mono(lcd0_rs, lcd0_en, lcd0_d4, lcd0_d5, lcd0_d6, lcd0_d7,
                               lcd_columns, lcd_rows)
lcd1_rs = DigitalInOut(board.D27)
lcd1_en = DigitalInOut(board.D22)
lcd1_d4 = DigitalInOut(board.D5)
lcd1_d5 = DigitalInOut(board.D6)
lcd1_d6 = DigitalInOut(board.D13)
lcd1_d7 = DigitalInOut(board.D19)
lcd1 = charlcd.Character_LCD_Mono(lcd1_rs, lcd1_en, lcd1_d4, lcd1_d5, lcd1_d6, lcd1_d7,
                             lcd_columns, lcd_rows)

#Declare global variables
today = datetime.datetime.today().strftime('%m_%d_%Y')
moment = datetime.datetime.today().strftime('%H:%M:%S')
thresh = 0.80


def running_signal():	#Function blinks the LEDs thrice
  for i in range(3):
    led_0.value = True
    led_1.value = True
    time.sleep(0.1)
    led_0.value = False
    led_1.value = False
    time.sleep(0.1)
  lcd0.clear()
  lcd1.clear()
  return None

def make_files():	#Function makes and writes the headers for the data and cost files 
  with open("/mnt/usb_static/datalog__"+today+".txt", "w", newline='') as data_txt:
    data_txt.write("current_0\tcurrent_1\ttime\n") # - sudo permission needed to manipulate USB dir
  with open("/mnt/usb_static/costs__"+today+".txt", "w", newline='') as costs_txt:
    costs_txt.write("jet_num\tstart_time\tstop_time\tcost\ttotal\n")

def is_ez_sleeping():	#FUNCTION DOESN'T WORK AT THE MOMENT AND WON'T BE A FEATURE OF THE FINAL PRODUCT ANYWAY
  STATE_USB = 'mounted'
  while(True):
    if sleep_pin.value == False:			#If pin is pulled low:
      if STATE_USB == 'mounted':
        os.system("sudo umount /mnt/usb_static")	# the program unmounts the drive,
        STATE_USB = 'unmounted'				# then cycles idly.
      continue
    elif STATE_USB == 'unmounted':					#If the pin is high, but the drive unmounted:
      os.system("sudo mount -t vfat /dev/sda1 /mnt/usb_static")
      #sudo.mount("/dev/sda1", "/mnt/usb_static", "-tvfat")		# the program remounts the drive,
      STATE_USB = 'mounted'						# then returns to the main loop
      break
    else:
      pass

def file_cleanup():	#Function erases files older than 7 days
  path = "/mnt/usb_static"
  for f in os.listdir(path):
    f = os.path.join(path, f)
    if os.stat(f).st_mtime < (time.time() - 7 *24*60*60):
      if os.path.isfile(f):
        os.remove(f)

def measure():		#Function takes voltage readings from current sensors
  voltage0 = float( chan0.voltage )	# via the MCP analog-to-digital chip
  voltage1 = float( chan1.voltage )
  return voltage0, voltage1

def update_datalog_file():	#Function uploads the present current readings to the data file
  filename = "/mnt/usb_static/datalog__"+today+".txt"
  current_reading_0, current_reading_1 = measure()
  current_reading_0 = current_reading_0 * 2
  current_reading_1 = current_reading_1 * 2
  with open(filename, "a", newline='') as data_file:
    data_file.write( str( round(current_reading_0,2) )+'\t\t'+str( round(current_reading_1,2) )+'\t\t'+moment+'\n' )
  return filename

def update_cost_file(JetNum, Start_time, Stop_time, Cost, Total):	#Function uploads cost amount and other pertinent data into costs file
  filename = "/mnt/usb_static/costs__"+today+".txt"
  with open(filename, "a", newline='') as costs_file:
    costs_file.write( str(JetNum)+'\t'+Start_time+'\t'+Stop_time+'\t'+str( round(Cost,2) )+'\t'+str( round(Total,2) )+'\n' )
    return None

def lcd_show_cost(JetNum, Cost): #Function displays most recent cost-of-use to the relevant LCD screen
  if JetNum == 0:
    lcd0.clear()
    lcd0.message = "You owe:\n       $"+str( round(Cost, 2) )
  else:
    lcd1.clear()
    lcd1.message = "You owe:\n       $"+str( round(Cost, 2) )

def png_this(fname):	#Function plots values in data file and stores it in a .png file
  with open(fname, newline='') as data_file:
    data_file.readline()	#skip past header line

    #Make data arrays with which to generate plot
    data = list( zip( *(line.strip().split('\t\t') for line in data_file) ) ) #magic
    x = list(data[2])
    y0 = [float(ch) for ch in list(data[0])]
    y1 = [float(ch) for ch in list(data[1])]
    y_thresh = [thresh*2]*len(x)
    #print (x)
    #print (y_thresh)
    #print (y0)
    #print (y1)

    #Plot with linestyle
    fig = Figure()
    canvas = FigureCanvasAgg(fig)
    ax = fig.subplots()
    ax.plot_date(x, y0, linestyle='-', color='r', marker=',', label='Jet0 Current')
    ax.plot_date(x, y1, linestyle='-', color='y', marker=',', label='Jet1 Current')
    ax.plot(x, y_thresh, linestyle=':', color='#ffa500', marker='None', label='threshold')

    #Format and save file
    fig.autofmt_xdate()
    ax.set_xlabel('time')
    ax.set_ylabel('Amps')
    ax.set_title('LaserJet as of: ' + today)
    ax.legend(loc='upper left')
    plt.tight_layout()
    fig.savefig('/mnt/usb_static/plot__'+today+'.png')

#def send_to_cloud():

def measure_and_file():	#This is the main function.
  global today	    #global line needed since
  global moment	    # variables will be changed

  #Initialize local variables
  last_day = today
  last_time_txt = last_time_tol_0 = last_time_tol_1 = time.time() #last_time_png = time.time()
  last_measurement_0, last_measurement_1 = measure()
  area_total_0 = area_total_1 = 0.00
  cost_total = 0.00
  STATE_0 = STATE_1 = 'idling'

  #Make files, delete old ones, and blink LEDs to signal that the main loop has started
  make_files()
  file_cleanup()
  running_signal()

  while(True):
    #is_ez_sleeping()
    if sleep_pin.value == False:	#If pin is pulled, ready to die. (extract USB, power-off, jack-in USB, power-on)
      continue

    elif last_day == today and time.time() - last_time_txt > 1: #If today is the same day as since the day the program started, and the timer reaches 1 second:
      last_time_txt = time.time()		# update timer, day, time
      today = datetime.datetime.today().strftime('%m_%d_%Y')
      moment = datetime.datetime.today().strftime('%H:%M:%S')
      txt_filename = update_datalog_file()	# and then data file.
      #print (sleep_pin.value)

      measurement_0, measurement_1 = measure() #Take new measurements...
      #What follows is a bit messy to explain line-by-line and is repeated twice. Basically:
      # If the new measurement(s) is above the idling threshold current, then the machine state changes
      #  to 'cutting' and sums the proceeding voltage readings into a total which, once the readings drop
      #  below the threshold for over 3 seconds, will go into the cost calculation of that cutting session.
      # When that happens, the cost file is updated, the amount is printed to the lcd screen,
      #  a new .png plot is generated from the data, and all files are sent to the cloud.
      # After which, the state and summed values reset.
      if measurement_0 > thresh:
        area_0 = ( (last_measurement_0 + measurement_0)/2 )*1 - 0.8*1
        area_total_0 += area_0
        last_time_tol_0 = time.time()
        if STATE_0 == 'idling':
          start_time_0 = datetime.datetime.today().strftime('%H:%M:%S')
          led_0.value = True
          STATE_0 = 'cutting'
      if measurement_0 < thresh and STATE_0 == 'cutting' and time.time() - last_time_tol_0 > 3:
        current_area = area_total_0 * 2
        E_total = (current_area * 208)
        kWh_total = E_total / (60*60)
        cost = .0834 * kWh_total * 100 #$/kWh and $Arbitrary
        #print ( "0: " + str(cost) )
        cost_total += cost
        stop_time = datetime.datetime.today().strftime('%H:%M:%S')
        update_cost_file(0, start_time_0, stop_time, cost, cost_total)
        lcd_show_cost(0, cost)
        png_this(txt_filename)
        #send_to_cloud()
        led_0.value = False
        STATE_0 = 'idling'
        area_total_0 = 0.00
      last_measurement_0 = measurement_0
      if measurement_1 > thresh:
        area_1 = ( (last_measurement_1 + measurement_1)/2 )*1 - 0.8*1
        area_total_1 += area_1
        last_time_tol_1 = time.time()
        if STATE_1 == 'idling':
          start_time_1 = datetime.datetime.today().strftime('%H:%M:%S')
          led_1.value = True
          STATE_1 = 'cutting'
      if measurement_1 < thresh and STATE_1 == 'cutting' and time.time() - last_time_tol_1 > 3:
        current_area = area_total_1 * 2
        E_total = (current_area * 208)
        kWh_total = E_total / (60*60)
        cost = .0834 * kWh_total * 100 #$/kWh and $Arbitrary
        #print ( "1: " + str(cost) )
        cost_total += cost
        stop_time = datetime.datetime.today().strftime('%H:%M:%S')
        update_cost_file(1, start_time_1, stop_time, cost, cost_total)
        lcd_show_cost(1, cost)
        png_this(txt_filename)
        #send_to_cloud()
        led_1.value = False
        STATE_1 = 'idling'
        area_total_1 = 0.00
      last_measurement_1 = measurement_1

    elif last_day != today:			#ELSE a day has elapsed since running this program:
      make_files()		# then make new files for new day,
      file_cleanup()		# delete the old ones,
      last_day = today		# reset the value of the day
      cost_total = 0.00		# and its cost total



#is_ez_sleeping()
measure_and_file()
