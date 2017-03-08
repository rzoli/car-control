#include <string.h>
#include <stdlib.h>
#include <avr/interrupt.h>
#include <avr/io.h>
#include <avr/wdt.h>
#include "config.h"
#include "clksys_driver.h"
#include "usart_driver.h"
#include "adc_driver.h"
#include "board2host.h"

#define PW2REG(pulsewidth) (int)(pulsewidth*PWM_PERIOD_REGISTER_VALUE/1000)

USART_data_t USART_data;

ISR(USARTC0_RXC_vect)
{
    USART_RXComplete(&USART_data);
}

ISR(USARTC0_DRE_vect)
{
    USART_DataRegEmpty(&USART_data);
}

Board2HostInterface::Board2HostInterface(void)
{
    init_clock();
    init_uart();
    init_microsecond_timer();
    init_adc();
    init_pwm();
    sei();
    PORTB.DIRSET = 1<<GREEN_LED | 1 << RED_LED; 
    SET_GREEN_LED;
    SET_RED_LED;
    _delay_ms(1000);
    CLEAR_RED_LED;
    _delay_ms(1000);
    CLEAR_GREEN_LED;
    *this<<"Started";

}
void Board2HostInterface::run(void)
{   
    static int res;
    static char c[2];
    c[0]=getbyte();
    if (c[0]>0)
    {
        c[1]=0;
        //putbyte(c[0]);
        put(c);
        res=parse();
        if (res==NO_ERROR)
        {
            dispatch_commands();
        }
    }
    //*this<<"12345";
    _delay_ms(10);
}
void Board2HostInterface::init_clock(void)
{
    CLKSYS_Enable( OSC_RC2MEN_bm );
    CLKSYS_Prescalers_Config( CLK_PSADIV_1_gc, CLK_PSBCDIV_1_1_gc );
    do {} while ( CLKSYS_IsReady( OSC_RC2MRDY_bm ) == 0 );
    CLKSYS_Main_ClockSource_Select( CLK_SCLKSEL_RC2M_gc );//2 MHz selected
}
void Board2HostInterface::reset(void)
{
    //Enable watchdog and wait...
    CCP=0xD8;
    WDT.CTRL=3;//period is 8 ms
    _delay_ms(10);
}
void Board2HostInterface::init_uart(void)
{
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
	USART_Rx_Enable(USART_data.usart);
	USART_Tx_Enable(USART_data.usart);
    PMIC.CTRL |= PMIC_LOLVLEX_bm;
}
void Board2HostInterface::init_microsecond_timer(void)
{

    EVSYS.CH7MUX=EVSYS_CHMUX_TCC1_OVF_gc;//TCC1 overflow event is assigned to event channel 7
    //configure and start overflow driven counter first
    TCD1.CTRLA=TC_CLKSEL_EVCH7_gc;//select event channel 7
    TCC1.CTRLA=TC_CLKSEL_DIV2_gc;//2MHz peripheral clock 1/2 division
}
uint32_t Board2HostInterface::micros(void)
{
    static uint32_t t;
    t=(uint32_t)(TCD1.CNT)<<16;
    t+=(uint32_t)(TCC1.CNT);
    return t;
}
void Board2HostInterface::init_adc(void)
{
    PORTA.DIRSET &= ~(1<<7);//porta pin 7
    ADC_CalibrationValues_Load(&ADCA);
    ADCA.REFCTRL=1<<1;//Bandgap is enabled for 1V vref
    ADCA.PRESCALER=1;//Clock prescaler is at div8 -> 250 kHz kHz adc clock ~28 us acquisition time
    ADCA.CH0.CTRL|=1;//single ended selected
    ADCA.CH0.MUXCTRL=7<<3;//adc7 pin
    ADCA.CTRLA|=1;//enable adc
    _delay_ms(10);//wait till adc clock settles

}
void Board2HostInterface::init_pwm(void)
{
    PORTE.DIRSET = PIN0_bm|PIN1_bm|PIN2_bm|PIN3_bm;
    TCE0.CTRLA = TC_CLKSEL_DIV1_gc;
    TCE0.CTRLB = TC_WGMODE_SS_gc | 0xf0; //A,B,C and D channels are enabled
    TCE0.PER = PWM_PERIOD_REGISTER_VALUE;
    stop();
}
void Board2HostInterface::set_pwm(uint16_t a, uint16_t b, uint16_t c, uint16_t d)
{
    TCE0.CCA = PW2REG(a);
    TCE0.CCB = PW2REG(b);
    TCE0.CCC = PW2REG(c);
    TCE0.CCD = PW2REG(d);
}
void Board2HostInterface::stop(void)
{
    TCE0.CCA = 0;
    TCE0.CCB = 0;
    TCE0.CCC = 0;
    TCE0.CCD = 0;
}
void Board2HostInterface::putbyte(char c)
{
    USART_TXBuffer_PutByte(&USART_data, c);
}
char Board2HostInterface::getbyte(void)
{
    char res = 0U;
    if (USART_RXBufferData_Available(&USART_data)) {
     res = USART_RXBuffer_GetByte(&USART_data);
	}
    return res;
}

