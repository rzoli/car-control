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

DeviceCommands::DeviceCommands(TC0_t* left_motor, TC0_t* right_motor)
{
    right_motor = right_motor;
    left_motor = left_motor;
    //TODO: pointers to rpm counters
}

void DeviceCommands::echo(uint8_t par)
{
    *this<<"echo("<<par<<")";
}

void DeviceCommands::set_pwm(char channel, uint16_t pulsewidth_forward, uint16_t pulsewidth_reverse)
{
    static int forward_register, reverse_register;
    if ((pulsewidth_forward > 1000) || (pulsewidth_reverse > 1000))
    {
        *this<<"set_pwm("<<MORE_THAN_100_PERCENT_DUTY_CYCLE_REQUESTED << ")";
        return;
    }
    forward_register = (int)(pulsewidth_forward*1e-3*PWM_PER_VALUE);
    reverse_register = (int)(pulsewidth_reverse*1e-3*PWM_PER_VALUE);
    switch (channel)
    {
        case 'L':
            //Left side motor control
            left_motor->CCA = forward_register;
            left_motor->CCB = reverse_register;
            break;
        case 'R':
            //Right side motor control
            right_motor->CCA = forward_register;
            right_motor->CCB = reverse_register;
            *this<<"set_pwm("<< WARNING_RIGHT_MOTOR_NOT_CONFIGURED << ")";
            break;
        default:
            //Do nothing
            break;
    }
    *this<<"set_pwm("<<channel <<","<<forward_register<<","<<reverse_register<<","<<pulsewidth_forward<<","<<pulsewidth_reverse<<")";
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
                set_pwm((char)command.parameters[0], command.parameters[1], command.parameters[2]);
            
            
  //          comm << cp.command.name<<"\t"<<cp.command.nparameters<<"\n";
        }
    return 0;
}
