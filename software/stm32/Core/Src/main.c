/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2023 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "cmsis_os.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "stm32g0xx_ll_utils.h"
#include "display.h"
#include "colors.h"
#include <stdio.h>
#include <errno.h>
#include <stdlib.h>
#include <sys/unistd.h>
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */
uint8_t RxData[20] = {0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0};

uint8_t TxData[20] = {'X','X','X',':',' ','0','0','0',' ','H','P','T',':',' ','0','0','0'};
uint8_t TxDataUID[13] = {0};
char rpiIP[15] = {'U','N','K','N','O','W','N',0,0,0,0,0,0,0,0};
uint8_t GSTpressure=0;
uint8_t HPTpressure=0;

// Login credentials
#define LOGIN_PASSWORD "cybics"

// Menu options
#define MENU_STATUS '1'
#define MENU_FLAG '2'
#define MENU_CONTROLS '3'
#define MENU_FREERTOS '4'
#define MENU_MCU '5'
#define MENU_HELP '6'
#define MENU_LOGOUT '7'

uint8_t C_on = 0;
uint8_t C_off = 0;
uint8_t S_green = 0;
uint8_t S_red = 0;
uint8_t S_sen = 0;
uint8_t SV_green = 0;
uint8_t SV_red = 0;
uint8_t BO_red = 0;
uint8_t BO_green = 0;
uint8_t BO_sen = 0;
uint8_t GST_full = 0;
uint8_t GST_normal = 0;
uint8_t GST_low = 0;
uint8_t HPT_critical = 0;
uint8_t HPT_high = 0;
uint8_t HPT_normal = 0;
uint8_t HPT_low = 0;
uint8_t HPT_empty = 0;

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
#define LOG_ERR 0x03
#define LOG_WAR 0x02
#define LOG_INF 0x01
#define LOG_DEB 0x00

#define showLogLevel LOG_DEB
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
I2C_HandleTypeDef hi2c1;

UART_HandleTypeDef huart1;

osThreadId defaultTaskHandle;
osThreadId heartBeatHandle;
osThreadId displayHandle;
osThreadId physicalHandle;
osThreadId i2chandlerHandle;
osThreadId writeOutputHandle;
osThreadId uartHandle;
/* USER CODE BEGIN PV */
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_I2C1_Init(void);
static void MX_USART1_UART_Init(void);
void FdefaultTask(void const * argument);
void FheartBeat(void const * argument);
void Fdisplay(void const * argument);
void Fphysical(void const * argument);
void Fi2chandler(void const * argument);
void FwriteOutput(void const * argument);
void Fuart(void const * argument);

/* USER CODE BEGIN PFP */
#ifdef __GNUC__
#define PUTCHAR_PROTOTYPE int __io_putchar(int ch)
#else
#define PUTCHAR_PROTOTYPE int fputc(int ch, FILE *f)
#endif

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
SemaphoreHandle_t huart1Mutex;

int _write(int file, char * data, int len) {
    if ((file != STDOUT_FILENO) && (file != STDERR_FILENO)) {
        errno = EBADF;
        return -1;
    }

    HAL_StatusTypeDef status = HAL_OK;
    if (xSemaphoreTake(huart1Mutex, 100) == pdTRUE) {
        status = HAL_UART_Transmit(&huart1, (uint8_t *)data, len, 100);
        xSemaphoreGive(huart1Mutex);
    }

    // return # of bytes written - as best we can tell
    return (status == HAL_OK ? len : 0);
}

