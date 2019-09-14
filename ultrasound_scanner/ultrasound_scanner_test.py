import serial,unittest,time
class UltrasoundScannerTester(unittest.TestCase):
    def setUp(self):
        self.s=serial.Serial('/dev/ttyACM0',115200,timeout=1)
        
    def test_01(self):
        self.s.write('ping\r\n')
        time.sleep(0.1)
        print self.s.readline()
        
    def tearDown(self):
        self.s.close()



if __name__ == "__main__":
    unittest.main()
