/*Roadmap:
Echo
1. capture TEST
test TEST
2. timer, timer isr
3. read adc/temperature
4. move stdio to I2C (once rpi is available)

*/
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <ctype.h>
#include <avr/interrupt.h>
#include <avr/wdt.h>
#include <avr/io.h>
#include "config.h"
#include "clksys_driver.h"
#include "usart_driver.h"
#include "utils.h"
#include "comm.h"
#include <util/delay.h>
#include <string.h>
#include "../command_protocol.h"


//FILE mystdout = FDEV_SETUP_STREAM(uart_putchar, NULL, _FDEV_SETUP_WRITE);

TC0_t* left_motor;
TC0_t* right_motor;
bool rpm_capture_overflow = false;
bool new_rpm_value_left = false;
bool enable_measurement_messages = false;
uint16_t rpm_capture_left, rpm_capture_right;

extern USART_data_t USART_data;

ISR(USARTC0_RXC_vect)
{
	USART_RXComplete(&USART_data);
}

ISR(USARTC0_DRE_vect)
{
	USART_DataRegEmpty(&USART_data);
}

ISR(TCC1_OVF_vect)
{
	rpm_capture_overflow=true;
}

ISR(TCC1_CCA_vect)
{
    printf("*");
	TCC1.CNT=0U;
	if (!rpm_capture_overflow)
	{
		rpm_capture_left = TCC1.CCA;
        new_rpm_value_left = true;
	}
	else
	{
        //Does it really happen?TEST
		rpm_capture_left = RPM_MEASUREMENT_COUNTER_RELOAD_VALUE;
		rpm_capture_overflow=false;
	}
}

void init_mcu(void)
{
//    stdout = &mystdout;
    // Clock
    CLKSYS_Enable( OSC_RC2MEN_bm );
    CLKSYS_Prescalers_Config( CLK_PSADIV_1_gc, CLK_PSBCDIV_1_1_gc );
    do {} while ( CLKSYS_IsReady( OSC_RC2MRDY_bm ) == 0 );
    CLKSYS_Main_ClockSource_Select( CLK_SCLKSEL_RC2M_gc );
    //IO ports
    PORTA.DIRSET = 1<<GREEN_LED | 1 << RED_LED;
    PORTA.OUTSET = 1<<GREEN_LED | 1 << RED_LED;
    //USART C0
    /* PC3 (TXD0) as output. */
	PORTC.DIRSET   = PIN3_bm;
	/* PC2 (RXD0) as input. */
	PORTC.DIRCLR   = PIN2_bm;
    USART_InterruptDriver_Initialize(&USART_data, &USARTC0, USART_DREINTLVL_LO_gc);

	/* USARTC0, 8 Data bits, No Parity, 1 Stop bit. */
	USART_Format_Set(USART_data.usart, USART_CHSIZE_8BIT_gc,
                     USART_PMODE_DISABLED_gc, false);
    
	/* Enable RXC interrupt. */
	USART_RxdInterruptLevel_Set(USART_data.usart, USART_RXCINTLVL_LO_gc);
	
	/* set baud */
	USART_Baudrate_Set(&USARTC0, 149 , -7);
    USARTC0.CTRLB |= USART_CLK2X_bm;

	/* Enable both RX and TX. */
	USART_Rx_Enable(USART_data.usart);
	USART_Tx_Enable(USART_data.usart);
    
    //PWM
    left_motor = &TCC0;
    right_motor = &TCE0;
    PORTC.DIRSET   = PIN0_bm|PIN1_bm;
    left_motor->CTRLA = TC_CLKSEL_DIV1_gc;
    left_motor->CTRLB = TC_WGMODE_SS_gc | 0x30; //A and B channels are enabled
    left_motor->PER = PWM_PER_VALUE;
    left_motor->CCA = 0;
    left_motor->CCB = 0;//(int)(0.13*PWM_PER_VALUE);
    
    //Input capture/rpm measurement
    //other channel might be TCE1
    TCC1.PER = RPM_MEASUREMENT_COUNTER_RELOAD_VALUE;
	TCC1.CTRLA |= TC_CLKSEL_DIV1_gc; 
    TCC1.CTRLB |= 0x10; /* select capture channel A */
    TCC1.CTRLD |= TC_EVACT_CAPT_gc | TC_EVSEL_CH0_gc; /* select capture event and event channel 0 */
	EVSYS.CH0MUX = EVSYS_CHMUX_PORTE_PIN0_gc; /* portE pin 0 */
	PORTE.DIRCLR = 0x1; /* PE0 is input */
	PORTE.PIN0CTRL = PORT_ISC_RISING_gc; /* sense rising edges */
	TCC1.INTCTRLA = 1;
	TCC1.INTCTRLB = 1;//later: medium priorityTEST
    
    /* Enable PMIC interrupt level low. */
	PMIC.CTRL |= PMIC_LOLVLEX_bm;

	/* Enable global interrupts. */
	sei();

}

