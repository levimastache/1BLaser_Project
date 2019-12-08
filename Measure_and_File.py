import time
import datetime
import sys
import os

import board
import busio
from digitalio import DigitalInOut, Direction
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import adafruit_character_lcd.character_lcd as charlcd

from matplotlib import pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure


#PIN NUMBERS CHANGE WITH PiZeroW
#GPIO_23 Pi3
led_0 = DigitalInOut(board.D23)
led_0.direction = Direction.OUTPUT
#led_1 = DigitalInOut(board.D)
#led_1.direction = Direction.OUTPUT

#GPIO_8-11 of Pi3
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs = DigitalInOut(board.D8)
mcp = MCP.MCP3008(spi, cs)
chan0 = AnalogIn(mcp, MCP.P0) #pin 0 of MCP ; ROOM FOR EXPANSION (multichannel mcp)
chan1 = AnalogIn(mcp, MCP.P1)

#GPIO_24,25,21,20,16,&12 of Pi3
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
#lcd1_rs = DigitalInOut(board.D)
#lcd1_en = DigitalInOut(board.D)
#lcd1_d4 = DigitalInOut(board.D)
#lcd1_d5 = DigitalInOut(board.D)
#lcd1_d6 = DigitalInOut(board.D)
#lcd1_d7 = DigitalInOut(board.D)
#lcd1 = charlcd.Character_LCD_Mono(lcd1_rs, lcd1_en, lcd1_d4, lcd1_d5, lcd1_d6, lcd1_d7,
#                             lcd_columns, lcd_rows)

date = datetime.datetime.today().strftime('%m_%d_%Y')
time = datetime.datetime.today().strftime('%H:%M:%S')
thresh = 0.80

def running_led():
    led_0.value = True
    #led_1.value = True
    time.sleep(0.5)
    led_0.value = False
    #led_1.value = False
    return None

def make_files():	#SUDO PERMIT to manipulate USB dir
  with open("/mnt/usb_static/datalog__"+date+".txt", "w", newline='') as data_txt:
    data_txt.write("current_0\tcurrent_1\ttime\n")
  with open("/mnt/usb_static/costs__"+date+".txt", "w", newline='') as costs_txt:
    costs_txt.write("jet_num\tstart_time\tstop_time\tcost\ttotal\n")

def file_cleanup():
  path = "/mnt/usb_static"
  for f in os.listdir(path):
    f = os.path.join(path, f)
    if os.stat(f).st_mtime < (time.time() - 7 * 24*60*60):
      if os.path.isfile(f):
        os.remove(f)

def measure():
  voltage0 = float( chan0.voltage )
  voltage1 = float( chan1.voltage )
  return voltage0, voltage1

def update_datalog_file(): #calls measure()
  filename = "/mnt/usb_static/datalog__"+date+".txt"
  current_reading0, current_reading1 = measure()*2
  with open(filename, "a", newline='') as data_file: #SUDO PERMIT
    data_file.write( str( round(current_reading0,2) )+'\t'+str( round(current_reading1,2) )+'\t'+time+'\n' )
  return filename

def update_cost_file(JetNum, Start_time, Stop_time, Cost, Total):
  filename = "/mnt/usb_static/costs__"+date+".txt"
  with open(filename, "a", newline='') as costs_file: #SUDO PERMIT
    costs_file.write( str(JetNum)+'\t'+Start_time+'\t'+Stop_time+'\t'+str( round(Cost,2) )+'\t'+str( round(Total,2) )+'\n' )
    return None

def lcd_show_cost(JetNum, Cost): #CAN ONLY TEST WITH APPARATUS
  if JetNum == 0:
    lcd0.clear()
    lcd0.message = "You owe:\n        $"+str( round(Cost, 2) )
  else:
    lcd1.clear()
    lcd1.message = "You owe:\n        $"+str( round(Cost, 2) )

def png_this(fname):
  with open(fname, newline='') as data_file:
    data_file.readline()
    data = list( zip( *(line.strip().split('\t') for line in data_file) ) ) #magic
    x = list(data[2])
    y0 = [float(ch) for ch in list(data[0])]
    y1 = [float(ch) for ch in list(data[1])]
    y_thresh = [thresh*2]*len(x)

    fig = Figure()
    canvas = FigureCanvasAgg(fig)
    #plt.style.use('seaborn')
    ax = fig.subplots()
    ax.plot_date(x, y0, linestyle='-', color='#ffa500', marker=',', label='Jet0 Current')
    ax.plot_date(x, y1, linestyle='-', color='#ffa300', marker=',', label='Jet1 Current')
    ax.plot(x, y_thresh, linestyle=':', color='#a83232', marker='None', label='threshold')

    fig.autofmt_xdate()
    ax.set_xlabel('time')
    ax.set_ylabel('Amps')
    ax.set_title('LaserJet as of: ' + date)
    ax.legend(loc='upper left')
    #ax.grid(True)
    plt.tight_layout()
    fig.savefig('/mnt/usb_static/plot__'+date+'.png')

#def send_to_cloud():

#calls all other functions
def measure_and_file():
  last_date = date
  last_time_txt = time.time()
  last_time_tol_0, last_time_tol_1 = last_time_txt
  #last_time_png = last_time_tol
  last_measurement_0, last_measurement_1 = measure()
  area_total_0, area_total_1 = 0.00
  cost_total = 0.00
  STATE_0, STATE_1 = 'idling'

  make_files()
  running_led()

  while(True):
    if last_date == date:
      file_cleanup()

      if time.time() - last_time_txt > 1:	#txt refresh time
        last_time_txt = time.time()
        date = datetime.datetime.today().strftime('%m_%d_%Y')
        time = datetime.datetime.today().strftime('%H:%M:%S')
        txt_filename = update_datalog_file()

        measurement_0, measurement_1 = measure()

        if measurement_0 > thresh:
          area_0 = ( (last_measurement_0 + measurement_0)/2 )*1 - 0.8*1
          area_total_0 += area_0
          last_time_tol_0 = time.time()
          if STATE_0 == 'idling':
            start_time_0 = datetime.datetime.today().strftime('%H:%M:%S')
            led_0.value = True
            STATE_0 = 'cutting'
        if measurement_0 < thresh and STATE_0 == 'cutting':
          if time.time() - last_time_tol_0 > 3:
            current_area = area_total_0*2
            E_total = (current_area * 208)
            kWh_total = E_total / (60*60)
            cost = .0834 * kWh_total * 1000 #$/kWh and $Arbitrary
            cost_total += cost
            stop_time = datetime.datetime.today().strftime('%H:%M:%S')
            update_cost_file(0, start_time_0, stop_time, cost, cost_total)
            lcd_show_cost(0, cost)
            #png_this(txt_filename)
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
            led_0.value = True
            STATE_1 = 'cutting'
        if measurement_1 < thresh and STATE_1 == 'cutting':
          if time.time() - last_time_tol_1 > 3:
            current_area = area_total_1*2
            E_total = (current_area * 208)
            kWh_total = E_total / (60*60)
            cost = .0834 * kWh_total * 1000 #$/kWh and $Arbitrary
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

      #elif time.time() - last_time_png > 5:	#becoming obsolete
        #png_this(txt_filename)
        #last_time_png = time.time()

    else:
      make_files()
      last_date = date
      cost_total = 0.00



measure_and_file()