Board2HostInterface& Board2HostInterface::operator <<(char* pBuffer)
{
    for(uint8_t i=0;i<strlen(pBuffer);i++)
    {
        putbyte(pBuffer[i]);
    }
	return *this;
}

Board2HostInterface& Board2HostInterface::operator <<(uint32_t uiVal)
{
	char aIntBuff[10];
	ultoa(uiVal, aIntBuff,10);
	*this << aIntBuff;
	return *this;
}
uint16_t Board2HostInterface::read_battery_voltage(void)
{
    static uint16_t adc_res, adc_res_buffered;
    ADCA.CH0.CTRL|=1<<7;//Start conversion
    while ((ADCA.CH0.INTFLAGS&0x1)==0) {}//wait until conversion finishes
    ADCA.CH0.INTFLAGS=1;//clearing interrupt flag
    adc_res = ADCA.CH0.RES;
    adc_res_buffered=adc_res;
    return adc_res_buffered;
}
void Board2HostInterface::dispatch_commands(void)
{
        static uint32_t t1,t2;
        static int i;
        if (strcmp(command, "ping") == 0)
        {
                *this<<"pong\r\n";
        }
        else if ((strcmp(command, "green") == 0)&&(nparams==1))
        {
                if (par[0]==0)
                {
                        CLEAR_GREEN_LED;
                }
                else
                {
                        SET_GREEN_LED;
                }
                *this<<"green led set to "<<par[0]<<"\r\n";
        }
        else if ((strcmp(command, "red") == 0)&&(nparams==1))
        {
                if (par[0]==0)
                {
                        CLEAR_RED_LED;
                }
                else
                {
                        SET_RED_LED;
                }
                *this<<"red led set to "<<par[0]<<"\r\n";
        }
        else if ((strcmp(command, "test_micros") == 0)&&(nparams==1))
        {
                t1=micros();
                for (i=0;i<par[0];i++)
                {
                    _delay_ms(1);
                }
                t2=micros();
                *this<<t1<<" "<<t2<<" "<<t2-t1<<"\r\n";
        }
        else if ((strcmp(command, "micros") == 0)&&(nparams==0))
        {
                *this<<micros()<<"\r\n";
        }
        else if ((strcmp(command, "set_pwm") == 0)&&(nparams==4))
        {
                set_pwm(par[0], par[1], par[2], par[3]);
                *this<<"pwm set to "<<par[0]<<","<<par[1]<<","<<par[2]<<","<<par[3]<<"\r\n";
        }
        else if ((strcmp(command, "stop") == 0)&&(nparams==0))
        {
            stop();
            *this<<"pwm stopped\r\n";
        }

        else if ((strcmp(command, "reset") == 0)&&(nparams==0))
        {
            reset();
            *this<<"reset\r\n";
        }
        else if ((strcmp(command, "read_vbatt") == 0)&&(nparams==0))
        {
            *this<<read_battery_voltage()<<"\r\n";
        }
        else if ((strcmp(command, "meas_sample_time") == 0)&&(nparams==1))
        {
            t1=micros();
            for(i=0;i<par[0];i++)
            {
                read_battery_voltage();
            }
            t2=micros();
            *this<<t2-t1<<"\r\n";
        }

        else
        {
          *this<<"unknown command\r\n";
        }
}

