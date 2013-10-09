'''
This module implements a command/remote function call interface via serial port and tcp/ip socket using the following protocol:
    SOC<command/function name>EOC<parameters>EOP
    Parameters:par1,par2,....parn, kwpar1=parA,kwpar2=parB....
'''
import os
import serial
import threading
import time
import Queue
import unittest

class ProtocolHandler(object):
    '''
    Assembles string chunks from queue_in and extracts commands
    Sends command
    parsed_commands - queue
    '''
    def __init__(self, queue_in, queue_out, parsed_commands):
        self.buffer=''
        self.parsed_commands = parsed_commands
        self.queue_out = queue_out
        self.queue_in = queue_in
        
    def parse(self):
        while not self.queue_in.empty():
            self.buffer+=self.queue_in.get()
        soc_index = self.buffer.find('SOC')
        eoc_index = self.buffer.find('EOC')
        eop_index = self.buffer.find('EOP')
        if soc_index == -1 or  eoc_index == -1 or eop_index == -1:
            #packet is not ready
            return
        if soc_index < eoc_index < eop_index:
            command = self.buffer[soc_index+3:eoc_index]
            parameters = self.buffer[eoc_index+3:eop_index].split(',')
            kw_parameters = {}
            nonkw_parameters = []
            for parameter in parameters:
                if '=' in parameter:
                    chunks = parameter.split('=')
                    kw_parameters[chunks[0]] = chunks[1]
                else:
                    nonkw_parameters.append(parameter)
            parsed_command = {}
            parsed_command['command'] = command
            parsed_command['args'] = nonkw_parameters
            parsed_command['kwargs'] = kw_parameters
            self.buffer=self.buffer.replace(self.buffer[soc_index:eop_index+3],'')
            self.parsed_commands.put(parsed_command)
        else:
            raise RuntimeError('This command cannot be parsed: {0}'.format(self.buffer))
        pass
        
    def send_command(self, command, *args, **kwargs):
        '''
        args and kwargs must contain only strings or numeric values
        '''
        parameters = ''
        valid_types=[float,int,str]
        reserved_chars = ['=', ',']
        for arg in args:
            if not any([isinstance(arg, type) for type in valid_types]):
               raise RuntimeError('{0} parameter is not valid datatype: {1}. Valid datatypes: {2}'.format(arg, type(arg),valid_types)) 
            if isinstance(arg, str) and any([c in arg for c in reserved_chars]):
               raise RuntimeError('Parameter contains reserved character: {0}'.format(arg)) 
            parameters += '{0},'.format(arg)
        for k,v in kwargs.items():
            if not any([isinstance(v, type) for type in valid_types]):
                raise RuntimeError('{0} parameter is not valid datatype: {1}. Valid datatypes: {2}'.format(v, type(v),valid_types)) 
            for item in [k,v]:
                if isinstance(item, str) and any([c in item for c in reserved_chars]):
                   raise RuntimeError('Parameter contains reserved character: {0}'.format(item)) 
            
            parameters += '{0}={1},'.format(k,v)
        message = 'SOC{0}EOC{1}EOP'.format(command, parameters[:-1])
        self.queue_out.put(message)
        
class SerialPortHandler(threading.Thread, ProtocolHandler):
    '''
    queue_in: data from serial port
    queue_out: data to serial port
    '''
    def __init__(self, port, baudrate, timeout, queue_in, queue_out, parsed_commands, read_chunk=1):
        threading.Thread.__init__(self)
        ProtocolHandler.__init__(self, queue_in, queue_out, parsed_commands)
        self.terminate=False
        self.s = serial.Serial(port, timeout=timeout, baudrate=baudrate)
        if os.name != 'nt':
            self.s.open()
        self.read_chunk = read_chunk
        
    def run(self):
        while(not self.terminate):
            if not self.queue_out.empty():
                self.s.write(self.queue_out.get())
            read_chunk = self.s.read(self.read_chunk)
            if len(read_chunk)>0:
                self.queue_in.put(read_chunk)
                self.parse()
            time.sleep(1e-3)
        self.s.close()


##################### TESTS #####################
class TestProtocolHandler(unittest.TestCase):    
    def setUp(self):
        self.p=ProtocolHandler(Queue.Queue(),Queue.Queue(),Queue.Queue())

    def test_01_protocol_handler_send_command(self):
        par1='a'
        par2=1
        par3=123.0
        par4='abc'
        self.p.send_command('cmd', par1, par2, par3=par3, par4=par4)
        self.assertEqual(self.p.queue_out.get(),'SOCcmdEOCa,1,par4=abc,par3=123.0EOP')
        
    def test_02_invalid_datatype(self):
        par1=['a']
        par2=1
        par3=123.0
        par4='abc'
        self.assertRaises(RuntimeError, self.p.send_command, 'cmd', par1, par2, par3=par3, par4=par4)
        
    def test_03_invalid_datatype(self):
        par1='a'
        par2=1
        par3=[123.0]
        par4='abc'
        self.assertRaises(RuntimeError, self.p.send_command, 'cmd', par1, par2, par3=par3, par4=par4)
        
    def test_04_invalid_string(self):
        par1='a,'
        par2=1
        par3=[123.0]
        par4='abc'
        self.assertRaises(RuntimeError, self.p.send_command, 'cmd', par1, par2, par3=par3, par4=par4)
        
    def test_05_invalid_string(self):
        par1='a'
        par2=1
        par3=[123.0]
        par4='ab=c'
        self.assertRaises(RuntimeError, self.p.send_command, 'cmd', par1, par2, par3=par3, par4=par4)
        
    def test_06_parse(self):
        for c in 'SOCcmdEOCa,1,par4=abc,par3=123.0EOP':
            self.p.queue_in.put(c)
        self.p.parse()
        self.assertEqual(self.p.parsed_commands.get(), {'args': ['a', '1'], 'command': 'cmd', 'kwargs': {'par4': 'abc', 'par3': '123.0'}})
        
    def test_07_parse(self):
        for c in 'abcSOCcmdEOCa,1,par4=abc,par3=123.0EOPcde':
            self.p.queue_in.put(c)
        self.p.parse()
        self.assertEqual(self.p.parsed_commands.get(), {'args': ['a', '1'], 'command': 'cmd', 'kwargs': {'par4': 'abc', 'par3': '123.0'}})
        
class TestSerialPortHandler(unittest.TestCase):
    '''
    These tests assume that a serial port is connected wired in loopback
    '''
        
    def test_01_serial_port_loopback(self):
        '''
        This test expects that the microcontroller is connected or at least a serial port is connected in loopback mode
        '''
        self.s=SerialPortHandler('/dev/ttyUSB0',115200,0.1,Queue.Queue(),Queue.Queue(),Queue.Queue())
        self.s.queue_out.put('abcSOCechoEOC12345EOPcde')
        self.s.queue_out.put('abc12345SOCechoEOC67890EOPcde')
        self.s.start()
        time.sleep(1)
        self.s.terminate=True
        self.s.join()
        self.assertEqual((self.s.parsed_commands.get(timeout=1),self.s.parsed_commands.get(timeout=1)),
                            ({'args': ['12345'], 'command': 'echo', 'kwargs': {}},
                            {'args': ['67890'], 'command': 'echo', 'kwargs': {}}))
        

if __name__ == "__main__":
    unittest.main()
