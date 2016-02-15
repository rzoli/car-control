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

#define pw2reg(pulsewidth) (int)(pulsewidth*1e-3*PWM_PERIOD_REGISTER_VALUE)

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

void DeviceCommands::set_motors(uint16_t a, uint16_t b, uint16_t c, uint16_t d)
/*
Sets all the 4 pwm channels at the same time
*/
{
    char i;
    static int register_value;
    for(i=0;i<4;i++)
    {  
        switch (i)
        {
            case 0:
                register_value = pw2reg(a);
                motor->CCA = register_value;
                break;
            case 1:
                register_value = pw2reg(b);
                motor->CCB = register_value;
                break;
            case 2:
                register_value = pw2reg(c);
                motor->CCC = register_value;
                break;
            case 3:
                register_value = pw2reg(d);
                motor->CCD = register_value;
                break;
            default:
            //Do nothing
            break;
        }
    }
    *this<<"set_motors("<<a <<","<<b<<","<<c<<","<<d<<")";
        
    
    
}

void DeviceCommands::set_pwm(uint8_t channel, uint16_t pulsewidth)
{
    /*
    channel: 0...3
    pulsewidth: 0....1000
    */
    static int register_value;
    if (pulsewidth > 1000)
    {
        *this<<"set_pwm("<<MORE_THAN_100_PERCENT_DUTY_CYCLE_REQUESTED << ")";
        return;
    }
    register_value = (int)(pulsewidth*1e-3*PWM_PERIOD_REGISTER_VALUE);
    if (pulsewidth==0)
        register_value = 0;
    switch (channel)
    {
        case 0:
            //Left side motor control
            motor->CCA = register_value;
            break;
        case 1:
            //Left side motor control
            motor->CCB = register_value;
            break;
        case 2:
            //Left side motor control
            motor->CCC = register_value;
            break;
        case 3:
            //Left side motor control
            motor->CCD = register_value;
            break;
        default:
            //Do nothing
            break;
    }
    *this<<"set_pwm("<<channel <<","<<register_value<<")";
}

void DeviceCommands::stop(void)
{
    motor->CCA = 0;
    motor->CCB = 0;
    motor->CCC = 0;
    motor->CCD = 0;
    *this<<"stop()";
}

void DeviceCommands::set_led(uint8_t color, uint8_t state)
{
    if (state == 0)
    {
        PORTA.OUTSET = 1<<color;
    }
    else if (state == 1)
    {
        PORTA.OUTCLR = 1<<color;
    }
    *this<<"set_led("<<color<<","<<state<<")";
}

void DeviceCommands::read_adc(void)
{
    uint16_t val1=1000;
    uint16_t val2=2000;
    uint16_t val3=2000;
    uint16_t temp;
    uint16_t ch6;
    uint16_t ch7;
    ADCA.CH0.CTRL|=1<<7;
    ADCA.CH1.CTRL|=1<<7;
    ADCA.CH2.CTRL|=1<<7;
    
    while ((ADCA.CH0.INTFLAGS&0x1)==0) {}
    while ((ADCA.CH1.INTFLAGS&0x1)==0) {}
    while ((ADCA.CH2.INTFLAGS&0x1)==0) {}
    
    ADCA.CH0.INTFLAGS=1;
    ADCA.CH1.INTFLAGS=1;
    ADCA.CH2.INTFLAGS=1;
    
    //ADCA.INTFLAGS|=7;
    temp = ADCA.CH0.RES;
    ch6 = ADCA.CH1.RES;
    ch7 = ADCA.CH2.RES;
    val1=temp;
    val2=ch6;
    val3=ch7;
    *this<<"read_adc("<<val1<<","<<val2<<","<<val3<<")";
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
                set_pwm((uint8_t)command.parameters[0], command.parameters[1]);
            else if (strcmp(command.name, "set_motors") == 0)
                set_motors(command.parameters[0], command.parameters[1], command.parameters[2], command.parameters[3]);
            else if (strcmp(command.name, "set_led") == 0)
                set_led((uint8_t)command.parameters[0], (uint8_t)command.parameters[1]);
            else if (strcmp(command.name, "read_adc") == 0)
                read_adc();
            else if (strcmp(command.name, "stop") == 0)
                stop();

            
            
  //          comm << cp.command.name<<"\t"<<cp.command.nparameters<<"\n";
        }
    return 0;
}
