/*
Interface between motor controller board and host interface
*/
#include "comm.h"

class Board2HostInterface:public Comm {
    public:
        Board2HostInterface(void);
        void run(void);
        Board2HostInterface& operator << (char*);
        Board2HostInterface& operator << (unsigned int);
    private:
        void dispatch_commands(void);
        void putbyte(char c);
        char getbyte(void);
        void set_pwm(uint16_t a, uint16_t b, uint16_t c, uint16_t d);
        void stop(void);
        void read_battery_voltage(void);
        void set_led(uint8_t channel, uint8_t state);
        void reset_time(void);//resets timebase
        void read_odometer(void);
        void measure_distance(void);
        void rotate(uint8_t angle);
        void read_ultrasound_transient(void);
        void init_uart(void);
        void init_adc(void);
        void init_pwm_control(void);
        void init_clock(void);
        char c[2];
};