void logging(unsigned char logLevel, const char *fmt, ...){
    if(showLogLevel <= logLevel){
        if(logLevel == LOG_ERR)
        {  
            printf("%sERR: %s%s\r\n", CRED, fmt, CRST);
        }
        else if(logLevel == LOG_WAR)
        {
            printf("%sWAR: %s%s\r\n", CYEL, fmt, CRST);
        }
        else if(logLevel == LOG_INF)
        {
            printf("%sINF: %s%s\r\n", CBLU, fmt, CRST);
        }
        else if(logLevel == LOG_DEB)
        {
            printf("%sDEB: %s%s\r\n", CMAG, fmt, CRST);
        }
        else
        {
            printf("%s???: %s%s\r\n", CRED, fmt, CRST);
        }
    }
}
/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_I2C1_Init();
  MX_USART1_UART_Init();
  /* USER CODE BEGIN 2 */
  if(HAL_I2C_EnableListen_IT(&hi2c1) != HAL_OK)
  {
    /* Transfer error in reception process */
    Error_Handler();
  }

  huart1Mutex = xSemaphoreCreateMutex();
  /* USER CODE END 2 */

  /* USER CODE BEGIN RTOS_MUTEX */
  /* add mutexes, ... */
  /* USER CODE END RTOS_MUTEX */

  /* USER CODE BEGIN RTOS_SEMAPHORES */
  /* add semaphores, ... */
  /* USER CODE END RTOS_SEMAPHORES */

  /* USER CODE BEGIN RTOS_TIMERS */
  /* start timers, add new ones, ... */
  /* USER CODE END RTOS_TIMERS */

  /* USER CODE BEGIN RTOS_QUEUES */
  /* add queues, ... */
  /* USER CODE END RTOS_QUEUES */

  /* Create the thread(s) */
  /* definition and creation of defaultTask */
  osThreadDef(defaultTask, FdefaultTask, osPriorityNormal, 0, 128);
  defaultTaskHandle = osThreadCreate(osThread(defaultTask), NULL);

  /* definition and creation of heartBeat */
  osThreadDef(heartBeat, FheartBeat, osPriorityIdle, 0, 128);
  heartBeatHandle = osThreadCreate(osThread(heartBeat), NULL);

  /* definition and creation of display */
  osThreadDef(display, Fdisplay, osPriorityNormal, 0, 256);
  displayHandle = osThreadCreate(osThread(display), NULL);

  /* definition and creation of physical */
  osThreadDef(physical, Fphysical, osPriorityAboveNormal, 0, 256);
  physicalHandle = osThreadCreate(osThread(physical), NULL);

  /* definition and creation of i2chandler */
  osThreadDef(i2chandler, Fi2chandler, osPriorityNormal, 0, 128);
  i2chandlerHandle = osThreadCreate(osThread(i2chandler), NULL);

  /* definition and creation of writeOutput */
  osThreadDef(writeOutput, FwriteOutput, osPriorityRealtime, 0, 128);
  writeOutputHandle = osThreadCreate(osThread(writeOutput), NULL);

  /* definition and creation of uart */
  osThreadDef(uart, Fuart, osPriorityLow, 0, 256);
  uartHandle = osThreadCreate(osThread(uart), NULL);

  /* USER CODE BEGIN RTOS_THREADS */
  /* add threads, ... */
  /* USER CODE END RTOS_THREADS */

  /* Start scheduler */
  osKernelStart();

  /* We should never get here as control is now taken by the scheduler */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Configure the main internal regulator output voltage
  */
  HAL_PWREx_ControlVoltageScaling(PWR_REGULATOR_VOLTAGE_SCALE1);

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSIDiv = RCC_HSI_DIV1;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSI;
  RCC_OscInitStruct.PLL.PLLM = RCC_PLLM_DIV1;
  RCC_OscInitStruct.PLL.PLLN = 8;
  RCC_OscInitStruct.PLL.PLLP = RCC_PLLP_DIV2;
  RCC_OscInitStruct.PLL.PLLR = RCC_PLLR_DIV2;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief I2C1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_I2C1_Init(void)
{

  /* USER CODE BEGIN I2C1_Init 0 */

  /* USER CODE END I2C1_Init 0 */

  /* USER CODE BEGIN I2C1_Init 1 */

  /* USER CODE END I2C1_Init 1 */
  hi2c1.Instance = I2C1;
  hi2c1.Init.Timing = 0x10707DBC;
  hi2c1.Init.OwnAddress1 = 64;
  hi2c1.Init.AddressingMode = I2C_ADDRESSINGMODE_7BIT;
  hi2c1.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
  hi2c1.Init.OwnAddress2 = 0;
  hi2c1.Init.OwnAddress2Masks = I2C_OA2_NOMASK;
  hi2c1.Init.GeneralCallMode = I2C_GENERALCALL_ENABLE;
  hi2c1.Init.NoStretchMode = I2C_NOSTRETCH_DISABLE;
  if (HAL_I2C_Init(&hi2c1) != HAL_OK)
  {
    Error_Handler();
  }

  /** Configure Analogue filter
  */
  if (HAL_I2CEx_ConfigAnalogFilter(&hi2c1, I2C_ANALOGFILTER_ENABLE) != HAL_OK)
  {
    Error_Handler();
  }

  /** Configure Digital filter
  */
  if (HAL_I2CEx_ConfigDigitalFilter(&hi2c1, 0) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN I2C1_Init 2 */

  /* USER CODE END I2C1_Init 2 */

}

/**
  * @brief USART1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART1_UART_Init(void)
{

  /* USER CODE BEGIN USART1_Init 0 */

  /* USER CODE END USART1_Init 0 */

  /* USER CODE BEGIN USART1_Init 1 */

  /* USER CODE END USART1_Init 1 */
  huart1.Instance = USART1;
  huart1.Init.BaudRate = 115200;
  huart1.Init.WordLength = UART_WORDLENGTH_8B;
  huart1.Init.StopBits = UART_STOPBITS_1;
  huart1.Init.Parity = UART_PARITY_NONE;
  huart1.Init.Mode = UART_MODE_TX_RX;
  huart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart1.Init.OverSampling = UART_OVERSAMPLING_16;
  huart1.Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;
  huart1.Init.ClockPrescaler = UART_PRESCALER_DIV1;
  huart1.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_NO_INIT;
  if (HAL_UART_Init(&huart1) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_UARTEx_SetTxFifoThreshold(&huart1, UART_TXFIFO_THRESHOLD_1_8) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_UARTEx_SetRxFifoThreshold(&huart1, UART_RXFIFO_THRESHOLD_1_8) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_UARTEx_DisableFifoMode(&huart1) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USART1_Init 2 */

  /* USER CODE END USART1_Init 2 */

}

/**
  * @brief GPIO Initialization Function
  * @param None
  * @retval None
  */
static void MX_GPIO_Init(void)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};
  /* USER CODE BEGIN MX_GPIO_Init_1 */
  /* USER CODE END MX_GPIO_Init_1 */

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOC_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();
  __HAL_RCC_GPIOD_CLK_ENABLE();

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOC, ST_heartbeat_Pin|S_red_Pin|S_green_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOA, S_sen_Pin|BO_sen_Pin|SV_red_Pin|SV_green_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOB, D_enable_Pin|D_rs_Pin|D_d4_Pin|D_d5_Pin
                          |D_d6_Pin|D_d7_Pin|C_off_Pin|C_on_Pin
                          |GST_low_Pin|GST_normal_Pin|GST_full_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOD, BO_green_Pin|BO_red_Pin|HPT_empty_Pin|HPT_low_Pin
                          |HPT_normal_Pin|HPT_high_Pin|HPT_critical_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pins : ST_heartbeat_Pin S_red_Pin S_green_Pin */
  GPIO_InitStruct.Pin = ST_heartbeat_Pin|S_red_Pin|S_green_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOC, &GPIO_InitStruct);

  /*Configure GPIO pins : C_sig_Pin SV_sig_Pin PA4 GST_sig_Pin
                           PA6 Display_in_Pin */
  GPIO_InitStruct.Pin = C_sig_Pin|SV_sig_Pin|GPIO_PIN_4|GST_sig_Pin
                          |GPIO_PIN_6|Display_in_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

  /*Configure GPIO pins : S_sen_Pin BO_sen_Pin SV_red_Pin SV_green_Pin */
  GPIO_InitStruct.Pin = S_sen_Pin|BO_sen_Pin|SV_red_Pin|SV_green_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

  /*Configure GPIO pins : D_enable_Pin D_rs_Pin D_d4_Pin D_d5_Pin
                           D_d6_Pin D_d7_Pin C_off_Pin C_on_Pin
                           GST_low_Pin GST_normal_Pin GST_full_Pin */
  GPIO_InitStruct.Pin = D_enable_Pin|D_rs_Pin|D_d4_Pin|D_d5_Pin
                          |D_d6_Pin|D_d7_Pin|C_off_Pin|C_on_Pin
                          |GST_low_Pin|GST_normal_Pin|GST_full_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

  /*Configure GPIO pins : BO_green_Pin BO_red_Pin HPT_empty_Pin HPT_low_Pin
                           HPT_normal_Pin HPT_high_Pin HPT_critical_Pin */
  GPIO_InitStruct.Pin = BO_green_Pin|BO_red_Pin|HPT_empty_Pin|HPT_low_Pin
                          |HPT_normal_Pin|HPT_high_Pin|HPT_critical_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOD, &GPIO_InitStruct);

  /*Configure GPIO pin : button_Pin */
  GPIO_InitStruct.Pin = button_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(button_GPIO_Port, &GPIO_InitStruct);

  /* USER CODE BEGIN MX_GPIO_Init_2 */
  /* USER CODE END MX_GPIO_Init_2 */
}

