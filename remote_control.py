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
from visexpman.engine.generic import gui, fileop
from motor_drive.firmware_test import MotorControl,parse_firmware_config

def excepthook(excType, excValue, tracebackobj):
    msg='\n'.join(traceback.format_tb(tracebackobj))+str(excType.__name__)+': '+str(excValue)
    print msg
    error_messages.put(msg)
    
sys.excepthook = excepthook


error_messages = Queue.Queue()

class RemoteControl(gui.VisexpmanMainWindow):
    def __init__(self):
        if QtCore.QCoreApplication.instance() is None:
            qt_app = Qt.QApplication([])
        gui.VisexpmanMainWindow.__init__(self)
        self.logfile = os.path.join(tempfile.gettempdir(), 'robot_gui_{0}.txt'.format(int(time.time())))
        logging.basicConfig(filename= self.logfile,
                    format='%(asctime)s %(levelname)s\t%(message)s',
                    level=logging.DEBUG)
        self.setWindowTitle('Robot GUI')
        icon_folder = os.path.join(os.path.split(__file__)[0], 'icons')
        self.toolbar = gui.ToolBar(self, ['connect', 'echo', 'set_pwm', 'exit'], icon_folder = icon_folder)
        self.addToolBar(self.toolbar)
        self.console = gui.PythonConsole(self, selfw = self)
        self.console.setMinimumWidth(800)
        self._add_dockable_widget('Console', QtCore.Qt.LeftDockWidgetArea, QtCore.Qt.LeftDockWidgetArea, self.console)
        self.logw = gui.TextOut(self)
        self._add_dockable_widget('Log', QtCore.Qt.LeftDockWidgetArea, QtCore.Qt.LeftDockWidgetArea, self.logw)
        self.settings = gui.ParameterTable(self, self._get_params_config())
        self.settings.setMinimumWidth(300)
        self.settings.params.sigTreeStateChanged.connect(self.settings_changed)
        self.settings_changed()
        self._add_dockable_widget('Settings', QtCore.Qt.RightDockWidgetArea, QtCore.Qt.RightDockWidgetArea, self.settings)
        self.show()
        self.log('Started')
        self.error_timer = QtCore.QTimer()
        self.error_timer.timeout.connect(self.catch_error_message)
        self.error_timer.start(100)
        if QtCore.QCoreApplication.instance() is not None:
            QtCore.QCoreApplication.instance().exec_()
            
    def catch_error_message(self):
        if not error_messages.empty():
            self.log(error_messages.get(),'error')
            
    def _get_params_config(self):
        pc =  [ 
                
                {'name': 'Microcontroller level', 'type': 'group', 'expanded' : True, 'children': [
                    {'name': 'Serial port', 'type': 'str', 'value': '/dev/ttyUSB0'},
                    {'name': 'Connection', 'type': 'list', 'values': ['serial port', 'tcp/ip'], 'value': 'serial port'},
                    ]},
                    
                    ]
        pc[0]['children'].extend([{'name': '{0}'.format(l), 'type': 'bool', 'value': False} for l in [k for k in parse_firmware_config().keys() if 'LED' in k]])
        pwm_channels = ['PWM {0}'.format(pwmc) for pwmc in ['PORTE01', 'PORTE34', 'PORTD01', 'PORTD34']]
        pc[0]['children'].extend([{'name': p, 'type': 'float', 'value': 0.0, 'suffix': '%'} for p in pwm_channels])
        return pc
        
    def settings_changed(self):
        self.setting_values = self.settings.get_parameter_tree(True)
        
    def connect_action(self):
        if self.setting_values['Connection'] == 'serial port':
            if hasattr(self,'mc'):
                self.printc('Already open')
                return
            import serial
            self.s=serial.Serial(self.setting_values['Serial port'], timeout=0.5, baudrate=parse_firmware_config()['BAUD'])
            self.mc=mc=MotorControl(self.s)
        
    def echo_action(self):
        if hasattr(self, 'mc'):
            self.log(self.mc.echo(1))
        
    def set_pwm_action(self):
        if hasattr(self, 'mc'):
            self.printc(self.mc)
            
    def exit_action(self):
        self.log('Exit')
        self.close()
        
    def log(self, msg, loglevel='info'):
        getattr(logging, loglevel)(str(msg))
        self.logw.update(fileop.read_text_file(self.logfile))
        
                    
if __name__ == '__main__':
    RemoteControl()
