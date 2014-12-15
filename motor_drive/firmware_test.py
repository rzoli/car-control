import numpy
import os.path
import serial
import time
import unittest
import command_interface

def parse_firmware_config():
    f=open(os.path.join(os.path.split(__file__)[0],'config.h'),  'rt')
    values = [item.split(' ') for item in f.read().replace('#define ','').split('\n')]
    config = {}
    for value in values:
        if len(value) == 2 and '//' not in value[0]:
            import string
            all=string.maketrans('','')
            nodigs=all.translate(all, string.digits)
            converted_value = value[1].translate(all, nodigs)
            if '.' in value[1]:
                converted_value = float(converted_value)
            else:
                converted_value = int(converted_value)
            config[value[0].strip()] = converted_value
    f.close()
    return config

class FirmwareTester(unittest.TestCase):
    def setUp(self):
        fwconfig = parse_firmware_config()
        self.s=command_interface.SerialPortHandler('/dev/ttyUSB0',115200,0.1,Queue.Queue(),Queue.Queue(),Queue.Queue())
        self.mc=mc=MotorControl(self.s)

    def tearDown(self):
        #Switch off measurement messages
        self.s.send_command('enable_messages', 0)
        #Make sure that all motors are stopped
        self.s.send_command('set_pwmt', 'L', 0,0)
        self.s.send_command('set_pwmt', 'R', 0,0)
        self.s.terminate=True
        self.s.join()
        
    def _get_response(self,timeout=1.0):
        time.sleep(timeout)
        return self.s.parsed_commands.get(timeout=0.01)
        
    def test_01_echo(self):
        import random
        time.sleep(3.0)#Wait till microcontroller starts up and ready to receive commands
        id = int(random.random()*1e5)
        self.s.send_command('echo', id)
        self.assertEqual(self._get_response(), {'command':'echo', 'args': [str(id)], 'kwargs': {}})
        
    def test_02_set_pwm(self):
        print 'Warning: generated waveform is not tested'
        self.s.send_command('set_pwm', 'L', 100,100)
        self.assertEqual(self._get_response(), {'command':'set_pwm', 'args': ['L', str(100), str(100)], 'kwargs': {}})

    def test_03_rpm_measurement(self):
        '''
        toggle gpio, read pulsewidth, gpio needs to be connected to capture input
        '''
        self.s.send_command('enable_messages', 1)
        
    def test_04_read_adc(self):
        self.s.send_command('enable_messages', 1)
        
class MotorControl(object):
    def __init__(self,serial_port):
        self.s=serial_port
        self.fwconfig = parse_firmware_config()
        
    def set_motor_voltage(self, channel,direction,voltage):
        '''
        channel: LEFT, RIGHT
        direction: FORWARD,BACKWARD
        voltage: PU 0...1.0
        '''
        forward_pw = int((voltage if direction == 'FORWARD' else 0)*1000)
        backward_pw = int((voltage if direction == 'BACKWARD' else 0)*1000)
        command = 'set_pwm({0},{1},{2})'.format(self.fwconfig[channel + '_MOTOR'], forward_pw, backward_pw)        
        self.s.flushInput()
        self.s.write(command)
        time.sleep(0.3)
        response = self.s.read(25)
        print response
        #TODO: check response
        
    def stop(self):
        for channel in ['LEFT','RIGHT']:
            command = 'set_pwm({0},0,0)'.format(self.fwconfig[channel + '_MOTOR'])        
            self.s.flushInput()
            self.s.write(command)
            response = self.s.read(25)
            print response
        
    def set_motor_speed(self,channel,speed):
        '''
        '''
        

        
def test():
    time.sleep(3.0)
    print 'Firmware test started'
    fwconfig = parse_firmware_config()
    s = serial.Serial('/dev/ttyUSB0', timeout=0.5, baudrate=fwconfig['BAUD'])
    #Test motor
    mc=MotorControl(s)
    s.write('echo(1)')
    for v in numpy.arange(0,1,0.1):
        mc.set_motor_voltage('LEFT', 'BACKWARD', v)
        time.sleep(1)
    mc.stop()
    #Test something else
    
    s.close()
    print 'Firmware test finished'

if __name__ == "__main__":
    test()