/* USER CODE BEGIN 4 */
void HAL_I2C_ListenCpltCallback (I2C_HandleTypeDef *hi2c)
{
	HAL_I2C_EnableListen_IT(hi2c);
}

void HAL_I2C_AddrCallback(I2C_HandleTypeDef *hi2c, uint8_t TransferDirection, uint16_t AddrMatchCode)
{
	if(TransferDirection == I2C_DIRECTION_TRANSMIT)  // if the master wants to transmit the data
	{
		HAL_I2C_Slave_Sequential_Receive_IT(hi2c, RxData, sizeof(RxData), I2C_FIRST_AND_LAST_FRAME);
	}
	else  // master requesting the data is not supported yet
	{
    if(RxData[0]==0){
		  HAL_I2C_Slave_Sequential_Transmit_IT(hi2c, TxData, sizeof(TxData), I2C_LAST_FRAME);
    }
    else if(RxData[0]==1){
      HAL_I2C_Slave_Sequential_Transmit_IT(hi2c, TxDataUID, sizeof(TxDataUID), I2C_LAST_FRAME);
    }
	}
}

void HAL_I2C_SlaveRxCpltCallback(I2C_HandleTypeDef *hi2c)
{

}

void HAL_I2C_ErrorCallback(I2C_HandleTypeDef *hi2c)
{
	HAL_I2C_EnableListen_IT(hi2c);
}
/* USER CODE END 4 */

/* USER CODE BEGIN Header_FdefaultTask */
/**
  * @brief  Function implementing the defaultTask thread.
  * @param  argument: Not used
  * @retval None
  */
/* USER CODE END Header_FdefaultTask */
void FdefaultTask(void const * argument)
{
  /* USER CODE BEGIN 5 */
  /* Infinite loop */
  for(;;)
  {


    osDelay(1);
  }
  /* USER CODE END 5 */
}

/* USER CODE BEGIN Header_FheartBeat */
/**
* @brief Function implementing the heartBeat thread.
* @param argument: Not used
* @retval None
*/
/* USER CODE END Header_FheartBeat */
void FheartBeat(void const * argument)
{
  /* USER CODE BEGIN FheartBeat */
  logging(LOG_DEB, "Starting FheartBeat");
  /* Infinite loop */
  for(;;)
  {
    HAL_GPIO_TogglePin(ST_heartbeat_GPIO_Port, ST_heartbeat_Pin);
    
    osDelay(1000);
  }
  /* USER CODE END FheartBeat */
}

