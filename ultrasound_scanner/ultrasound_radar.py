from PIL import Image
import numpy,serial
import Queue
import os
import time
import tempfile
import logging
import sys
import traceback
import PyQt4.Qt as Qt
import PyQt4.QtGui as QtGui
import PyQt4.QtCore as QtCore
from visexpman.engine.generic import gui, fileop,utils
import multiprocessing

def excepthook(excType, excValue, tracebackobj):
    msg='\n'.join(traceback.format_tb(tracebackobj))+str(excType.__name__)+': '+str(excValue)
    print msg
    error_messages.put(msg)
    
sys.excepthook = excepthook


error_messages = Queue.Queue()

class UltrasoundRadar(gui.VisexpmanMainWindow):
    def __init__(self):
        if QtCore.QCoreApplication.instance() is None:
            qt_app = Qt.QApplication([])
        gui.VisexpmanMainWindow.__init__(self)
        
        self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.split(os.path.dirname(__file__))[0],'icons', 'mr.jpg')))
        
        self.logfile = os.path.join(tempfile.gettempdir(), 'ultrasound_radar_{0}.txt'.format(int(time.time())))
        logging.basicConfig(filename= self.logfile,
                    format='%(asctime)s %(levelname)s\t%(message)s',
                    level=logging.DEBUG)
        self.setWindowTitle('Ultrasound Radar')
        icon_folder = os.path.join(os.path.split(os.path.dirname(__file__))[0], 'icons')
        self.toolbar = gui.ToolBar(self, ['connect', 'echo', 'new', 'exit'], icon_folder = icon_folder)
        self.addToolBar(self.toolbar)
        self.console = gui.PythonConsole(self, selfw = self)
        self.console.setMinimumWidth(800)
        self.console.setMinimumHeight(200)
        self._add_dockable_widget('Console', QtCore.Qt.BottomDockWidgetArea, QtCore.Qt.BottomDockWidgetArea, self.console)
        self.logw = gui.TextOut(self)
        self.logw.setMinimumWidth(300)
        self._add_dockable_widget('Log', QtCore.Qt.BottomDockWidgetArea, QtCore.Qt.BottomDockWidgetArea, self.logw)
        self.settings = gui.ParameterTable(self, self._get_params_config())
        self.settings.setMinimumWidth(300)
        self.settings.params.sigTreeStateChanged.connect(self.settings_changed)
        self.settings_changed()
        self._add_dockable_widget('Settings', QtCore.Qt.RightDockWidgetArea, QtCore.Qt.RightDockWidgetArea, self.settings)
        self.plot=gui.Plot(self)
        self.plot.setFixedWidth(500)
        self.plot.setFixedHeight(500)
        self.setCentralWidget(self.plot)
        
        self.show()
        self.log('Started')
        self.error_timer = QtCore.QTimer()
        self.error_timer.timeout.connect(self.catch_error_message)
        self.error_timer.start(100)
        self.log_update_timer = QtCore.QTimer()#Makes sure that whole logfile is always displayed on screen
        self.log_update_timer.timeout.connect(self.logfile2screen)
        self.log_update_timer.start(700)
        self.logtext=''
        
        self.map=[]
        
        if QtCore.QCoreApplication.instance() is not None:
            QtCore.QCoreApplication.instance().exec_()
            
    def get_image(self):
        if not self.imageq.empty():
            self.captured_image=self.imageq.get()
            self.image.img.setImage(self.captured_image)
            last_update=utils.timestamp2hms(time.time())
            self.image.plot.setTitle(last_update)
            
    def catch_error_message(self):
        if not error_messages.empty():
            self.log(error_messages.get(),'error')
            
    def logfile2screen(self):
        newlogtext=fileop.read_text_file(self.logfile)
        if len(newlogtext)!=len(self.logtext):
            self.logtext=newlogtext
            self.logw.update(self.logtext)
            
    def _get_params_config(self):
        pc =  [                
                {'name': 'Microcontroller', 'type': 'group', 'expanded' : True, 'children': [
                    {'name': 'Serial port', 'type': 'str', 'value': '/dev/ttyACM0'},
                    {'name': 'Connection', 'type': 'list', 'values': ['serial port', 'tcp/ip'], 'value': 'serial port'},
                    {'name': 'Timeout', 'type': 'float', 'value': 0.5, 'suffix': 's'},
                    ]},
                
                    
                    ]
        return pc
        
    def settings_changed(self):
        new_values=self.settings.get_parameter_tree(True)
        self.setting_values = new_values
        
    def connect_action(self):
        self.serial=serial.Serial(self.setting_values['Serial port'],115200,timeout=self.setting_values['Timeout'])
        self.log('Connected')
        
    def echo_action(self):
        if not hasattr(self, 'serial'):
            self.connect_action()
        self.serial.write('ping\r\n')
        time.sleep(0.1)
        self.log(self.serial.readline())
            
    def exit_action(self):
        if hasattr(self, 'serial'):
            self.serial.close()
        self.log('Exit')
        self.close()
        
    def new_action(self):
        self.log('New map')
        self.map=[]
        
    def cmd(self,cmd):
        if not hasattr(self, 'serial'):
            self.connect_action()
        self.log(cmd)
        self.serial.write(cmd+'\r\n')
        time.sleep(0.1)
        res=self.serial.readline()
        self.log(res)
        return res
        
    def rot(self,angle):
        self.cmd('rot,{0}'.format(angle))
        
    def tilt(self,angle):
        self.cmd('tilt,{0}'.format(angle))
        
    def meas(self,rot=None):
        if rot!=None:
            self.rot(rot)
            time.sleep(0.5)
        res=self.cmd('meas')
        distance=float(res.split(' ')[0])
        if rot!=None:
            self.map.append([rot,distance])
            self.map2plot()
    
    def map2plot(self):
        map=numpy.array(self.map)
        self.x=[numpy.cos(numpy.radians(map[:,0]))*map[:,1],numpy.array([0])]
        self.y=[numpy.sin(numpy.radians(map[:,0]))*map[:,1],numpy.array([0])]
        plotparams=[{'pen': None,'symbol':'o', 'symbolSize':5, 'symbolBrush': (0,200,0,150)}]
        plotparams.append({'pen': None,'symbol':'d', 'symbolSize':12, 'symbolBrush': (200,0,0,150)})
        self.plot.update_curves(self.x,self.y,plotparams=plotparams)
        self.plot.plot.setYRange(0, 100)
        self.plot.plot.setXRange(-50, 50)
        
        
    def log(self, msg, loglevel='info'):
        getattr(logging, loglevel)(str(msg))
        self.logw.update(fileop.read_text_file(self.logfile))
            
if __name__ == '__main__':
    UltrasoundRadar()
