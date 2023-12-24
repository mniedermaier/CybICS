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
#include "display.h"

/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */
uint8_t RxData[20] = {0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0};
uint8_t TxData[20] = {'E','M','P','T','Y',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0};
char rpiIP[15] = {'U','N','K','N','O','W','N',0,0,0,0,0,0,0,0};
uint8_t GSTpressure=0;
uint8_t HPTpressure=0;

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

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

/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

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
  osThreadDef(display, Fdisplay, osPriorityNormal, 0, 128);
  displayHandle = osThreadCreate(osThread(display), NULL);

  /* definition and creation of physical */
  osThreadDef(physical, Fphysical, osPriorityAboveNormal, 0, 256);
  physicalHandle = osThreadCreate(osThread(physical), NULL);

  /* definition and creation of i2chandler */
  osThreadDef(i2chandler, Fi2chandler, osPriorityNormal, 0, 128);
  i2chandlerHandle = osThreadCreate(osThread(i2chandler), NULL);

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
  HAL_GPIO_WritePin(GPIOB, D_enable_Pin|D_rs_Pin|D_d4_Pin|D_d5_Pin
                          |D_d6_Pin|D_d7_Pin|C_off_Pin|C_on_Pin
                          |GST_low_Pin|GST_normal_Pin|GST_full_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOA, SV_red_Pin|SV_green_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOD, BO_green_Pin|BO_red_Pin|HPT_empty_Pin|HPT_low_Pin
                          |HPT_normal_Pin|HPT_high_Pin|HPT_critical_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pins : ST_heartbeat_Pin S_red_Pin S_green_Pin */
  GPIO_InitStruct.Pin = ST_heartbeat_Pin|S_red_Pin|S_green_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOC, &GPIO_InitStruct);

  /*Configure GPIO pins : C_sig_Pin PA1 PA2 PA3
                           PA4 PA5 PA6 */
  GPIO_InitStruct.Pin = C_sig_Pin|GPIO_PIN_1|GPIO_PIN_2|GPIO_PIN_3
                          |GPIO_PIN_4|GPIO_PIN_5|GPIO_PIN_6;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
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

  /*Configure GPIO pins : SV_red_Pin SV_green_Pin */
  GPIO_InitStruct.Pin = SV_red_Pin|SV_green_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

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
		HAL_I2C_Slave_Sequential_Transmit_IT(hi2c, TxData, sizeof(TxData), I2C_LAST_FRAME);
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
  Lcd_PortType ports[] = {
		  D_d4_GPIO_Port, D_d5_GPIO_Port, D_d6_GPIO_Port, D_d7_GPIO_Port
  };

  Lcd_PinType pins[] = {D_d4_Pin, D_d5_Pin, D_d6_Pin, D_d7_Pin};

  Lcd_HandleTypeDef lcd = Lcd_create(ports, pins, D_rs_GPIO_Port, D_rs_Pin, D_enable_GPIO_Port, D_enable_Pin, LCD_4_BIT_MODE);
  uint32_t secondsAfterStart = 0;
  char displayText[20];
  Lcd_string(&lcd, "CybICS v0.1");
  /* Infinite loop */
  for(;;)
  {
    snprintf(displayText, sizeof(displayText), "%li", ++secondsAfterStart);
    Lcd_cursor(&lcd, 0, 12);
    Lcd_string(&lcd, displayText);
    snprintf(displayText, sizeof(displayText), "IP: %s ", &rpiIP[shifting]);
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

  // clear Gas Storage Tank LEDs
  HAL_GPIO_WritePin(GST_full_GPIO_Port, GST_full_Pin, GPIO_PIN_SET);
  HAL_GPIO_WritePin(GST_normal_GPIO_Port, GST_normal_Pin, GPIO_PIN_SET);
  HAL_GPIO_WritePin(GST_low_GPIO_Port, GST_low_Pin, GPIO_PIN_SET);

  // clear Compressor LEDs
  HAL_GPIO_WritePin(C_on_GPIO_Port, C_on_Pin, GPIO_PIN_SET);
  HAL_GPIO_WritePin(C_off_GPIO_Port, C_off_Pin, GPIO_PIN_SET);

  // clear High Pressure Tank LEDs
  HAL_GPIO_WritePin(HPT_critical_GPIO_Port, HPT_critical_Pin, GPIO_PIN_SET);
  HAL_GPIO_WritePin(HPT_high_GPIO_Port, HPT_high_Pin, GPIO_PIN_SET);
  HAL_GPIO_WritePin(HPT_normal_GPIO_Port, HPT_normal_Pin, GPIO_PIN_SET);
  HAL_GPIO_WritePin(HPT_low_GPIO_Port, HPT_low_Pin, GPIO_PIN_SET);
  HAL_GPIO_WritePin(HPT_empty_GPIO_Port, HPT_empty_Pin, GPIO_PIN_SET);

  // clear Blow Out LEDs
  HAL_GPIO_WritePin(BO_red_GPIO_Port, BO_red_Pin, GPIO_PIN_SET);
  HAL_GPIO_WritePin(BO_green_GPIO_Port, BO_green_Pin, GPIO_PIN_SET); 

  // clear System Valve LEDs
  HAL_GPIO_WritePin(SV_red_GPIO_Port, SV_red_Pin, GPIO_PIN_SET);
  HAL_GPIO_WritePin(SV_green_GPIO_Port, SV_green_Pin, GPIO_PIN_SET); 

  // clear System LEDs
  HAL_GPIO_WritePin(S_red_GPIO_Port, S_red_Pin, GPIO_PIN_SET);
  HAL_GPIO_WritePin(S_green_GPIO_Port, S_green_Pin, GPIO_PIN_SET); 
  
  GPIO_PinState buttonState;
  GPIO_PinState cState;

  uint16_t HPTdelay=0;
  /* Infinite loop */
  for(;;)
  {
    //GPIO_PinState buttonState = HAL_GPIO_ReadPin(button_GPIO_Port, button_Pin);
    GPIO_PinState cState = HAL_GPIO_ReadPin(C_sig_GPIO_Port, C_sig_Pin);
    /**
     * When compressor is running:
     * - Increase HPT pressure
     * - LED Compressor should be green
    */
    if(cState)
    {
      HAL_GPIO_WritePin(C_on_GPIO_Port, C_on_Pin, GPIO_PIN_RESET);
      HAL_GPIO_WritePin(C_off_GPIO_Port, C_off_Pin, GPIO_PIN_SET);
      if(HPTdelay>100) // increase pressure 1 per second
      {
        if(HPTpressure<255)
        {
          HPTpressure++;
        }        
        HPTdelay=0;
      }
      
    }
    else
    {
      HAL_GPIO_WritePin(C_on_GPIO_Port, C_on_Pin, GPIO_PIN_SET);
      HAL_GPIO_WritePin(C_off_GPIO_Port, C_off_Pin, GPIO_PIN_RESET);      
      if(HPTdelay>100) // decrease pressure 1 per second
      {
        HPTuse = rand() % 5;
        if((HPTpressure-HPTuse)>=0)
        {
          HPTpressure = HPTpressure - HPTuse;
        }        
        HPTdelay=0;
      }
    }

    if(HPTpressure<20)
    {
      HAL_GPIO_WritePin(HPT_critical_GPIO_Port, HPT_critical_Pin, GPIO_PIN_SET);
      HAL_GPIO_WritePin(HPT_high_GPIO_Port, HPT_high_Pin, GPIO_PIN_SET);
      HAL_GPIO_WritePin(HPT_normal_GPIO_Port, HPT_normal_Pin, GPIO_PIN_SET);
      HAL_GPIO_WritePin(HPT_low_GPIO_Port, HPT_low_Pin, GPIO_PIN_SET);
      HAL_GPIO_WritePin(HPT_empty_GPIO_Port, HPT_empty_Pin, GPIO_PIN_RESET);
    }
    else if (HPTpressure<50)
    {
      HAL_GPIO_WritePin(HPT_critical_GPIO_Port, HPT_critical_Pin, GPIO_PIN_SET);
      HAL_GPIO_WritePin(HPT_high_GPIO_Port, HPT_high_Pin, GPIO_PIN_SET);
      HAL_GPIO_WritePin(HPT_normal_GPIO_Port, HPT_normal_Pin, GPIO_PIN_SET);
      HAL_GPIO_WritePin(HPT_low_GPIO_Port, HPT_low_Pin, GPIO_PIN_RESET);
      HAL_GPIO_WritePin(HPT_empty_GPIO_Port, HPT_empty_Pin, GPIO_PIN_SET);
    }
    else if (HPTpressure<100)
    {
      HAL_GPIO_WritePin(HPT_critical_GPIO_Port, HPT_critical_Pin, GPIO_PIN_SET);
      HAL_GPIO_WritePin(HPT_high_GPIO_Port, HPT_high_Pin, GPIO_PIN_SET);
      HAL_GPIO_WritePin(HPT_normal_GPIO_Port, HPT_normal_Pin, GPIO_PIN_RESET);
      HAL_GPIO_WritePin(HPT_low_GPIO_Port, HPT_low_Pin, GPIO_PIN_SET);
      HAL_GPIO_WritePin(HPT_empty_GPIO_Port, HPT_empty_Pin, GPIO_PIN_SET);
    }
    else if (HPTpressure<150)
    {
      HAL_GPIO_WritePin(HPT_critical_GPIO_Port, HPT_critical_Pin, GPIO_PIN_SET);
      HAL_GPIO_WritePin(HPT_high_GPIO_Port, HPT_high_Pin, GPIO_PIN_RESET);
      HAL_GPIO_WritePin(HPT_normal_GPIO_Port, HPT_normal_Pin, GPIO_PIN_SET);
      HAL_GPIO_WritePin(HPT_low_GPIO_Port, HPT_low_Pin, GPIO_PIN_SET);
      HAL_GPIO_WritePin(HPT_empty_GPIO_Port, HPT_empty_Pin, GPIO_PIN_SET);
    }
    else
    {
      HAL_GPIO_WritePin(HPT_critical_GPIO_Port, HPT_critical_Pin, GPIO_PIN_RESET);
      HAL_GPIO_WritePin(HPT_high_GPIO_Port, HPT_high_Pin, GPIO_PIN_SET);
      HAL_GPIO_WritePin(HPT_normal_GPIO_Port, HPT_normal_Pin, GPIO_PIN_SET);
      HAL_GPIO_WritePin(HPT_low_GPIO_Port, HPT_low_Pin, GPIO_PIN_SET);
      HAL_GPIO_WritePin(HPT_empty_GPIO_Port, HPT_empty_Pin, GPIO_PIN_SET);
    }

    /**
     * Blowout if the HPTpressure if over 200
    */  
    if(HPTpressure>200)
    {
      HAL_GPIO_WritePin(BO_red_GPIO_Port, BO_red_Pin, GPIO_PIN_RESET);
      HAL_GPIO_WritePin(BO_green_GPIO_Port, BO_green_Pin, GPIO_PIN_SET); 
      if(HPTdelay>100) // decrease pressure 1 per second
      {
        HPTuse = rand() % 20;
        if((HPTpressure-HPTuse)>=0)
        {
          HPTpressure = HPTpressure - HPTuse;
        }        
        HPTdelay=0;
      }
    }
    else
    {
      HAL_GPIO_WritePin(BO_red_GPIO_Port, BO_red_Pin, GPIO_PIN_SET);
      HAL_GPIO_WritePin(BO_green_GPIO_Port, BO_green_Pin, GPIO_PIN_RESET);     
    }

    /**
     * System operating, when pressure is in normal range
    */  
    if((HPTpressure>50) && (HPTpressure<100))
    {
      HAL_GPIO_WritePin(S_red_GPIO_Port, S_red_Pin, GPIO_PIN_SET);
      HAL_GPIO_WritePin(S_green_GPIO_Port, S_green_Pin, GPIO_PIN_RESET); 
    }
    else
    {
      HAL_GPIO_WritePin(S_red_GPIO_Port, S_red_Pin, GPIO_PIN_RESET);
      HAL_GPIO_WritePin(S_green_GPIO_Port, S_green_Pin, GPIO_PIN_SET); 
    }

    GSTpressure = rand();
    /**
     * Set the right values in the TX Data:
     * - GSTTpressure
     * - HPTpressure
     * Format: GST: %03d HPT: %03d
    */    
    snprintf(TxData, sizeof(TxData), "GST: %03d HPT: %03d", GSTpressure, HPTpressure);

    HPTdelay = HPTdelay+1;
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
  if (htim->Instance == TIM1) {
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