/* USER CODE BEGIN Header_Fdisplay */
/**
* @brief Function implementing the display thread.
* @param argument: Not used
* @retval None
*/
/* USER CODE END Header_Fdisplay */
void Fdisplay(void const * argument)
{
  /* USER CODE BEGIN Fdisplay */
  uint8_t shifting=0;
  uint8_t displayScreen=0;
  uint32_t secondsAfterStart = 0;
  uint8_t wifiPressed = 0;
  char displayText[20];

  osDelay(10);

  Lcd_PortType ports[] = {
		  D_d4_GPIO_Port, D_d5_GPIO_Port, D_d6_GPIO_Port, D_d7_GPIO_Port
  };

  Lcd_PinType pins[] = {D_d4_Pin, D_d5_Pin, D_d6_Pin, D_d7_Pin};
  Lcd_HandleTypeDef lcd = Lcd_create(ports, pins, D_rs_GPIO_Port, D_rs_Pin, D_enable_GPIO_Port, D_enable_Pin, LCD_4_BIT_MODE);

  logging(LOG_DEB, "Starting Fdisplay");

  
  snprintf((char*)TxDataUID, sizeof(TxDataUID), "%04lx%04lx%04lx", LL_GetUID_Word0(), LL_GetUID_Word1(), LL_GetUID_Word2());
  TxDataUID[12]='0'; // default STA
  
  /* Infinite loop */
  for(;;)
  {
    // Switch between station and AP mode of Wifi
    if(HAL_GPIO_ReadPin(button_GPIO_Port, button_Pin)){
      if(!wifiPressed){
        if(TxDataUID[12]=='0'){
          TxDataUID[12]='1';
        }
        else{
          TxDataUID[12]='0';
        }
        snprintf(rpiIP, sizeof(rpiIP), "%-14s", "Unknown");
        shifting=0;        
        wifiPressed=1;
      }
    }
    else{
      wifiPressed=0;
    }
     
    // Switch between displays if Display button is pressed
    if(HAL_GPIO_ReadPin(Display_in_GPIO_Port, Display_in_Pin)){
      displayScreen++;
      if(displayScreen>3){
        displayScreen=0;
      }
    }

    secondsAfterStart++;
    // Display showing Cybics string and IP
    if(0==displayScreen){
      snprintf(displayText, sizeof(displayText), "%-16s", "CybICS v1.0.2");
      Lcd_cursor(&lcd, 0, 0);
      Lcd_string(&lcd, displayText);
      snprintf(displayText, sizeof(displayText), "%16li", secondsAfterStart);
      Lcd_cursor(&lcd, 1, 0);
      Lcd_string(&lcd, displayText);
    }
    // Display WiFi configuration
    else if(1==displayScreen){
      if(TxDataUID[12]=='0'){
        snprintf(displayText, sizeof(displayText), "%-16s", "Wifi STA mode");
        Lcd_cursor(&lcd, 0, 0);
        Lcd_string(&lcd, displayText);
        snprintf(displayText, sizeof(displayText), "IP: %-12s", &rpiIP[shifting]);
        Lcd_cursor(&lcd, 1, 0);
        Lcd_string(&lcd, displayText);

        if(strlen(rpiIP)>12)
        {
          shifting++;
        }    
        if(shifting>3)
        {
          shifting=0;
        }
      }
      else if(TxDataUID[12]=='1'){
        snprintf(displayText, sizeof(displayText), "%-16s", "AP mode: cybics-");
        Lcd_cursor(&lcd, 0, 0);
        Lcd_string(&lcd, displayText);
        snprintf(displayText, sizeof(displayText), "%-16s", TxDataUID);
        displayText[12]=' '; // removing the 1, which is not part of the UID
        Lcd_cursor(&lcd, 1, 0);
        Lcd_string(&lcd, displayText);
      }
      else{
        snprintf(displayText, sizeof(displayText), "%-16s", "WiFi error");
        Lcd_cursor(&lcd, 0, 0);
        Lcd_string(&lcd, displayText);
      }
    }
    // Display showing real pressure values
    else if(2==displayScreen){
      snprintf(displayText, sizeof(displayText), "%-16s", "Physical/real:  ");
      Lcd_cursor(&lcd, 0, 0);
      Lcd_string(&lcd, displayText);
      snprintf(displayText, sizeof(displayText), "GST:%03d HPT:%03d ", GSTpressure, HPTpressure);
      Lcd_cursor(&lcd, 1, 0);
      Lcd_string(&lcd, displayText);
    }
    // Display showing status
    else if(3==displayScreen){
      snprintf(displayText, sizeof(displayText), "%-16s", "Status:");
      Lcd_cursor(&lcd, 0, 0);
      Lcd_string(&lcd, displayText);
      if(BO_sen>0){
        snprintf(displayText, sizeof(displayText), "%-16s", "Danger! BlowOut");
      }
      else if((HPTpressure>50) && (HPTpressure<100) && SV_green){
        snprintf(displayText, sizeof(displayText), "%-16s", "Operational");
      }
      else if((HPTpressure>50) && (HPTpressure<100)){
        snprintf(displayText, sizeof(displayText), "%-16s", "SV closed");
      }
      else if(HPTpressure>100){
        snprintf(displayText, sizeof(displayText), "%-16s", "Pressure too high");
      }
      else if(HPTpressure<=50){
        snprintf(displayText, sizeof(displayText), "%-16s", "Pressure too low");
      }
      Lcd_cursor(&lcd, 1, 0);
      Lcd_string(&lcd, displayText);
    }

    osDelay(1000);
  }
  /* USER CODE END Fdisplay */
}

/* USER CODE BEGIN Header_Fphysical */
/**
* @brief Function implementing the physical thread.
* @param argument: Not used
* @retval None
*/
/* USER CODE END Header_Fphysical */
void Fphysical(void const * argument)
{
  /* USER CODE BEGIN Fphysical */
  uint8_t HPTuse=0;
  osDelay(20);

  logging(LOG_DEB, "Starting Fphysical");

  GPIO_PinState cState; // state of the compressor
  GPIO_PinState svState; // state of the system valve
  GPIO_PinState gstState; // state of refilling GST

  uint16_t HPTdelay=0;
  uint16_t GSTdelay=0;
  uint16_t BOdelay=0;
  /* Infinite loop */
  for(;;)
  {
    //GPIO_PinState buttonState = HAL_GPIO_ReadPin(button_GPIO_Port, button_Pin);
    cState = HAL_GPIO_ReadPin(C_sig_GPIO_Port, C_sig_Pin);
    svState = HAL_GPIO_ReadPin(SV_sig_GPIO_Port, SV_sig_Pin);
    gstState = HAL_GPIO_ReadPin(GST_sig_GPIO_Port, GST_sig_Pin);

    /**
     * When compressor is running:
     * - Increase HPT pressure
     * - LED Compressor should be green
    */
    if(cState)
    {
      C_on = 1;
      C_off = 0;
      if(HPTdelay>100) // increase pressure 1 per second
      {
        if(HPTpressure<255)
        {          
          if(GSTpressure>=50){ // HPT pressure can only be increased, if GST >= 50
            GSTpressure = GSTpressure - 2;
            HPTpressure++;
          }
        }        
        HPTdelay=0;
      }
      
    }
    else
    {
      C_on = 0;
      C_off = 1;     
      if(HPTdelay>100) // decrease pressure in rand%5 per second
      {
        HPTuse = rand() % 3;
        // decrease presussure only if > 0 and system valve is open
        if(((HPTpressure-HPTuse)>=0) & svState)
        {
          HPTpressure = HPTpressure - HPTuse;
        }        
        HPTdelay=0;
      }
    }

    if(GSTdelay>100)
    {
      if((GSTpressure<251) & (gstState))
      {
        GSTpressure = GSTpressure + (rand() % 4);
      }
      GSTdelay=0;
    }

    if(svState)
    {
      SV_green = 1;
      SV_red = 0;
    }
    else
    {
      SV_green = 0;
      SV_red = 1;
    }

    if(HPTpressure<1)
    {
      HPT_critical = 0;
      HPT_high = 0;
      HPT_normal = 0;
      HPT_low = 0;
      HPT_empty = 1;
    }
    else if (HPTpressure<50)
    {
      HPT_critical = 0;
      HPT_high = 0;
      HPT_normal = 0;
      HPT_low = 1;
      HPT_empty = 0;
    }
    else if (HPTpressure<100)
    {
      HPT_critical = 0;
      HPT_high = 0;
      HPT_normal = 1;
      HPT_low = 0;
      HPT_empty = 0;
    }
    else if (HPTpressure<150)
    {
      HPT_critical = 0;
      HPT_high = 1;
      HPT_normal = 0;
      HPT_low = 0;
      HPT_empty = 0;
    }
    else
    {
      HPT_critical = 1;
      HPT_high = 0;
      HPT_normal = 0;
      HPT_low = 0;
      HPT_empty = 0;
    }

    /**
     * Blowout if the HPTpressure if over 220
     * Until HTP pressure < 201
    */  
    if((HPTpressure>220) || ((HPTpressure>200) & (BO_sen > 0)))
    {
      BO_red = 1;
      BO_green = 0;
      BO_sen = 1;
      if(BOdelay>100) // decrease pressure 1 per second
      {
        HPTuse = rand() % 2;
        if((HPTpressure-HPTuse)>=0)
        {
          HPTpressure = HPTpressure - HPTuse;
        }        
        BOdelay=0;
      }
    }
    else
    {
      BO_red = 0;
      BO_green = 1;
      BO_sen = 0; 
    }

    /**
     * System operating, when pressure is in normal range
     * And System valve is open
    */  
    if((HPTpressure>50) && (HPTpressure<100) && svState)
    {
      S_red = 0;
      S_green = 1;
      S_sen  = 1;
    }
    else
    {
      S_red = 1;
      S_green = 0;
      S_sen  = 0;
    }
    /**
     * Gas Storage Tank
    */  
    if(GSTpressure<50)
    {
      GST_low = 1;
      GST_normal = 0;
      GST_full = 0;
    }
    else if(GSTpressure<150)
    {
      GST_low = 0;
      GST_normal = 1;
      GST_full = 0;
    }
    else
    {
      GST_low = 0;
      GST_normal = 0;
      GST_full = 1;
    }
    
    /**
     * Set the right values in the TX Data:
     * - GSTTpressure
     * - HPTpressure
     * Format: GST: %03d HPT: %03d
    */    
    snprintf((char*)TxData, sizeof(TxData), "GST: %03d HPT: %03d", GSTpressure, HPTpressure);

    HPTdelay = HPTdelay+1;
    GSTdelay = GSTdelay+1;
    BOdelay = BOdelay+1;
    osDelay(10);
  }
  /* USER CODE END Fphysical */
}

