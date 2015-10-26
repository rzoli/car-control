from PIL import Image
import numpy
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
from motor_drive.firmware_test import MotorControl,parse_firmware_config
import multiprocessing

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
        self.image=gui.Image(self)
        self.image.setFixedWidth(500)
        self.image.setFixedHeight(500)
        self.setCentralWidget(self.image)
        
        self.show()
        self.log('Started')
        self.error_timer = QtCore.QTimer()
        self.error_timer.timeout.connect(self.catch_error_message)
        self.error_timer.start(100)
        self.log_update_timer = QtCore.QTimer()#Makes sure that whole logfile is always displayed on screen
        self.log_update_timer.timeout.connect(self.logfile2screen)
        self.log_update_timer.start(700)
        self.logtext=''
        
        self.command=multiprocessing.Queue()
        self.imageq=multiprocessing.Queue()
        self.vs = VideoStreamer(self.imageq,self.command)
        self.vs.start()
        self.image_timer = QtCore.QTimer()
        self.image_timer.timeout.connect(self.get_image)
        self.image_timer.start(100)
        
        
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
        
    def start_remote_capture(self,duration):
        import paramiko
        ssh=paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        pw, ok = QtGui.QInputDialog.getText(self, QtCore.QString('Password'), QtCore.QString(''), mode=QtGui.QLineEdit.Password)
        ssh.connect('192.168.0.10', port=9127, username='rz', password=str(pw))
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('sudo python /data/capture.py {0}'.format(duration))
#        print ssh_stdout.read()
#        print ssh_stderr.read()
            
    def _get_params_config(self):
        pc =  [
                
                {'name': 'Microcontroller level', 'type': 'group', 'expanded' : True, 'children': [
                    {'name': 'Serial port', 'type': 'str', 'value': '/dev/ttyUSB0'},
                    {'name': 'Connection', 'type': 'list', 'values': ['serial port', 'tcp/ip'], 'value': 'serial port'},
                    {'name': 'Timeout', 'type': 'float', 'value': 0.5, 'suffix': 's'},
                    ]},
                    
                    ]
        pc[0]['children'].extend([{'name': '{0}'.format(l), 'type': 'bool', 'value': False} for l in [k for k in parse_firmware_config().keys() if 'LED' in k]])
        pwm_channels = ['PWM {0}'.format(pwmc) for pwmc in ['PORTE0', 'PORTE1', 'PORTE2', 'PORTE3']]
        pc[0]['children'].extend([{'name': p, 'type': 'float', 'value': 0.0, 'suffix': '%'} for p in pwm_channels])
        return pc
        
    def settings_changed(self):
        new_values=self.settings.get_parameter_tree(True)
        if hasattr(self, 'setting_values'):
            #Check if LED status was changed
            for pn in [k for k in parse_firmware_config().keys() if 'LED' in k]:
                state=new_values[pn]
                if self.setting_values[pn]!=state and hasattr(self,'mc'):
                    self.mc.set_led(pn[:-4],state)
            #Check if PWM status was changed
            for pn in [k for k in self.setting_values.keys() if 'PWM' in k]:
                voltage=new_values[pn]
                if self.setting_values[pn]!=voltage and hasattr(self,'mc'):
                    self.mc.set_pwm(int(pn[-1]),int(voltage*10))
        self.setting_values = new_values
        
    def connect_action(self):
        if self.setting_values['Connection'] == 'serial port':
            if hasattr(self,'mc'):
                self.log('Already open')
                return
            import serial
            self.s=serial.Serial(self.setting_values['Serial port'], timeout=self.setting_values['Timeout'], baudrate=parse_firmware_config()['BAUD'])
            self.mc=MotorControl(self.s)
            self.log('Connected')

        
    def echo_action(self):
        if hasattr(self, 'mc'):
            self.log(self.mc.echo(1))
        
    def set_pwm_action(self):
        if hasattr(self, 'mc'):
            self.printc(self.mc)
            
    def exit_action(self):
        
        self.command.put('terminate')
        self.vs.join()
        
        self.log('Exit')
        self.close()
        
    def log(self, msg, loglevel='info'):
        getattr(logging, loglevel)(str(msg))
        self.logw.update(fileop.read_text_file(self.logfile))
        
    
class VideoStreamer(multiprocessing.Process):
    def __init__(self,image, command):
        self.image=image
        self.command=command
        multiprocessing.Process.__init__(self)
        
    def run(self):
        ip='192.168.0.10'
        port=8001
        import zmq
        import io
        context = zmq.Context()
        socket = context.socket(zmq.PAIR)
        socket.connect("tcp://{0}:{1}".format(ip, port))

        ct=0
        while True:
            if not self.command.empty():  
                print self.command.get()
                break
            try:
                message = socket.recv(flags=zmq.NOBLOCK)
                self.image.put(numpy.asarray(Image.open(io.BytesIO(message))))
            except zmq.ZMQError:
                pass
            time.sleep(1e-3)
    
    def run1(self):
        import io
        import socket
        import struct
        from PIL import Image
        self.aborted=False

        # Start a socket listening for connections on 0.0.0.0:8000 (0.0.0.0 means
        # all interfaces)
        server_socket = socket.socket()
        server_socket.bind(('0.0.0.0', 8000))
        while True:
            server_socket.listen(0)

        
            # Accept a single connection and make a file-like object out of it
            self.connection = server_socket.accept()[0].makefile('rb')
            print 'connected'
            try:
                while True:
                    if not self.command.empty():  
                        print self.command.get()
                        self.aborted=True
                        break
                    try:
                        image_len = struct.unpack('<L', self.connection.read(4))[0]
                        if not image_len:
                            break
                    
                        self.image.put(numpy.asarray(Image.open(io.BytesIO(self.connection.read(image_len)))))
                        print 'image read'
                    except:
                        pass
                    time.sleep(1e-3)
            finally:
                print 'closing'
                self.connection.close()
                server_socket.close()
            if self.aborted: break
                    
if __name__ == '__main__':
    RemoteControl()
