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
            time.sleep(0.3)
            self.assertEqual(self.cmd('green',[0]),'green led set to 0\r\n')
            self.assertEqual(self.cmd('set_pwm',[1,2,3,4]),'pwm set to 1,2,3,4\r\n')
            twait=100
            res = self.cmd('test_micros', [twait])
            dt=int(res.split(' ')[-1])/1000.
            self.assertAlmostEqual(twait, dt,-1)
                
        def test_02_reset(self):
            t1=int(self.cmd('micros'))
            print self.cmd('reset')
            time.sleep(0.5)
            print self.s.read(10)
            t2=int(self.cmd('micros'))
            self.assertTrue(t1>t2)

        def test_03_read_battery_voltage(self):
            print self.cmd('read_vbatt')
            print self.cmd('meas_sample_time', [10])

        def test_04_set_pwm(self):
            print self.cmd('set_pwm', [500,1000,100,0])
            print self.cmd('stop')
                





if __name__ == "__main__":
    unittest.main()