/* USER CODE BEGIN Header_Fi2chandler */
/**
* @brief Function implementing the i2chandler thread.
* @param argument: Not used
* @retval None
*/
/* USER CODE END Header_Fi2chandler */
void Fi2chandler(void const * argument)
{
  /* USER CODE BEGIN Fi2chandler */
  osDelay(30);
  logging(LOG_DEB, "Starting Fi2chandler");
  /* Infinite loop */
  for(;;)
  {
    if(RxData[1]=='I' && RxData[2]=='P')
    {
      for(u_int8_t counter=0; counter<sizeof(rpiIP); counter++)
      {
        rpiIP[counter] = RxData[counter+4];
      }
    }

    osDelay(100);
  }
  /* USER CODE END Fi2chandler */
}

/* USER CODE BEGIN Header_FwriteOutput */
/**
* @brief Function implementing the writeOutput thread.
* @param argument: Not used
* @retval None
*/
/* USER CODE END Header_FwriteOutput */
void FwriteOutput(void const * argument)
{
  /* USER CODE BEGIN FwriteOutput */
  osDelay(1);

  /* Infinite loop */
  for(;;)
  {
    // clear Gas Storage Tank LEDs
    HAL_GPIO_WritePin(GST_full_GPIO_Port, GST_full_Pin, GPIO_PIN_SET);
    //HAL_GPIO_WritePin(GST_normal_GPIO_Port, GST_normal_Pin, GPIO_PIN_SET);
    HAL_GPIO_WritePin(GST_low_GPIO_Port, GST_low_Pin, GPIO_PIN_SET);

    // clear Compressor LEDs
    //HAL_GPIO_WritePin(C_on_GPIO_Port, C_on_Pin, GPIO_PIN_SET);
    HAL_GPIO_WritePin(C_off_GPIO_Port, C_off_Pin, GPIO_PIN_SET);

    // clear High Pressure Tank LEDs
    HAL_GPIO_WritePin(HPT_critical_GPIO_Port, HPT_critical_Pin, GPIO_PIN_SET);
    HAL_GPIO_WritePin(HPT_high_GPIO_Port, HPT_high_Pin, GPIO_PIN_SET);
    //HAL_GPIO_WritePin(HPT_normal_GPIO_Port, HPT_normal_Pin, GPIO_PIN_SET);
    HAL_GPIO_WritePin(HPT_low_GPIO_Port, HPT_low_Pin, GPIO_PIN_SET);
    HAL_GPIO_WritePin(HPT_empty_GPIO_Port, HPT_empty_Pin, GPIO_PIN_SET);

    // clear Blow Out LEDs
    HAL_GPIO_WritePin(BO_red_GPIO_Port, BO_red_Pin, GPIO_PIN_SET);
    //HAL_GPIO_WritePin(BO_green_GPIO_Port, BO_green_Pin, GPIO_PIN_SET); 

    // clear System Valve LEDs
    HAL_GPIO_WritePin(SV_red_GPIO_Port, SV_red_Pin, GPIO_PIN_SET);
    //HAL_GPIO_WritePin(SV_green_GPIO_Port, SV_green_Pin, GPIO_PIN_SET); 

    // clear System LEDs
    HAL_GPIO_WritePin(S_red_GPIO_Port, S_red_Pin, GPIO_PIN_SET);
    //HAL_GPIO_WritePin(S_green_GPIO_Port, S_green_Pin, GPIO_PIN_SET); 

    osDelay(14);
    if (C_on){
      HAL_GPIO_WritePin(C_on_GPIO_Port, C_on_Pin, GPIO_PIN_RESET);
    }
    else{
      HAL_GPIO_WritePin(C_on_GPIO_Port, C_on_Pin, GPIO_PIN_SET);
    }
    if (C_off){
      HAL_GPIO_WritePin(C_off_GPIO_Port, C_off_Pin, GPIO_PIN_RESET);
    }
    if (SV_red){
      HAL_GPIO_WritePin(SV_red_GPIO_Port, SV_red_Pin, GPIO_PIN_RESET);
    }
    if (SV_green){
      HAL_GPIO_WritePin(SV_green_GPIO_Port, SV_green_Pin, GPIO_PIN_RESET);
    }
    else{
      HAL_GPIO_WritePin(SV_green_GPIO_Port, SV_green_Pin, GPIO_PIN_SET);
    }
    if (GST_full){
      HAL_GPIO_WritePin(GST_full_GPIO_Port, GST_full_Pin, GPIO_PIN_RESET);
    }
    if (GST_normal){
      HAL_GPIO_WritePin(GST_normal_GPIO_Port, GST_normal_Pin, GPIO_PIN_RESET);
    }
    else{
      HAL_GPIO_WritePin(GST_normal_GPIO_Port, GST_normal_Pin, GPIO_PIN_SET);
    }
    if (GST_low){
      HAL_GPIO_WritePin(GST_low_GPIO_Port, GST_low_Pin, GPIO_PIN_RESET);
    }
    if (HPT_critical){
      HAL_GPIO_WritePin(HPT_critical_GPIO_Port, HPT_critical_Pin, GPIO_PIN_RESET);
    }
    if (HPT_high){
      HAL_GPIO_WritePin(HPT_high_GPIO_Port, HPT_high_Pin, GPIO_PIN_RESET);
     }
    if (HPT_normal){
      HAL_GPIO_WritePin(HPT_normal_GPIO_Port, HPT_normal_Pin, GPIO_PIN_RESET);
    }
    else{
      HAL_GPIO_WritePin(HPT_normal_GPIO_Port, HPT_normal_Pin, GPIO_PIN_SET);
    }
    if (HPT_low){
      HAL_GPIO_WritePin(HPT_low_GPIO_Port, HPT_low_Pin, GPIO_PIN_RESET);
    }
    if (HPT_empty){
      HAL_GPIO_WritePin(HPT_empty_GPIO_Port, HPT_empty_Pin, GPIO_PIN_RESET);
    }
    if (S_red){
      HAL_GPIO_WritePin(S_red_GPIO_Port, S_red_Pin, GPIO_PIN_RESET);
    }
    if (S_green){
      HAL_GPIO_WritePin(S_green_GPIO_Port, S_green_Pin, GPIO_PIN_RESET); 
    }
    else{
      HAL_GPIO_WritePin(S_green_GPIO_Port, S_green_Pin, GPIO_PIN_SET); 
    }
    if(S_sen){ // Sensor outputs should not be pulsed nor inverted
      HAL_GPIO_WritePin(S_sen_GPIO_Port, S_sen_Pin, GPIO_PIN_SET);
    }
    else{
      HAL_GPIO_WritePin(S_sen_GPIO_Port, S_sen_Pin, GPIO_PIN_RESET);
    }
    if (BO_red){
      HAL_GPIO_WritePin(BO_red_GPIO_Port, BO_red_Pin, GPIO_PIN_RESET);
    }
    if (BO_green){
      HAL_GPIO_WritePin(BO_green_GPIO_Port, BO_green_Pin, GPIO_PIN_RESET);
    }
    else{
      HAL_GPIO_WritePin(BO_green_GPIO_Port, BO_green_Pin, GPIO_PIN_SET);
    }
    if(BO_sen){ // Sensor outputs should not be pulsed nor inverted
      HAL_GPIO_WritePin(BO_sen_GPIO_Port, BO_sen_Pin, GPIO_PIN_SET);    
    }
    else{
      HAL_GPIO_WritePin(BO_sen_GPIO_Port, BO_sen_Pin, GPIO_PIN_RESET);  
    }

    osDelay(1);
  }
  /* USER CODE END FwriteOutput */
}

