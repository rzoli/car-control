'''
This module implements a command/remote function call interface via serial port and tcp/ip socket using the following protocol:
    <command/function name>(<parameter1>,<parameter2>)
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
        eoc_index = self.buffer.find('(')
        eop_index = self.buffer.find(')')
        if eoc_index == -1 or eop_index == -1:
            #packet is not ready
            return
        if eoc_index < eop_index:
            command = self.buffer[:eoc_index]
            parameters = self.buffer[eoc_index+1:eop_index].split(',')
            parsed_command = {}
            parsed_command['command'] = command
            parsed_command['args'] = parameters
            self.buffer=self.buffer.replace(self.buffer[:eop_index+1],'')
            self.parsed_commands.put(parsed_command)
        else:
            raise RuntimeError('This command cannot be parsed: {0}'.format(self.buffer))
        pass
        
    def send_command(self, command, *args):
        '''
        args shall contain only strings or numeric values
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
            
        message = '{0}({1})'.format(command, parameters[:-1])
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
        self.p.send_command('cmd', par1, par2, par3, par4)
        self.assertEqual(self.p.queue_out.get(),'cmd(a,1,123.0,abc)')
        
    def test_02_invalid_datatype(self):
        par1=['a']
        par2=1
        par3=123.0
        par4='abc'
        self.assertRaises(RuntimeError, self.p.send_command, 'cmd', par1, par2, par3, par4)
        
    def test_03_invalid_datatype(self):
        par1='a'
        par2=1
        par3=[123.0]
        par4='abc'
        self.assertRaises(RuntimeError, self.p.send_command, 'cmd', par1, par2, par3, par4)
        
    def test_04_invalid_string(self):
        par1='a,'
        par2=1
        par3=[123.0]
        par4='abc'
        self.assertRaises(RuntimeError, self.p.send_command, 'cmd', par1, par2, par3, par4)
        
    def test_06_parse(self):
        for c in 'cmd(a,1,abc,123.0)':
            self.p.queue_in.put(c)
        self.p.parse()
        self.assertEqual(self.p.parsed_commands.get(), {'args': ['a', '1', 'abc', '123.0'], 'command': 'cmd' })
        
    def test_07_parse(self):
        for c in 'cmd(a,1,abc,123.0)cde':
            self.p.queue_in.put(c)
        self.p.parse()
        self.assertEqual(self.p.parsed_commands.get(), {'args': ['a', '1', 'abc', '123.0'], 'command': 'cmd'})
        
class TestSerialPortHandler(unittest.TestCase):
    '''
    These tests assume that a serial port is connected wired in loopback
    '''
        
    def test_01_serial_port_loopback(self):
        '''
        This test expects that the microcontroller is connected or at least a serial port is connected in loopback mode
        '''
        self.s=SerialPortHandler('/dev/ttyUSB0',115200,0.1,Queue.Queue(),Queue.Queue(),Queue.Queue())
        self.s.queue_out.put('abc()echo(12345)cde')
        self.s.queue_out.put('abc12345()echo(67890)cde')
        self.s.start()
        time.sleep(1)
        self.s.terminate=True
        self.s.join()
        self.assertEqual((self.s.parsed_commands.get(timeout=1),self.s.parsed_commands.get(timeout=1)),
                            ({'args': ['12345'], 'command': 'echo'},
                            {'args': ['67890'], 'command': 'echo'}))
        

if __name__ == "__main__":
    unittest.main()
