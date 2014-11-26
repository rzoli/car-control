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
        DeviceCommands(TC0_t* left_motor, TC0_t* right_motor);
        uint8_t next_command(void);
    private:
        void echo(uint8_t par);
        void set_pwm(char channel, uint16_t pulsewidth_forward, uint16_t pulsewidth_reverse);
        TC0_t* left_motor;
        TC0_t* right_motor;
};
