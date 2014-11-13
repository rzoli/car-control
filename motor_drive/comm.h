
class Comm
{
    public:
        int uart_putchar(char c);
        char getchr(void);
        Comm& operator << (char*);
        Comm& operator << (unsigned int);
    private:
        
    
};
