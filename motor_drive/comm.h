#include "../command_protocol.h"

class Comm
{
    public:
        int uart_putchar(char c);
        char getchr(void);
        Comm& operator << (char*);
        Comm& operator << (unsigned int);
    private:

};

class DeviceCommands: public Comm, public CommandParser
{
    public:
        DeviceCommands(void);
        uint8_t next_command(void);
        void echo(uint8_t par);
        void set_pwm(uint8_t channel, uint16_t pulsewidth);
        void set_motors(uint16_t a, uint16_t b, uint16_t c, uint16_t d);
        void set_led(uint8_t color, uint8_t state);
        void read_adc(void);
        void read_rpm(void);
        void stop(void);
    private:
};
