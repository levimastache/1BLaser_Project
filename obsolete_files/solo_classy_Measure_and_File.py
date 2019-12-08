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


class Measurer_and_Filer:
  #PIN NUMBERS CHANGE WITH PiZeroW
  #GPIO_23 Pi3
  red_led = DigitalInOut(board.D23)
  red_led.direction = Direction.OUTPUT

  #GPIO_8-11 of Pi3
  spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
  cs = DigitalInOut(board.D8)
  mcp = MCP.MCP3008(spi, cs)
  chan0 = AnalogIn(mcp, MCP.P0) #pin 0 of MCP ; ROOM FOR EXPANSION (multichannel mcp)

  #GPIO_24,25,21,20,16,&12 of Pi3
  lcd_columns = 16
  lcd_rows = 2
  lcd_rs = DigitalInOut(board.D24)
  lcd_en = DigitalInOut(board.D25)
  lcd_d4 = DigitalInOut(board.D21)
  lcd_d5 = DigitalInOut(board.D20)
  lcd_d6 = DigitalInOut(board.D16)
  lcd_d7 = DigitalInOut(board.D12)
  lcd = charlcd.Character_LCD_Mono(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7,
                               lcd_columns, lcd_rows)
  date = datetime.datetime.today().strftime('%m_%d_%Y')
  time = datetime.datetime.today().strftime('%H:%M:%S')
  thresh = 0.80

  def __init__(self): # PASS MCP CHANNEL NUMBER
    pass

  def running_led(self):
    Measurer_and_Filer.red_led.value = True
    time.sleep(0.5)
    Measurer_and_Filer.red_led.value = False
    return None

  def make_files(self):	#SUDO PERMIT to manipulate USB dir
    with open("/mnt/usb_static/datalog__"+Measurer_and_Filer.date+".txt", "w", newline='') as data_txt:
      data_txt.write("current\ttime\n")
    with open("/mnt/usb_static/costs__"+Measurer_and_Filer.date+".txt", "w", newline='') as costs_txt:
      costs_txt.write("start_time\tstop_time\tcost\ttotal\n")

  def file_cleanup(self):
    path = "/mnt/usb_static"
    for f in os.listdir(path):
      f = os.path.join(path, f)
      if os.stat(f).st_mtime < (time.time() - 7 * 24*60*60):
        if os.path.isfile(f):
          os.remove(f)

  def measure(self):
    voltage = float( Measurer_and_Filer.chan0.voltage )
    return voltage

  def update_datalog_file(self): #calls measure()
    filename = "/mnt/usb_static/datalog__"+Measurer_and_Filer.date+".txt"
    with open(filename, "a", newline='') as data_file: #SUDO PERMIT
      current_reading = Measurer_and_Filer.measure(self)*2
      time = Measurer_and_Filer.time
      data_file.write( str( round(current_reading,2) )+'\t'+time+'\n' )
    return filename

  def update_cost_file(self, Start_time, Stop_time, Cost, Total):
    filename = "/mnt/usb_static/costs__"+Measurer_and_Filer.date+".txt"
    with open(filename, "a", newline='') as costs_file: #SUDO PERMIT
      costs_file.write( Start_time+'\t'+Stop_time+'\t'+str( round(Cost,2) )+'\t'+str( round(Total,2) )+'\n' )
    return None

  def lcd_show_cost(self, cost): #CAN ONLY TEST WITH APPARATUS
    Measurer_and_Filer.lcd.clear()
    Measurer_and_Filer.lcd.message = "You owe:\n        $"+str( round(cost, 2) )

  #def send_to_cloud():

  def png_this(self, fname):
    with open(fname, newline='') as data_file:
      data_file.readline()
      data = list( zip( *(line.strip().split('\t') for line in data_file) ) ) #magic
      x = list(data[1])
      y = [float(ch) for ch in list(data[0])]
      y_thresh = [Measurer_and_Filer.thresh*2]*len(y)

      fig = Figure()
      canvas = FigureCanvasAgg(fig)
      #plt.style.use('seaborn')
      ax = fig.subplots()
      ax.plot_date(x, y, linestyle='-', color='#ffa500',
        marker=',', label='Current draw')
      ax.plot(x, y_thresh, linestyle=':', color='#a83232',
        marker='None', label='threshold')

      fig.autofmt_xdate()
      ax.set_xlabel('time')
      ax.set_ylabel('Amps')
      ax.set_title('LaserJet as of: ' + Measurer_and_Filer.date)
      ax.legend(loc='upper left')
      #ax.grid(True)
      plt.tight_layout()
      fig.savefig('/mnt/usb_static/plot__'+Measurer_and_Filer.date+'.png')


  #calls all other functions
  def measure_and_file(self):
    last_date = Measurer_and_Filer.date
    last_time_txt = time.time()
    last_time_tol = last_time_txt
    last_time_png = last_time_tol	#becoming obsolete
    last_measurement = Measurer_and_Filer.measure(self)
    area_total = 0.00
    cost_total = 0.00
    STATE = 'idling'

    Measurer_and_Filer.make_files(self)
    Measurer_and_Filer.running_led(self)

    while(True):	#LEAVE OUT FOR MULTI-TASK..?
      if last_date != Measurer_and_Filer.date:
        Measurer_and_Filer.make_files(self)
        last_date = Measurer_and_Filer.date
        cost_total = 0.00
      else:
        Measurer_and_Filer.file_cleanup(self)

        if time.time() - last_time_txt > 1:	#txt refresh time
          last_time_txt = time.time()
          Measurer_and_Filer.date = datetime.datetime.today().strftime('%m_%d_%Y')
          Measurer_and_Filer.time = datetime.datetime.today().strftime('%H:%M:%S')
          txt_filename = Measurer_and_Filer.update_datalog_file(self)

          measurement = Measurer_and_Filer.measure(self)
          if measurement > Measurer_and_Filer.thresh:
            area = ( (last_measurement + measurement)/2 )*1 - 0.8*1
            area_total += area
            last_time_tol = time.time()
            if STATE == 'idling':
              start_time = datetime.datetime.today().strftime('%H:%M:%S')
              Measurer_and_Filer.red_led.value = True
              STATE = 'cutting'
          if measurement < Measurer_and_Filer.thresh and STATE == 'cutting':
            if time.time() - last_time_tol > 3:
              current_area = area_total*2
              E_total = (current_area * 208)
              kWh_total = E_total / (60*60)
              cost = .0834 * kWh_total * 1000 #$/kWh and $Arbitrary
              cost_total += cost
              stop_time = datetime.datetime.today().strftime('%H:%M:%S')
              Measurer_and_Filer.update_cost_file(self, start_time, stop_time, cost, cost_total)
              Measurer_and_Filer.lcd_show_cost(self, cost)
              #Measurer_and_Filer.png_this(self, txt_filename)
              #Measurer_and_Filer.send_to_cloud()

              Measurer_and_Filer.red_led.value = False
              STATE = 'idling'
              area_total = 0.00
          last_measurement = measurement
        elif time.time() - last_time_png > 5:	#becoming obsolete
          Measurer_and_Filer.png_this(self, txt_filename)
          last_time_png = time.time()



board_boy = Measurer_and_Filer() #PASS MCP CHANNEL NUMBER
board_boy.measure_and_file()

#board_boy.running_led()
#board_boy.make_files()
#for i in range(1,20):
#  board_boy.update_datalog_file()
#board_boy.png_this('/mnt/usb_static/datalog__11_19_2019.txt')
