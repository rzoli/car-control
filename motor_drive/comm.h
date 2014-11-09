
class Comm
{
    public:
        Comm(USART_data_t* usart_data);
        int uart_putchar(char c) ;
        char getchr(void);
        Comm& operator << (char*);
        Comm& operator << (unsigned int);
    private:
        USART_data_t* usart_data;
    
};
