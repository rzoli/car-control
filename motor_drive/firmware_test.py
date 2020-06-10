import numpy
import os.path
import serial
import time
import random
import tempfile
import logging
import pdb
import unittest
import command_interface

def parse_firmware_config():
    f=open(os.path.join(os.path.split(__file__)[0],'config.h'),  'rt')
    values = [item.split(' ') for item in f.read().replace('#define ','').split('\n')]
    config = {}
    for value in values:
        if len(value) == 2 and '//' not in value[0]:
            try:
                import string
                all=string.maketrans('','')
                nodigs=all.translate(all, string.digits)
                converted_value = value[1].translate(all, nodigs)
            except:
                converted_value = ''.join([si for si in value[1] if si.isdigit() or si =='.'])
            if '.' in value[1]:
                converted_value = float(converted_value)
            else:
                converted_value = int(converted_value)
            config[value[0].strip()] = converted_value
    f.close()
    return config


class MotorControl(object):
    '''
    This class is repsonsible for issueing commands to the motor controller board. Besides motor voltage setting other 
    functions of the board are implemented here like led toggling, adc readout etc
    '''
    def __init__(self,serial_port):
        self.s=serial_port
        self.fwconfig = parse_firmware_config()
        
    def parse_parameters(self,s):
        return s.split('(')[1].split(')')[0].split(',')
        
    def send_command(self,command):
        self.s.flushInput()
        self.s.write(command)
        logging.info('command send: {0}'.format(command))
        
    def set_pwm(self,channel,pulse_width):
        command = 'set_pwm({0},{1})'.format(channel, int(pulse_width))
        self.send_command(command)
        time.sleep(0.1)
        response = self.s.read(len(command)*2)
        logging.info('response: {0}'.format(response))
        resp_par = self.parse_parameters(response)
        cmd_par = self.parse_parameters(command)
        return resp_par[0] == cmd_par[0] and resp_par[-2:] == cmd_par[-2:]
        
    def set_motor_voltage(self,channel,voltage):
        logging.info('set_motor_voltage({0},{1})'.format(channel,voltage))
        self.motor2pwm_channel=2*(channel-1)
        if voltage>0:
            self.pwm_channel1=self.motor2pwm_channel
            self.pwm_channel2=self.motor2pwm_channel+1
        else:
            self.pwm_channel1=self.motor2pwm_channel+1
            self.pwm_channel2=self.motor2pwm_channel
        if voltage==0:
            self.set_pwm(self.pwm_channel1,0)
            self.set_pwm(self.pwm_channel2,0)
        else:
            self.set_pwm(self.pwm_channel1,1000-abs(voltage))
            self.set_pwm(self.pwm_channel2,1000)
            
    def set_motors(self, voltage_left, voltage_right):
        logging.info('set_motors({0},{1})'.format(voltage_left,voltage_right))
        if voltage_left<0:
            a=1000-abs(voltage_left)
            b=1000
        else:
            b=1000-abs(voltage_left)
            a=1000
        if voltage_right<0:
            c=1000-abs(voltage_right)
            d=1000
        else:
            d=1000-abs(voltage_right)
            c=1000
        command = 'set_motors({0},{1},{2},{3})'.format(int(a),int(b),int(c),int(d))
        self.send_command(command)
        time.sleep(0.1)
        response = self.s.read(len(command))
        logging.info('response: {0}'.format(response))
        resp_par = self.parse_parameters(response)
        cmd_par = self.parse_parameters(command)
        return resp_par == cmd_par
            
        
        
        
    def stop(self):
        for channel in ['LEFT','RIGHT']:
            command = 'stop()'
            self.send_command(command)
            response = self.s.read(len(command)+4)
            logging.info('response: {0}'.format(response))
            time.sleep(0.1)
            return response == command
        
    def set_motor_speed(self,channel,speed):
        '''
        '''

    def set_led(self, color,state):
        col_str = color.upper() + '_LED'
        if not self.fwconfig.has_key(col_str):
            raise RuntimeError('Invalid led color: {0}', format(color))
        command = 'set_led({0},{1})'.format(self.fwconfig[col_str],int(state))
        self.send_command(command)
        response = self.s.read(len(command))
        logging.info('response: {0}'.format(response))
        return response == command
        
    def echo(self, value):
        command = 'echo({0})'.format(value)
        self.send_command(command)
        response = self.s.read(len(command))
        logging.info('response: {0}'.format(response))
        return response == command
        
    def read_adc(self):
        command = 'read_adc()'
        self.send_command(command)
        response = self.s.read(len(command)+3*5)
        logging.info('response: {0}'.format(response))
        return response
        
    def read_rpm(self):
        pass

class FirmwareTester(unittest.TestCase):
    def __init__(self,*args, **kwargs):
        unittest.TestCase.__init__(self,*args, **kwargs)
        logging.basicConfig(filename=os.path.join(tempfile.gettempdir(), 'robot_firmware_test_{0}.txt'.format(int(time.time()))),
                    format='%(asctime)s %(levelname)s\t%(message)s',
                    level=logging.DEBUG)
    
    def setUp(self):
        logging.info('Beginning of {0}' .format(self._testMethodName))
        self.serial_port_timeout = 0.5
        fwconfig = parse_firmware_config()
        self.s=serial.Serial('/dev/ttyUSB0', timeout=self.serial_port_timeout, baudrate=fwconfig['BAUD'])
        self.mc=mc=MotorControl(self.s)
        time.sleep(3.0)#Wait till microcontroller starts up and ready to receive commands

    def tearDown(self):
        #turn off leds
        map(self.mc.set_led, ['green', 'red'],[0,0])
        #Make sure that all motors are stopped
        if not self.mc.stop():
            raise RuntimeError('Motors did not stop')
        self.s.close()
        logging.info('End of {0}'.format(self._testMethodName))
        
    def test_01_echo(self):
        self.assertTrue(self.mc.echo(int(random.random()*255)))
        
    def test_02_measure_response_time(self):
        t0=time.time()
        res = self.mc.echo(int(random.random()*255))
        dt = time.time()-t0
        self.echo_response_time=dt
        print (dt)
        self.assertLess(dt, self.serial_port_timeout +0.1)
        self.assertTrue(res)
        
    def test_03_set_led(self):
        res = []
        for i in range(2):
            res.append(self.mc.set_led('red',i%2))
            res.append(self.mc.set_led('green',not bool(i%2)))
        map(self.assertTrue,res)
        
    def test_04_set_motor_voltage(self):
        res = []
        for v in numpy.arange(0,1,0.3):
            res.append(self.mc.set_motor_voltage('LEFT', 'BACKWARD', v))
            res.append(self.mc.set_motor_voltage('LEFT', 'FORWARD', v))
        map(self.assertTrue,res)
        
    def test_05_read_adc(self):
        self.mc.read_adc()
        
    def test_06_read_rpm(self):
        pass

if __name__ == "__main__":
    unittest.main()
