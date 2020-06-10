from PIL import Image
import numpy,scipy,socket
import os
import time
import tempfile
import logging
import sys
import traceback
try:
    import PyQt4.Qt as Qt
    import PyQt4.QtGui as QtGui
    import PyQt4.QtCore as QtCore
    import Queue
except:
    import PyQt5.Qt as Qt
    import PyQt5.QtGui as QtGui
    import PyQt5.QtCore as QtCore
    import queue as Queue
from visexpman.engine.generic import gui, fileop,utils
from motor_drive.firmware_test import parse_firmware_config
import multiprocessing

ADC_CALIB=numpy.array([
    [6, 	1833, 	0.403, 	0.284],
    [7, 	2126, 	0.473, 	0.285],
    [8, 	2421, 	0.544, 	0.285],
    [9, 	2704, 	0.615, 	0.286],
    [10, 	3005, 	0.686, 	0.286]])

def excepthook(excType, excValue, tracebackobj):
    msg='\n'.join(traceback.format_tb(tracebackobj))+str(excType.__name__)+': '+str(excValue)
    print (msg)
    error_messages.put(msg)
    
sys.excepthook = excepthook


error_messages = Queue.Queue()

def socket_client(cmd, ip, port=20000):
    print(cmd)
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(1)
    client.connect((ip, port))
    client.send(cmd.encode())
    from_server = client.recv(4096)
    client.close()
    return from_server.decode('utf-8')

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
        self.toolbar = gui.ToolBar(self, ['connect', 'echo', 'set_motor', 'read_steps', 'backward', 'forward', 'turn_left', 'turn_right', 'run_maneuver', 'read_adc', 'start_video', 'stop', 'exit'], icon_folder = icon_folder)
        self.addToolBar(self.toolbar)
        self.console = gui.PythonConsole(self, selfw = self)
        self.console.setMinimumWidth(700)
        self.console.setMinimumHeight(200)
        self._add_dockable_widget('Console', QtCore.Qt.BottomDockWidgetArea, QtCore.Qt.BottomDockWidgetArea, self.console)
        self.logw = gui.TextOut(self)
        self.logw.setMinimumWidth(400)
        self._add_dockable_widget('Log', QtCore.Qt.BottomDockWidgetArea, QtCore.Qt.BottomDockWidgetArea, self.logw)
        self.settings = gui.ParameterTable(self, self._get_params_config())
        self.settings.setMinimumWidth(300)
        self.settings.params.sigTreeStateChanged.connect(self.settings_changed)
        self.settings_changed()
        self._add_dockable_widget('Settings', QtCore.Qt.RightDockWidgetArea, QtCore.Qt.RightDockWidgetArea, self.settings)
        self.image=gui.Image(self)
        self.image.setFixedWidth(500)
        self.image.setMaximumHeight(500)
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
        
        self.lut=scipy.interpolate.interp1d(ADC_CALIB[:,1], ADC_CALIB[:,0],bounds_error=False, fill_value='extrapolate')
        
        if QtCore.QCoreApplication.instance() is not None:
            QtCore.QCoreApplication.instance().exec_()
            
    def cmd(self,cmd, pars=[]):
        if self.setting_values['params/Microcontroller/Connection'] == 'tcp/ip':
            ip=self.setting_values['params/Microcontroller/Serial port']
            cmdout=cmd
            if len(pars)>0:
                cmdout+=',{0}'.format(','.join(map(str,pars)))
            cmdout+='\r\n'
            return socket_client(cmdout, ip)
        elif self.setting_values['params/Microcontroller/Connection'] == 'serial port':
            self.s.write(cmd)
            if len(pars)>0:
                    self.s.write(',{0}'.format(','.join(map(str,pars))))
            self.s.write('\r\n')
            return self.s.readline()
            
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
                    {'name': 'Serial port', 'type': 'str', 'value': '192.168.1.11'},
                    {'name': 'Connection', 'type': 'list', 'values': ['serial port', 'tcp/ip'], 'value': 'tcp/ip'},
                    {'name': 'Timeout', 'type': 'float', 'value': 0.5, 'suffix': 's'},
                    ]},
                {'name': 'Vehicle', 'type': 'group', 'expanded' : True, 'children': [
                    {'name': 'Default Motor Voltage', 'type': 'int', 'value': 50},
                    {'name': 'Movement Duration', 'type': 'float', 'value': 0.5},
                    {'name': 'NSteps', 'type': 'int', 'value': 1},
                    ]},
                {'name': 'Camera', 'type': 'group', 'expanded' : False, 'children': [
                    {'name': 'N frames', 'type': 'int', 'value': 100},
                    {'name': 'Width', 'type': 'int', 'value': 320},
                    {'name': 'Height', 'type': 'int', 'value': 240},
                    {'name': 'ISO', 'type': 'int', 'value': 100},
                    {'name': 'Exposure', 'type': 'int', 'value': 10},
                    {'name': 'Delay', 'type': 'int', 'value': 50, 'suffix': 'ms'},
                    ]},
                    
                    ]
        pc[0]['children'].extend([{'name': '{0}'.format(l), 'type': 'bool', 'value': False} for l in [k for k in parse_firmware_config().keys() if 'LED' in k]])
        return pc
        
    def settings_changed(self):
        new_values=self.settings.get_parameter_tree(True)
        if hasattr(self, 'setting_values'):
            #Check if LED status was changed
            for pn in [k for k in parse_firmware_config().keys() if 'LED' in k]:
                state=new_values['params/Microcontroller/'+pn]
                if self.setting_values['params/Microcontroller/'+pn]!=state:
                    self.cmd(pn[:-4].lower(),[int(state)])
        self.setting_values = new_values
        
    def connect_action(self):
        if self.setting_values['params/Microcontroller/Connection'] == 'serial port':
            if hasattr(self,'s'):
                self.log('Already open')
                return
            import serial
            self.s=serial.Serial(self.setting_values['params/Microcontroller/Serial port'], timeout=self.setting_values['params/Microcontroller/Timeout'], baudrate=parse_firmware_config()['BAUD'])
            self.log('Connected')
        
    def echo_action(self):
        if hasattr(self, 's'):
            self.log(self.cmd('ping'))
            
    def set_pwm(self, values):
        return self.cmd('set_pwm', values)
        
    def set_motor(self,v1,v2):
        if abs(v1)==100 or abs(v2)==100:
            raise RuntimeError('100 % voltage is not yet supported')
        values=[]
        if v1<0:
            values.extend([1000, 1000+int(v1*10)])
        else:
            values.extend([1000-int(v1*10),1000])
        if v2<0:
            values.extend([1000+int(v2*10),1000])
        else:
            values.extend([1000, 1000-int(v2*10)])
        self.log(self.cmd('set_pwm', values))
        
    def set_motor_action(self):
        if hasattr(self, 's'):
            return
            if self.setting_values['params/Vehicle/Motor Mode']=='wheels':
                new_values=self.settings.get_parameter_tree(True)
                pn1='Wheel voltage'
                pn2='Wheels voltage difference'
                v=int(new_values[pn1]*10)
                d=int(new_values[pn2]*10)
                if v<0:
                    v2=v-d
                else:
                    v2=v+d
                self.mc.set_motors(v-d/2,v+d/2)
            elif self.setting_values['params/Vehicle/Motor Mode']=='voltage':
                self.mc.set_motors(int(self.setting_values['params/Vehicle/Motor1 voltage'])*10,int(self.setting_values['params/Vehicle/Motor2 voltage'])*10)
                
    def read_adc_action(self):
        if hasattr(self, 's') or self.setting_values['params/Microcontroller/Connection'] == 'tcp/ip':
            raw_adc=self.cmd('read_vbatt')
            self.log('battery voltage is {0} V'.format(self.lut(raw_adc)))
            
    def stop_action(self):
        if hasattr(self, 's'):
            self.log(self.cmd('stop'))
            
    def move(self,direction):
        p=self.settings.get_parameter_tree(True)
        s=p['params/Vehicle/NSteps']
        if s>0:
            self.cmd('goto,{0}'.format(s))
        v=p['params/Vehicle/Default Motor Voltage']
        t=p['params/Vehicle/Movement Duration']
        d=1 if direction else -1
        self.set_motor(d*v,d*v)
        if s==0:
            time.sleep(t)
            self.cmd('stop')
#        self.read_steps_action()
            
    def turn(self,direction):
        p=self.settings.get_parameter_tree(True)
        v=p['params/Vehicle/Default Motor Voltage']
        t=p['params/Vehicle/Movement Duration']
        d=1 if direction else -1
        self.set_motor(d*v*1.5,-d*v*0)
        time.sleep(t)
        self.cmd('stop')
            
    def backward_action(self):
        self.move(True)
        
    def forward_action(self):
        self.move(False)
        
    def turn_left_action(self):
        self.turn(True)
        
    def turn_right_action(self):
        self.turn(False)
        
    def run_maneuver_action(self):
        pass
        
    def read_steps_action(self):
        self.log('steps '+self.cmd('read_steps'))

            
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
        
    def eval(self,res):
        values=[]
        x=[]
        y=[]
        for line in res.replace('\x00','').split('\r\n')[:-2]:
            if '\r' in line:
                lines=line.split('\r')
            else:
                lines=[line]
            for l in lines:
                r=map(int, l.split(','))
                if r[0]<500e6 and r[1]<100e6:
                    x.append(r[0])
                    y.append(r[1])
                
        from pylab import plot,show
        plot(x,y, 'x-');show()
        return x,y
        
        
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
                print (self.command.get())
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
