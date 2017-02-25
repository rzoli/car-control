import unittest,serial,time

class TestFirmware(unittest.TestCase):
        def setUp(self):
                self.s=serial.Serial('/dev/ttyUSB0',115200, timeout=1)
                self.s.read(100)

        def tearDown(self):
                self.s.close()

        def cmd(self,cmd,pars=[]):
                self.s.write(cmd)
                if len(pars)>0:
                        self.s.write(',{0}'.format(','.join(map(str,pars))))
                self.s.write('\r\n')
                return self.s.readline()

        def test_01_commands(self):
                self.assertEqual(self.cmd('ping'),'pong\r\n')
                self.assertEqual(self.cmd('green',[1]),'green led set to 1\r\n')
                time.sleep(1)
                self.assertEqual(self.cmd('green',[0]),'green led set to 0\r\n')
                self.assertEqual(self.cmd('set_pwm',[1,2,3,4]),'pwm set to 1,2,3,4\r\n')

        def test_02_read_battery_voltage(self):
                pass
                





if __name__ == "__main__":
    unittest.main()
