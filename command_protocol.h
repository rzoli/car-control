#define PARSE_BUFFER_SIZE 32
#define MAX_FUNCTION_PARAMETERS 8
#define MAX_FUNCTION_NAME_LENGTH 16
#define BEGINNING_OF_PARAMETERS '('
#define END_OF_COMMAND ')'
#define PARAMETER_DELIMITER ','

struct command_t {
		char name[MAX_FUNCTION_NAME_LENGTH];
		int parameters[MAX_FUNCTION_PARAMETERS];
        unsigned char nparameters;
    
};

class Dummy
{
};

class CommandParser: public Dummy
{
    public:
        CommandParser();
        void put(char c);
        bool parse();
        void prncmd();
    private:
        void clear_command();
        char parse_buffer[PARSE_BUFFER_SIZE];
        unsigned char parse_buffer_index;
        bool start_parse;
        command_t command;
        unsigned char i,j;
};
