#!/bin/bash

# Build the STM32 application
west build -b nucleo_g070rb -- -DCONFIG_COMPILER_WARNINGS_AS_ERRORS=y
