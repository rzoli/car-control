#include <ctype.h>
#include <avr/interrupt.h>
#include <avr/io.h>
#include <string.h>
#include <stdlib.h>
#include "usart_driver.h"
#include "utils.h"
#include "comm.h"
#include "config.h"
//#include "../command_protocol.h"

USART_data_t USART_data;//If passed as pointer to Comm, does not work
TC0_t* motor;

int Comm::uart_putchar(char c) {
    USART_TXBuffer_PutByte(&USART_data, c);
    return 0;
}

char Comm::getchr(void)
{    
	char res = 0U;
    
	 if (USART_RXBufferData_Available(&USART_data)) {
			res = USART_RXBuffer_GetByte(&USART_data);
	 }
	 return (res);
}

Comm& Comm::operator <<(char* pBuffer)
{
    for(uint8_t i=0;i<strlen(pBuffer);i++)
    {
        uart_putchar(pBuffer[i]);
    }
	return *this;
}

Comm& Comm::operator <<(unsigned int uiVal)
{
	char aIntBuff[6];
	itoa(uiVal, aIntBuff,10);
	*this << aIntBuff;
	return *this;
}

DeviceCommands::DeviceCommands(void)
{
    //TODO: pointers to rpm counters
}

void DeviceCommands::echo(uint8_t par)
{
    *this<<"echo("<<par<<")";
}

void DeviceCommands::set_pwm(uint8_t channel, uint16_t pulsewidth_forward, uint16_t pulsewidth_backward)
{
    static int forward_register, reverse_register;
    if ((pulsewidth_forward > 1000) || (pulsewidth_backward > 1000))
    {
        *this<<"set_pwm("<<MORE_THAN_100_PERCENT_DUTY_CYCLE_REQUESTED << ")";
        return;
    }
    forward_register = (int)(pulsewidth_forward*1e-3*PWM_PERIOD_REGISTER_VALUE);
    reverse_register = (int)(pulsewidth_backward*1e-3*PWM_PERIOD_REGISTER_VALUE);
    if (pulsewidth_forward==0)
        forward_register = 0;
    if (pulsewidth_backward==0)
        reverse_register = 0;
    switch (channel)
    {
        case LEFT_MOTOR:
            //Left side motor control
            motor->CCA = forward_register;
            motor->CCB = reverse_register;
            break;
        case RIGHT_MOTOR:
            //Right side motor control
            motor->CCC = forward_register;
            motor->CCD = reverse_register;
            break;
        default:
            //Do nothing
            break;
    }
    *this<<"set_pwm("<<channel <<","<<forward_register<<","<<reverse_register<<","<<pulsewidth_forward<<","<<pulsewidth_backward<<")";
}

uint8_t DeviceCommands::next_command(void)
{
    static char c;
    c = getchr();
    if (c>0)
        put(c);
        if (parse()) {
            if (strcmp(command.name, "echo") == 0)
                echo(command.parameters[0]);
            else if (strcmp(command.name, "set_pwm") == 0)
                set_pwm((uint8_t)command.parameters[0], command.parameters[1], command.parameters[2]);
            
            
  //          comm << cp.command.name<<"\t"<<cp.command.nparameters<<"\n";
        }
    return 0;
}
