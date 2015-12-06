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
//#include "../command_protocol.h"


//FILE mystdout = FDEV_SETUP_STREAM(uart_putchar, NULL, _FDEV_SETUP_WRITE);

bool rpm_capture_overflow = false;
bool new_rpm_value_left = false;
bool enable_measurement_messages = false;
uint16_t rpm_capture_left, rpm_capture_right;

extern USART_data_t USART_data;
extern TC0_t* motor;

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

void init_adc(void)
{
    
    ADCA.REFCTRL|=(1<<4)|1;//vref on porta selected, tempref enabled
    ADCA.PRESCALER=1;//125 kHz sampling rate using div8
    PORTA.DIRSET &= ~0xC0;//porta 6 and 7 bits
    
    
  
    
    
    //temperature:
    ADCA.CH0.CTRL=0;//internal channels selected
    ADCA.CH0.MUXCTRL=0;//temp channel selected
    
    //adc ch0,1:
    ADCA.CH1.CTRL|=1;
    ADCA.CH1.MUXCTRL=6<<3;
    ADCA.CH2.CTRL|=1;
    ADCA.CH2.MUXCTRL=7<<3;
    
    ADCA.CTRLA|=1;//enable adc
    _delay_ms(10);//wait till adc clock settles
}



void init_mcu(void)
{
//    stdout = &mystdout;
    // Clock
    CLKSYS_Enable( OSC_RC2MEN_bm );
    CLKSYS_Prescalers_Config( CLK_PSADIV_1_gc, CLK_PSBCDIV_1_1_gc );
    do {} while ( CLKSYS_IsReady( OSC_RC2MRDY_bm ) == 0 );
    CLKSYS_Main_ClockSource_Select( CLK_SCLKSEL_RC2M_gc );//2 MHz selected
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
	
	/* set baud 115200 */
	USART_Baudrate_Set(&USARTC0, 149 , -7);
    USARTC0.CTRLB |= USART_CLK2X_bm;

	/* Enable both RX and TX. */
	USART_Rx_Enable(USART_data.usart);
	USART_Tx_Enable(USART_data.usart);
    
    //PWM
    motor = &TCE0;
    PORTE.DIRSET = PIN0_bm|PIN1_bm|PIN2_bm|PIN3_bm;
    motor->CTRLA = TC_CLKSEL_DIV1_gc;
    motor->CTRLB = TC_WGMODE_SS_gc | 0xf0; //A,B,C and D channels are enabled
    motor->PER = PWM_PERIOD_REGISTER_VALUE;
    motor->CCA = 0;
    motor->CCB = 0;//(int)(0.13*PWM_PERIOD_REGISTER_VALUE);
    motor->CCC = 0;
    motor->CCD = 0;
    
    init_adc();
    //Input capture/rpm measurement
    //other channel might be TCE1
    
//    TCC1.PER = RPM_MEASUREMENT_COUNTER_RELOAD_VALUE;
//	TCC1.CTRLA |= TC_CLKSEL_DIV1_gc; 
//    TCC1.CTRLB |= 0x10; /* select capture channel A */
//    TCC1.CTRLD |= TC_EVACT_CAPT_gc | TC_EVSEL_CH0_gc; /* select capture event and event channel 0 */
//	EVSYS.CH0MUX = EVSYS_CHMUX_PORTE_PIN0_gc; /* portE pin 0 */
	//PORTE.DIRCLR = 0x1; /* PE0 is input */
	//PORTE.PIN0CTRL = PORT_ISC_RISING_gc; /* sense rising edges */
//	TCC1.INTCTRLA = 1;
//	TCC1.INTCTRLB = 1;//later: medium priorityTEST
    
    /* Enable PMIC interrupt level low. */
	PMIC.CTRL |= PMIC_LOLVLEX_bm;

	/* Enable global interrupts. */
	sei();

}

char parse_buffer[PARSE_BUFFER_SIZE];
uint8_t parse_buffer_index = 0;

int main(void)
{    
   
//    char c;
//    CommandParser cp; //command parser
//    Comm comm; //standard io using uart
    DeviceCommands dc;
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
    dc << "start\r\n";
    while(1){ // loop forever
        dc.next_command();
//        c = comm.getchr();
//        if (c>0)
//            cp.put(c);
//            if (cp.parse()) {
//                comm << cp.command.name<<"\t"<<cp.command.nparameters<<"\n";
//            }
//        _delay_ms(500);
        
//        SET_GREEN_LED;
//        _delay_ms(50);
//        CLEAR_GREEN_LED;
    
//        parser();
//        if (host_ready && !first_run)
//        {
//            printf("start1\r\n");
//            printf(" %i\r\n", (int)(PWM_PERIOD_REGISTER_VALUE));
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