void set_pwm(char channel, uint16_t pulsewidth_forward, uint16_t pulsewidth_reverse)
/*
uint16_t channel : (L)eft side, (R)ight side
uint16_t pulsewidth_forward, uint16_t pulsewidth_reverse: 1 = 0.1% duty cycle. 
                            Depending on F_CPU and F_PWM the real resolution might be lower

*/
{
    static int forward_register, reverse_register;
    if ((pulsewidth_forward > 1000) || (pulsewidth_reverse > 1000))
    {
        printf("SOCset_pwmEOC%iEOP", MORE_THAN_100_PERCENT_DUTY_CYCLE_REQUESTED);
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
            printf("SOCset_pwmEOC%iEOP",WARNING_RIGHT_MOTOR_NOT_CONFIGURED);
            break;
        default:
            //Do nothing
            break;
    }
    printf("SOCset_pwmEOC%c,%i,%i,%i,%iEOP", channel,forward_register,reverse_register,pulsewidth_forward,pulsewidth_reverse);
}

//#define PARSE_BUFFER_SIZE 32
char parse_buffer[PARSE_BUFFER_SIZE];
uint8_t parse_buffer_index = 0;
bool host_ready = false;

void parser(void)
{
    static uint8_t i, j;
    static char c;
    static char command[MAX_COMMANDLENGTH];
    static char parameters[MAX_N_PARAMS][MAX_PARAMLENGTH];
    char *p_start, *p_end, *p_soc, *p_eoc, *p_eop;
    static uint16_t pulsewidth_forward, pulsewidth_reverse;
    static uint16_t buffer;
    char channel;
    c = 'a';//getchr();
    if (c > 0)
    {
        //Reset parse buffer
        if (parse_buffer_index == 0)
        {
            uint8_t i;
            for (i=0; i<PARSE_BUFFER_SIZE;i++)
            {
                parse_buffer[i]='.';
            }
        }
        parse_buffer[parse_buffer_index] = c;
        parse_buffer_index++;
        if ((parse_buffer_index >= 10) && (strstr(parse_buffer, "SOC") != NULL) && (strstr(parse_buffer, "EOC") != NULL) && (strstr(parse_buffer, "EOP") != NULL))
        {
            //Reset command buffer
            for(i=0;i<MAX_COMMANDLENGTH;i++)
            {
                command[i] = 0;
            }
            //Reset parameters buffer 
            for(i=0;i<MAX_N_PARAMS;i++)
            {
                for(j=0;j<MAX_PARAMLENGTH;j++)
                {
                    parameters[i][j]=0;
                }
            }
            //Parse tokens
            p_soc = strstr(parse_buffer, "SOC");
            p_eoc = strstr(parse_buffer, "EOC");
            p_eop = strstr(parse_buffer, "EOP");
            if (((int)p_soc < (int)p_eoc) && ((int)p_eoc < (int)p_eop))
            {                
                //First copy command
                strncpy(command, p_soc+3, p_eoc - p_soc-3);
                //copy parameters
                p_start = p_eoc + 3;
                i = 0;
                while(1)
                {
                    p_end = strchr(p_start, ','); 
                    if (p_end) { 
                        strncpy(parameters[i], p_start, p_end-p_start);
                        parameters[i][p_end-p_start] = 0; 
                        i++; 
                        p_start = p_end + 1; 
                        if (i >= MAX_N_PARAMS)
                        {
                            break;
                        }
                    } 
                    else {
                        //p_end is rarely NULL, therefore this code is rarely executed
                        strncpy(parameters[i], p_start, p_eop-p_start);
                        break; 
                    }
                }
                parse_buffer_index = 0;
                //Call functions
                if (strcmp(command, "echo") == 0)
                {
                    host_ready = true;
                    sscanf(parameters[0], "%i", &buffer);
                    printf("SOCechoEOC%iEOP",buffer);
                }
                else if (strcmp(command, "enable_messages") == 0)
                {
//                    if (parameters[0] == '1')
//                    {
//                        enable_measurement_messages = true;
//                    }
//                    else if (parameters[0] == '0')
//                    {
//                        enable_measurement_messages = false;
//                    }
                }
                else if (strcmp(command, "set_pwm") == 0)
                {
                    channel = parameters[0][0];
                    sscanf(parameters[1], "%i", &pulsewidth_forward);
                    sscanf(parameters[2], "%i", &pulsewidth_reverse);
                    set_pwm(channel, pulsewidth_forward, pulsewidth_reverse);
                }
            }
        }
        else if (parse_buffer_index == PARSE_BUFFER_SIZE)
        {
            parse_buffer_index = 0;
        }
    }
}

bool first_run = false;

int main(void)
{    
   
    init_mcu();
    CLEAR_GREEN_LED;
    _delay_ms(500);
    SET_GREEN_LED;
    _delay_ms(500);
    CLEAR_GREEN_LED;
    SET_RED_LED;
    _delay_ms(100);
    CLEAR_RED_LED;
    _delay_ms(1000);
    
    CommandParser cp;
    cp.put('a');
    cp.parse();
    Comm comm(&USART_data);
    comm.uart_putchar('a');
    comm << "OK"<<1;

    
    while(1){ // loop forever
        comm.uart_putchar(comm.getchr());
    
//        parser();
//        if (host_ready && !first_run)
//        {
//            printf("start1\r\n");
//            printf(" %i\r\n", (int)(PWM_PER_VALUE));
//            first_run=true;
//        }
//        if (enable_measurement_messages)
//        {
//            if (new_rpm_value_left)//?Make sure that at higher speeds capture event interval is lower than the transmission time of this message
//            {
//                printf("SOCrpmEOCL,%dEOP",rpm_capture_left);
//                new_rpm_value_left=false;
//            }
//        }
  }
}
