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
        void set_pwm(uint8_t channel, uint16_t pulsewidth_forward, uint16_t pulsewidth_backward);
    private:
};
