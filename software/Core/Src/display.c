#include "display.h"
#include "main.h"
#include "cmsis_os.h"

/**
  * @brief  Initialize the display
  * @retval void
  */
void displayInit (void)
{
    // clear the Enable output
    HAL_GPIO_WritePin(D_enable_GPIO_Port, D_enable_Pin, GPIO_PIN_SET);
}