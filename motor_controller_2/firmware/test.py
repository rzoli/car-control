import unittest,serial,time,numpy,scipy.interpolate

ADC_CALIB=numpy.array([
    [6, 	1833, 	0.403, 	0.284],
    [7, 	2126, 	0.473, 	0.285],
    [8, 	2421, 	0.544, 	0.285],
    [9, 	2704, 	0.615, 	0.286],
    [10, 	3005, 	0.686, 	0.286]])


class TestFirmware(unittest.TestCase):
        def setUp(self):
                self.s=serial.Serial('/dev/ttyUSB0',115200, timeout=1)
                self.s.read(100)
                self.lut=scipy.interpolate.interp1d(ADC_CALIB[:,1], ADC_CALIB[:,0],bounds_error=False, fill_value='extrapolate')

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
            self.assertEqual(self.cmd('set_pwm',[500,2,3,400]),'pwm set to 500,2,3,400\r\n')
            twait=100
            res = self.cmd('test_micros', [twait])
            dt=int(res.split(' ')[-1])/1000.
            self.assertAlmostEqual(twait, dt,-1)
                
        def test_02_reset(self):
            t1=int(self.cmd('micros'))
            print self.cmd('reset')
            time.sleep(1.0)
            print self.s.read(10)
            t2=int(self.cmd('micros'))
            self.assertTrue(t1>t2)

        def test_03_read_battery_voltage(self):
            raw_adc=int(self.cmd('read_vbatt'))
            print raw_adc
            if 1:
                vref=1.1#3.3/1.6
                adc_bits=12
                verr=0.09*0
            else:
                raw_adc&=0x7ff
                vref=3.3/1.6
                adc_bits=11
                verr=0
            vd1=0.277
            r101=39e3
            r100=510e3
            vadc=vref*(raw_adc/2.0**adc_bits)-verr
            print vadc
            vbatt=((r100+r101)/r101)*vadc+vd1
            print 'battery voltage is {0} V'.format(self.lut(raw_adc))
            n=10
            tsamplen = float(self.cmd('meas_tsample', [n]))
            print 'sample time is {0} us'.format(tsamplen/n)

        def test_04_set_pwm(self):
            v=750
            print self.cmd('set_pwm', [1000,v,v,1000])
            time.sleep(4)
            print self.cmd('set_pwm', [v,1000,1000,v])
            time.sleep(4)
            print self.cmd('stop')

if __name__ == "__main__":
    unittest.main()