/* USER CODE BEGIN Header_Fuart */
/**
* @brief Function implementing the uart thread.
* @param argument: Not used
* @retval None
*/
/* USER CODE END Header_Fuart */
void Fuart(void const * argument)
{
  /* USER CODE BEGIN Fuart */
  char statusMsg[50];
  char password[20];
  char input[2];
  uint8_t loggedIn = 0;
  uint8_t rxIndex = 0;
  uint8_t showMenu = 1;  // Flag to control menu display
  uint8_t passwordEntry = 0;  // Flag to track password entry state
  
  osDelay(1000);  // Initial delay to let system stabilize
  logging(LOG_DEB, "Starting Fuart");
  
  /* Infinite loop */
  for(;;)
  {
    if (!loggedIn) {
      if (!passwordEntry) {
        logging(LOG_INF, "Please enter password:");
        rxIndex = 0;
        memset(password, 0, sizeof(password));
        passwordEntry = 1;
      }
      
      // Non-blocking password input
      if (rxIndex < sizeof(password) - 1) {
        if (HAL_UART_Receive(&huart1, (uint8_t*)&password[rxIndex], 1, 100) == HAL_OK) {
          // Echo the character
          HAL_UART_Transmit(&huart1, (uint8_t*)&password[rxIndex], 1, 100);
          
          // Check for enter key
          if (password[rxIndex] == '\r' || password[rxIndex] == '\n') {
            password[rxIndex] = '\0';
            // Check password
            if (strcmp(password, LOGIN_PASSWORD) == 0) {
              loggedIn = 1;
              logging(LOG_INF, "Login successful!");
              showMenu = 1;
            } else {
              logging(LOG_ERR, "Invalid password. Please try again.");
              passwordEntry = 0;  // Reset for next attempt
            }
          } else {
            rxIndex++;
          }
        }
      }
      osDelay(10);  // Small delay between password attempts
      continue;
    }

    // Show menu only when needed
    if (showMenu) {
      logging(LOG_INF, "\r\n=== CybICS Menu ===");
      logging(LOG_INF, "1. System Status");
      logging(LOG_INF, "2. Display Flag");
      logging(LOG_INF, "3. System Controls");
      logging(LOG_INF, "4. FreeRTOS Stats");
      logging(LOG_INF, "5. MCU Information");
      logging(LOG_INF, "6. Help");
      logging(LOG_INF, "7. Logout");
      logging(LOG_INF, "Enter choice (1-7): ");
      showMenu = 0;
    }

    // Non-blocking menu choice input
    if (HAL_UART_Receive(&huart1, (uint8_t*)input, 1, 100) == HAL_OK) {
      switch(input[0]) {
        case MENU_STATUS:
          // Display system status
          logging(LOG_INF, "\r\n=== System Status ===");
          snprintf(statusMsg, sizeof(statusMsg), "GST Pressure: %d", GSTpressure);
          logging(LOG_INF, statusMsg);
          snprintf(statusMsg, sizeof(statusMsg), "HPT Pressure: %d", HPTpressure);
          logging(LOG_INF, statusMsg);
          snprintf(statusMsg, sizeof(statusMsg), "Compressor: %s", C_on ? "ON" : "OFF");
          logging(LOG_INF, statusMsg);
          snprintf(statusMsg, sizeof(statusMsg), "System Valve: %s", SV_green ? "OPEN" : "CLOSED");
          logging(LOG_INF, statusMsg);
          snprintf(statusMsg, sizeof(statusMsg), "System Status: %s", S_green ? "OPERATIONAL" : "NOT OPERATIONAL");
          logging(LOG_INF, statusMsg);
          snprintf(statusMsg, sizeof(statusMsg), "Blow Out: %s", BO_sen ? "ACTIVE" : "INACTIVE");
          logging(LOG_INF, statusMsg);
          showMenu = 1;
          break;

        case MENU_FLAG:
          logging(LOG_INF, "\r\n=== CybICS Flag ===");
          logging(LOG_INF, "CybICS(U#RT)");
          showMenu = 1;
          break;

        case MENU_CONTROLS:
          // Display system controls
          logging(LOG_INF, "\r\n=== System Controls ===");
          logging(LOG_INF, "Current Status:");
          logging(LOG_INF, "----------------");
          logging(LOG_INF, "Compressor: %s", C_on ? "Running" : "Stopped");
          logging(LOG_INF, "System Valve: %s", SV_green ? "Open" : "Closed");
          logging(LOG_INF, "Blow Out: %s", BO_sen ? "Active" : "Inactive");
          logging(LOG_INF, "GST Pressure: %d", GSTpressure);
          logging(LOG_INF, "HPT Pressure: %d", HPTpressure);
          logging(LOG_INF, "System Status: %s", S_green ? "OPERATIONAL" : "NOT OPERATIONAL");
          
          logging(LOG_INF, "\r\nControl Options:");
          logging(LOG_INF, "----------------");
          logging(LOG_INF, "1. Toggle Compressor");
          logging(LOG_INF, "2. Toggle System Valve");
          logging(LOG_INF, "3. Return to Main Menu");
          logging(LOG_INF, "Enter choice (1-3): ");
          
          // Non-blocking control choice input
          if (HAL_UART_Receive(&huart1, (uint8_t*)input, 1, 100) == HAL_OK) {
            switch(input[0]) {
              case '1':
                if (C_on) {
                  C_on = 0;
                  C_off = 1;
                  logging(LOG_INF, "Compressor stopped");
                } else {
                  C_on = 1;
                  C_off = 0;
                  logging(LOG_INF, "Compressor started");
                }
                break;
                
              case '2':
                if (SV_green) {
                  SV_green = 0;
                  SV_red = 1;
                  logging(LOG_INF, "System valve closed");
                } else {
                  SV_green = 1;
                  SV_red = 0;
                  logging(LOG_INF, "System valve opened");
                }
                break;
                
              case '3':
                logging(LOG_INF, "Returning to main menu...");
                break;
                
              default:
                logging(LOG_ERR, "Invalid control choice");
                break;
            }
            showMenu = 1;
          }
          break;

        case MENU_FREERTOS:
          // Display FreeRTOS statistics
          logging(LOG_INF, "\r\n=== FreeRTOS Statistics ===");
          
          // Task stats
          logging(LOG_INF, "Task Statistics:");
          logging(LOG_INF, "----------------");
          
          // Get task stats for each task
          char taskStats[100];
          TaskStatus_t taskStatus;
          
          // Default Task
          vTaskGetTaskInfo(defaultTaskHandle, &taskStatus, pdTRUE, eRunning);
          snprintf(taskStats, sizeof(taskStats), "Default Task: State=%d, Priority=%lu, Stack=%u", 
                  taskStatus.eCurrentState, taskStatus.uxCurrentPriority, taskStatus.usStackHighWaterMark);
          logging(LOG_INF, taskStats);
          
          // Heartbeat Task
          vTaskGetTaskInfo(heartBeatHandle, &taskStatus, pdTRUE, eRunning);
          snprintf(taskStats, sizeof(taskStats), "Heartbeat Task: State=%d, Priority=%lu, Stack=%u", 
                  taskStatus.eCurrentState, taskStatus.uxCurrentPriority, taskStatus.usStackHighWaterMark);
          logging(LOG_INF, taskStats);
          
          // Display Task
          vTaskGetTaskInfo(displayHandle, &taskStatus, pdTRUE, eRunning);
          snprintf(taskStats, sizeof(taskStats), "Display Task: State=%d, Priority=%lu, Stack=%u", 
                  taskStatus.eCurrentState, taskStatus.uxCurrentPriority, taskStatus.usStackHighWaterMark);
          logging(LOG_INF, taskStats);
          
          // Physical Task
          vTaskGetTaskInfo(physicalHandle, &taskStatus, pdTRUE, eRunning);
          snprintf(taskStats, sizeof(taskStats), "Physical Task: State=%d, Priority=%lu, Stack=%u", 
                  taskStatus.eCurrentState, taskStatus.uxCurrentPriority, taskStatus.usStackHighWaterMark);
          logging(LOG_INF, taskStats);
          
          // I2C Handler Task
          vTaskGetTaskInfo(i2chandlerHandle, &taskStatus, pdTRUE, eRunning);
          snprintf(taskStats, sizeof(taskStats), "I2C Handler Task: State=%d, Priority=%lu, Stack=%u", 
                  taskStatus.eCurrentState, taskStatus.uxCurrentPriority, taskStatus.usStackHighWaterMark);
          logging(LOG_INF, taskStats);
          
          // Write Output Task
          vTaskGetTaskInfo(writeOutputHandle, &taskStatus, pdTRUE, eRunning);
          snprintf(taskStats, sizeof(taskStats), "Write Output Task: State=%d, Priority=%lu, Stack=%u", 
                  taskStatus.eCurrentState, taskStatus.uxCurrentPriority, taskStatus.usStackHighWaterMark);
          logging(LOG_INF, taskStats);
          
          // UART Task
          vTaskGetTaskInfo(uartHandle, &taskStatus, pdTRUE, eRunning);
          snprintf(taskStats, sizeof(taskStats), "UART Task: State=%d, Priority=%lu, Stack=%u", 
                  taskStatus.eCurrentState, taskStatus.uxCurrentPriority, taskStatus.usStackHighWaterMark);
          logging(LOG_INF, taskStats);
          
          // System stats
          logging(LOG_INF, "\r\nSystem Statistics:");
          logging(LOG_INF, "-----------------");
          snprintf(taskStats, sizeof(taskStats), "Free Heap: %d bytes", xPortGetFreeHeapSize());
          logging(LOG_INF, taskStats);
          snprintf(taskStats, sizeof(taskStats), "Minimum Free Heap: %d bytes", xPortGetMinimumEverFreeHeapSize());
          logging(LOG_INF, taskStats);
          snprintf(taskStats, sizeof(taskStats), "Total Runtime: %lu ticks", xTaskGetTickCount());
          logging(LOG_INF, taskStats);
          
          showMenu = 1;
          break;

        case MENU_MCU:
          // Display MCU information
          logging(LOG_INF, "\r\n=== MCU Information ===");
          logging(LOG_INF, "----------------");
          
          char mcuInfo[100];
          
          // Get MCU ID
          uint32_t mcuId = HAL_GetDEVID();
          snprintf(mcuInfo, sizeof(mcuInfo), "MCU ID: 0x%08lX", mcuId);
          logging(LOG_INF, mcuInfo);
          
          // Get MCU Revision
          uint32_t mcuRev = HAL_GetREVID();
          snprintf(mcuInfo, sizeof(mcuInfo), "MCU Revision: 0x%08lX", mcuRev);
          logging(LOG_INF, mcuInfo);
          
          // Get UID using LL functions
          uint32_t uid[3];
          uid[0] = LL_GetUID_Word0();
          uid[1] = LL_GetUID_Word1();
          uid[2] = LL_GetUID_Word2();
          snprintf(mcuInfo, sizeof(mcuInfo), "Unique ID: 0x%08lX%08lX%08lX", uid[0], uid[1], uid[2]);
          logging(LOG_INF, mcuInfo);
          
          // Get Flash Size using LL function
          uint32_t flashSize = LL_GetFlashSize();
          snprintf(mcuInfo, sizeof(mcuInfo), "Flash Size: %lu KB", flashSize);
          logging(LOG_INF, mcuInfo);
          
          // Get System Clock
          uint32_t sysClock = HAL_RCC_GetSysClockFreq();
          snprintf(mcuInfo, sizeof(mcuInfo), "System Clock: %lu Hz", sysClock);
          logging(LOG_INF, mcuInfo);
          
          // Get HCLK (AHB) Clock
          uint32_t hclk = HAL_RCC_GetHCLKFreq();
          snprintf(mcuInfo, sizeof(mcuInfo), "HCLK (AHB) Clock: %lu Hz", hclk);
          logging(LOG_INF, mcuInfo);
          
          // Get PCLK1 (APB1) Clock
          uint32_t pclk1 = HAL_RCC_GetPCLK1Freq();
          snprintf(mcuInfo, sizeof(mcuInfo), "PCLK1 (APB1) Clock: %lu Hz", pclk1);
          logging(LOG_INF, mcuInfo);
          
          // Get Core Voltage
          uint32_t voltage = HAL_PWREx_GetVoltageRange();
          snprintf(mcuInfo, sizeof(mcuInfo), "Core Voltage Range: %lu", voltage);
          logging(LOG_INF, mcuInfo);
          
          showMenu = 1;
          break;

        case MENU_HELP:
          logging(LOG_INF, "\r\n=== Help ===");
          logging(LOG_INF, "1. System Status - Shows current system parameters");
          logging(LOG_INF, "2. Display Flag - Shows the CybICS flag");
          logging(LOG_INF, "3. System Controls - Shows control status");
          logging(LOG_INF, "4. FreeRTOS Stats - Shows FreeRTOS task and system statistics");
          logging(LOG_INF, "5. MCU Information - Shows detailed MCU specifications");
          logging(LOG_INF, "6. Help - Shows this help message");
          logging(LOG_INF, "7. Logout - Logs out of the system");
          showMenu = 1;
          break;

        case MENU_LOGOUT:
          loggedIn = 0;
          passwordEntry = 0;  // Reset password entry state
          logging(LOG_INF, "\r\nLogged out successfully.");
          break;

        default:
          logging(LOG_ERR, "\r\nInvalid choice. Please try again.");
          showMenu = 1;
          break;
      }
    }
    
    osDelay(10);  // Small delay between iterations
  }
  /* USER CODE END Fuart */
}

/**
  * @brief  Period elapsed callback in non blocking mode
  * @note   This function is called  when TIM1 interrupt took place, inside
  * HAL_TIM_IRQHandler(). It makes a direct call to HAL_IncTick() to increment
  * a global variable "uwTick" used as application time base.
  * @param  htim : TIM handle
  * @retval None
  */
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
  /* USER CODE BEGIN Callback 0 */

  /* USER CODE END Callback 0 */
  if (htim->Instance == TIM1)
  {
    HAL_IncTick();
  }
  /* USER CODE BEGIN Callback 1 */

  /* USER CODE END Callback 1 */
}

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  logging(LOG_ERR, "Error_Handler"); 
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}

#ifdef  USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
