#from bottle import route, static_file, run, debug, error
#import paste

from flask import Flask, redirect, request, send_from_directory, render_template
import datetime

class WebServer:
  #The statement below can be accessed via ClassName.__doc__
  'Class which encapsulates the web serving from the Python side' 
  
  #CLASS VARIABLES -> none

  def __init__(self):
    pass

  def get_date(self):
    today_d = datetime.datetime.today()
    today_date = today_d.strftime('%m_%d_%Y')
    return today_date

  def serve(self):
    #FUNCTION VARIABLES
    app = Flask(__name__, root_path='/',
                          static_url_path='',
                          static_folder='/mnt/usb_static',
                          template_folder='/home/pi/1BLaser/obsolete_files/templates')

    @app.route('/')
    def hello():
      return redirect('http://192.168.43.124:8080/plot') #CHANGE FOR WIFI TRANSFER
    @app.route('/plot')
    def plot():
      return render_template('plot.html', title = 'Today\'s Plot', today_date = WebServer.get_date(self) )
    @app.route('/data')
    def data():
      return render_template('data.html', title = 'Today\'s Data', today_date = WebServer.get_date(self) )
    @app.route('/costs')
    def costs():
      return render_template('costs.html', title = 'Today\'s Costs', today_date = WebServer.get_date(self) )
    @app.route('/<filename>') #ROOM FOR EXANSION (multichannel mcp)
    def server_static(filename): #serves a file as entered - downloads .csv files
      #return app.send_static_file(filename)
      return send_from_directory('/mnt/usb_static/', filename, as_attachment=False)

    @app.errorhandler(404)
    def error404(error):
      return '''The requested URL cased an error...
                   \n\t File not Found: check spelling'''
    @app.errorhandler(500)
    def error500(error):
      return '''The requested URL cased an error... 
                   \n\t Internal Server Error: check if Pi is running'''

    print ('Host: %s' % '192.168.43.124:8080')
    if __name__ == '__main__':
      #from waitress import serve
      #serve(app, host='0.0.0.0', port=8080)
      app.run( host='0.0.0.0',
               port=8080, #was 2000
               debug=True
      )



web = WebServer()
web.serve()
