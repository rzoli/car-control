import serial
import time
import unittest
import command_interface

def parse_firmware_config():
    f=open('motor_drive/config.h',  'rt')
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

def test():
    time.sleep(3.0)
    print 'Firmware test started'
    fwconfig = parse_firmware_config()
    s = serial.Serial('/dev/ttyUSB0', timeout=0.5, baudrate=fwconfig['BAUD'])
    s.write('SOCechoEOC1EOP')
    print s.read(100)
    from visexpman.engine.generic import utils
    ct=0
    while not utils.enter_hit():
        ct+=1
        if not False:
            vals = [1000, 200, 100]
            for val in vals:
                cmd = 'SOCset_pwmEOCL,500,{0}EOP'.format(val)
                s.write(cmd)
                print s.read(10*len(cmd))
                time.sleep(2)
            break
        else:
            print s.read(400)
            break
    
    s.close()
    print 'Firmware test finished'

if __name__ == "__main__":
    test()
