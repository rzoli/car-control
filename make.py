import sys
import os.path
import os
import subprocess
source_files = ['main.c', 'clksys_driver.c',  'usart_driver.c',  'utils.c']#'usart_driver.c',  'clksys_driver.c']
output_file = 'fw'
mcu = 'atxmega32a4'
optimization_level = 's'
firmware_folder = 'motor_drive'

def clean():
    [os.remove(f) for f in os.listdir(os.getcwd()) if '.hex' in f or '.map' in f or '.elf' in f]
    [os.remove(os.path.join(firmware_folder, f)) for f in os.listdir(firmware_folder) if '.hex' in f or '.map' in f or '.elf' in f]
    
def compile():
    '''
    -ffunction-sections in compile and -Wl,-gc-sections in linking will remove unused code
    '''
    clean()
    objects = ''
    for f in source_files:
        f = os.path.join(firmware_folder,  f)
        subprocess.call('avr-gcc -ffunction-sections -mmcu={0} -Wall -O{1} -c -o {2}.elf {3}'.format(mcu, optimization_level, f.split('.')[0],  f),
                         shell=True)
        objects += ' ' +f.replace('.c', '.elf')
        if not os.path.exists(f.replace('.c', '.elf')):
            return False
    subprocess.call('avr-gcc -Wl,-gc-sections -mmcu={0} -Wall {1} -o {2}.elf' .format(mcu, objects,  output_file), shell=True)
    subprocess.call('avr-objcopy -j .text -j .data -O ihex {0}.elf {0}.hex'.format(output_file), shell=True)
    if not os.path.exists(output_file+'.hex'):
        return False
    subprocess.call('avr-size {0}.elf'.format(output_file), shell=True)
    print 'Build OK'
    return True
    
def program_device(reset=False):
    if reset:
        reset_options = '-D -n'
    else:
        reset_options = ''
    subprocess.call('avrdude {0} -p x32a4 -c avrisp2 -P usb -U flash:w:{1}.hex'.format(reset_options, output_file), shell=True)

if __name__ == "__main__":
    if '--reset' in sys.argv:
        program_device(reset=True)
    elif compile() and '--download' in sys.argv:
        program_device()
    if '--test' in sys.argv:
        import unittest_aggregator
        unittest_aggregator.test()
