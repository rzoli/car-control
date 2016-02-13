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
        
        self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.split(__file__)[0],'icons', 'mr.jpg')))
        
        self.logfile = os.path.join(tempfile.gettempdir(), 'robot_gui_{0}.txt'.format(int(time.time())))
        logging.basicConfig(filename= self.logfile,
                    format='%(asctime)s %(levelname)s\t%(message)s',
                    level=logging.DEBUG)
        self.setWindowTitle('Robot GUI')
        icon_folder = os.path.join(os.path.split(__file__)[0], 'icons')
        self.toolbar = gui.ToolBar(self, ['connect', 'echo', 'set_motor', 'read_adc', 'start_video', 'stop', 'exit'], icon_folder = icon_folder)
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
        
        self.nframes=100
        self.width=800#320
        self.height=600#240
        self.iso=100
        self.exposure=10
        self.delay=100
        
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
                {'name': 'Motor Mode', 'type': 'list', 'values': ['voltage', 'pwm', 'wheels']},
                {'name': 'Microcontroller', 'type': 'group', 'expanded' : True, 'children': [
                    {'name': 'Serial port', 'type': 'str', 'value': '/dev/ttyUSB0'},
                    {'name': 'Connection', 'type': 'list', 'values': ['serial port', 'tcp/ip'], 'value': 'serial port'},
                    {'name': 'Timeout', 'type': 'float', 'value': 0.5, 'suffix': 's'},
                    ]},
                {'name': 'Vehicle Control', 'type': 'group', 'expanded' : True, 'children': [
                    {'name': 'Motor1 voltage', 'type': 'float', 'value': 0.0, 'suffix': '%'},
                    {'name': 'Motor2 voltage', 'type': 'float', 'value': 0.0, 'suffix': '%'},
                    {'name': 'Wheel voltage', 'type': 'float', 'value': 0.0, 'suffix': '%'},
                    {'name': 'Wheels voltage difference', 'type': 'float', 'value': 0.0, 'suffix': '%'},
                    ]},
                {'name': 'Camera', 'type': 'group', 'expanded' : True, 'children': [
                    {'name': 'N frames', 'type': 'int', 'value': 100},
                    {'name': 'Width', 'type': 'int', 'value': 320},
                    {'name': 'Height', 'type': 'int', 'value': 240},
                    {'name': 'ISO', 'type': 'int', 'value': 100},
                    {'name': 'Exposure', 'type': 'int', 'value': 10},
                    {'name': 'Delay', 'type': 'int', 'value': 50, 'suffix': 'ms'},
                    ]},
                    
                    ]
        pc[1]['children'].extend([{'name': '{0}'.format(l), 'type': 'bool', 'value': False} for l in [k for k in parse_firmware_config().keys() if 'LED' in k]])
        pwm_channels = ['PWM {0}'.format(pwmc) for pwmc in ['PORTE0', 'PORTE1', 'PORTE2', 'PORTE3']]
        pc[1]['children'].extend([{'name': p, 'type': 'float', 'value': 0.0, 'suffix': '%'} for p in pwm_channels])
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
            if self.setting_values['Motor Mode']=='pwm':
                for pn in [k for k in self.setting_values.keys() if 'PWM' in k]:
                    pwm=new_values[pn]
                    if self.setting_values[pn]!=pwm and hasattr(self,'mc'):
                        self.mc.set_pwm(int(pn[-1]),int(pwm*10))
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
        
    def set_motor_action(self):
        if hasattr(self, 'mc'):
            if self.setting_values['Motor Mode']=='wheels':
                pn1='Wheel voltage'
                pn2='Wheels voltage difference'
                v=int(new_values[pn1]*10)
                d=int(new_values[pn2]*10)
                if v<0:
                    v2=v-d
                else:
                    v2=v+d
                self.mc.set_motor_voltage(1,v)
                self.mc.set_motor_voltage(2,v2)
            elif self.setting_values['Motor Mode']=='voltage':
                self.mc.set_motor_voltage(1,int(self.setting_values['Motor1 voltage'])*10)
                self.mc.set_motor_voltage(2,int(self.setting_values['Motor2 voltage'])*10)
                
    def read_adc_action(self):
        if hasattr(self, 'mc'):
            self.mc.read_adc()
            
    def stop_action(self):
        if hasattr(self, 'mc'):
            self.mc.stop()
            
    def exit_action(self):
        
        self.command.put('terminate')
        self.vs.join()
        
        self.log('Exit')
        self.close()
        
    def start_video_action(self):
        self.capture()
        
    def log(self, msg, loglevel='info'):
        getattr(logging, loglevel)(str(msg))
        self.logw.update(fileop.read_text_file(self.logfile))
        
    def capture(self):
        self.pw='hejdejo1'
        if not hasattr(self, 'pw'):
            self.pw, ok = QtGui.QInputDialog.getText(self, QtCore.QString('Password'), QtCore.QString(''), mode=QtGui.QLineEdit.Password)
        #ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('sudo python /data/capture.py {0}'.format(duration))
        pars={
                'pw':self.pw,
                'nframes':self.setting_values['N frames'],
              'width':self.setting_values['Width'],
              'height':self.setting_values['Height'],
              'iso':self.setting_values['ISO'],
              'exposure':self.setting_values['Exposure'],
              'delay':self.setting_values['Delay']}
        if 1:
            import threading
            p=threading.Thread(target=send_capture_command,kwargs=pars)
            p.start()
        else:
            send_capture_command(**pars)
        
        
def send_capture_command(**pars):
    cmd='cd /data/camera_streamer&&sudo nohup ./camera_streamer {0} {1} {2} {3} {4} {5}&'.format(pars['nframes'],pars['width'],pars['height'],pars['iso'],pars['exposure'],pars['delay'])
    logging.info(cmd)
    #return
    import paramiko
    ssh=paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.0.11', port=9127, username='rz', password=str(pars['pw']))
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd)
    e=ssh_stdout.read()
    logging.info(e)
    e=ssh_stderr.read()
    if len(e)>0:
        logging.error(e)
#    except:
#        pass
    
class VideoStreamer(multiprocessing.Process):
    def __init__(self,image, command):
        self.image=image
        self.command=command
        multiprocessing.Process.__init__(self)
        
    def run(self):
        import socket,io,numpy
        from PIL import Image
        from StringIO import StringIO
        UDP_IP = ""
        UDP_PORT = 8000
        sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        sock.bind((UDP_IP, UDP_PORT))
        sock.settimeout(0.3)
        buffer=''
        framect=0
        while True:
            if not self.command.empty():  
                print self.command.get()
                break
            try:
                data, addr = sock.recvfrom(int(2**16))
                buffer=data
                start=buffer.find('start')
                end=buffer.find('end')
                if start!=-1 and end!=-1:
                    #logging.info((start,end,len(data)))
                    if end<start :
                        #buffer=buffer[end:]
                        pass
                    else:
                        img=buffer[start+5:end]
                        img=numpy.asarray(Image.open(StringIO(img)))
                        #buffer=buffer[end:]
                        framect+=1
                        #if framect>10:
                        self.image.put(img)
            except:
                if 0: logging.error(traceback.format_exc())
        sock.close()

if __name__ == '__main__':
    RemoteControl()
