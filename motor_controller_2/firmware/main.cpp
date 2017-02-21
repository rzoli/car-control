/*Roadmap:

*/
#include "board2host.h"

int main(void)
{
    

    Board2HostInterface bhi;
    bhi=Board2HostInterface();

      
    while(1){ // loop forever
        bhi.run();
  }
}
