#TODO: very slow above 100 ms timebases
#TODO: eliminate periodic signal runs on screen
#measure timer isr runtime->15 us
#measure timer isr frq->25 kHz, considering 14.7456 MHz clock speed
import numpy,time
import serial
import PyQt4.Qt as Qt
import PyQt4.QtGui as QtGui
import PyQt4.QtCore as QtCore
import pyqtgraph
from visexpman.engine.generic import gui


class CWidget(QtGui.QWidget):
    '''
    The central widget of the user interface which contains the image, the plot and the various controls for starting experiment or adjusting parameters
    '''
    def __init__(self,parent):
        QtGui.QWidget.__init__(self,parent)
        self.start_stop=QtGui.QPushButton('Start' ,parent=self)
        self.plotw=gui.Plot(self)#Plot widget initialization
        self.plotw.setFixedHeight(250)
        self.plotw.plot.setLabels(left='pin number-1', bottom='time [ms]')#Adding labels to the plot
        self.channelselect=[gui.LabeledCheckBox(self,'{0}'.format(i)) for i in range(8)]
        self.analog_selected=gui.LabeledCheckBox(self,'Analog')
        self.l = QtGui.QGridLayout()#Organize the above created widgets into a layout
        self.l.addWidget(self.plotw, 0, 0, 1, 5)
        self.l.addWidget(self.start_stop, 1, 0, 1, 1)
        self.l.addWidget(self.analog_selected, 1, 1, 1, 1)
        for i in range(len(self.channelselect)):
            self.l.addWidget(self.channelselect[i], 2+i/4, i%4, 1, 1)
        
        self.setLayout(self.l)


class OScope(gui.SimpleAppWindow):
    '''
    Main application class and main thread of the behavioral control software.
    '''
    def init_gui(self):
        self.setWindowTitle('Oscilliscope')
        self.cw=CWidget(self)#Creating the central widget which contains the image, the plot and the control widgets
        self.cw.setMinimumHeight(500)#Adjusting its geometry
        self.cw.setMinimumWidth(1100)
        self.setCentralWidget(self.cw)#Setting it as a central widget
        self.debugw.setMinimumWidth(800)#Setting the sizes of the debug widget. The debug widget is created by gui.SimpleAppWindow class which is 
        self.debugw.setMinimumHeight(250)#the superclass of Behavioral. The debug widget displays the logfile and provides a python console
        self.setMinimumWidth(1200)#Setting the minimum size of the main user interface
        self.setMinimumHeight(750)
        
        self.fsample=25e3
        self.timebase=10e-3#s
        self.ts=1.0/self.fsample
        try:
            self.s=serial.Serial('/dev/ttyACM0',baudrate=921600,timeout=1)
        except serial.SerialException:
            self.s=serial.Serial('/dev/ttyACM1',baudrate=921600,timeout=1)
        
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.read_samples)
        self.timer.start(int(1000.*self.timebase))
        self.connect(self.cw.start_stop, QtCore.SIGNAL('clicked()'), self.start_stop)
        self.run=False
        
    def start_stop(self):
        self.run = False if self.run else True
        self.cw.start_stop.setText('Start' if not self.run else 'Stop')
        
    def read_samples(self):
        if not self.run:
            return
        self.timer.setInterval(int(1000.*self.timebase))
        if not self.s.isOpen():
            return
        self.s.setTimeout(2*self.timebase)
        self.nsamples=int(self.timebase/self.ts)
        r=self.s.read(self.nsamples)
        self.data=numpy.fromstring(r,dtype=numpy.uint8)
        #self.data = self.data.reshape(self.nsamples,2)
        
        self.t=numpy.linspace(0,self.timebase,self.nsamples)*1e3
        
#        if numpy.diff(self.data[:,0]).min()!=1 and numpy.diff(self.data[:,0]).max()!=254 and 0:
#            self.log('some samples may be missing','warning')
#            return
        self.cw.plotw.plot.setTitle(format(self.data[-1], '#010b'))
        if self.cw.analog_selected.input.checkState()==2:
            y=self.data*(5.0/256)
            x=self.t
            self.cw.plotw.update_curve(x,y)
            self.cw.plotw.plot.setYRange(0, 5.0)
        else:
            enabled_channels = [w.input.checkState()==2 for w in self.cw.channelselect]
            if sum(enabled_channels)==0:
                return
            x=sum(enabled_channels)*[self.t]
            y=[numpy.where(numpy.bitwise_and(self.data,numpy.array(self.nsamples*[1<<b],dtype=numpy.uint8))==0,0,b+1) for b in range(8) if enabled_channels[b]]
            refcolors=[(255,0,0),(0,255,0),(0,0,255),(0,0,0),(0,255/2,255/2),(255,0,255),(255/2,255/2,0),(127,127,255)]
            c=[refcolors[ci] for ci in range(8) if enabled_channels[ci]]
            self.cw.plotw.update_curves(x,y,colors=c)
            self.cw.plotw.plot.setYRange(0, 8)
        
    def closeEvent(self, e):
        self.s.close()
        e.accept()

if __name__ == '__main__':
    gui = OScope()
