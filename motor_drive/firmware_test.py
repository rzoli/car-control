import serial
import time

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

def test():
    time.sleep(3.0)
    print 'Firmware test started'
    fwconfig = parse_firmware_config()
    s = serial.Serial('/dev/ttyUSB0', timeout=0.5, baudrate=fwconfig['BAUD'])
    s.write('SOChost_readyEOCEOP')
    from visexpman.engine.generic import utils
    ct=0
    while not utils.enter_hit():
        ct+=1
        if not False:
            vals = [1, 10,  100, 1000, 200]
            for val in vals:
                cmd = 'SOCset_pwmEOCL,500,{0}EOP'.format(val)
                s.write(cmd)
                print s.read(10*len(cmd))
                time.sleep(5)
            break
        else:
            print s.read(400)
            break
    
    s.close()
    print 'Firmware test finished'

if __name__ == "__main__":
    test()
