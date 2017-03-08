import serial,zmq,unittest,threading,sys,time

def run(port, serialport):
    s=serial.Serial(serialport, 115200, timeout=0.5)
    context = zmq.Context()
    socket = context.socket(zmq.PAIR)
    socket.bind("tcp://*:%s" % port)

    while True:
        serin=s.readline()
        if len(serin)>0:
            print 'serin', serin
            socket.send(serin)
        try:
            zmqin=socket.recv(flags=zmq.NOBLOCK)
            if 'exit\r\n' in zmqin:
                break
            elif len(zmqin)>0:
                print 'zmqin', zmqin
                s.write(zmqin)
        except zmq.ZMQError:
            pass
        
    s.close()



class Test(unittest.TestCase):
    def test(self):
        context = zmq.Context()
        socket = context.socket(zmq.PAIR)
        th=threading.Thread(target=run,args=(19000, '/dev/ttyUSB0'))
        th.start()
        socket.connect("tcp://{0}:{1}".format('localhost', 19000))
        socket.send('test1')
        socket.send('test2')
        socket.send('ping\r\n')
        time.sleep(2)
        for i in range(5):
            print i
            try:
                print socket.recv(flags=zmq.NOBLOCK)
            except:
                print 'err'
            time.sleep(1)
        socket.send('exit\r\n')
        th.join()
        print 'done'
        

if __name__ == '__main__':
    if len(sys.argv)==1:
        unittest.main()
    else:
        run(sys.argv[1], sys.argv[2])
