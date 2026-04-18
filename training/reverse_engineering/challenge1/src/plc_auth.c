/*
 * CybICS PLC Maintenance Authentication Tool
 * Gas Pressure Control System - Operator Access Module
 *
 * Found on the CybICS PLC during incident response.
 * This binary appears to be a custom maintenance utility
 * used by the original vendor to access the PLC.
 *
 * CTF Challenge: Reverse engineer this binary to recover
 * the operator password and retrieve the maintenance code.
 */

#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <stdlib.h>

#define PW_LEN    12
#define FLAG_LEN  35

/* Operator password stored with simple encoding to protect it from
 * accidental disclosure in plaintext memory dumps.
 * Encoding key is embedded in the authentication logic. */
static const uint8_t enc_pw[PW_LEN] = {
    0x0F, 0x76, 0x73, 0x2C, 0x36, 0x71,
    0x2C, 0x76, 0x2C, 0x21, 0x71, 0x63
};

/* System diagnostic flag - only shown after successful authentication */
static const uint8_t enc_flag[FLAG_LEN] = {
    0x01, 0x3B, 0x20, 0x0B, 0x01, 0x11, 0x6A, 0x3A,
    0x72, 0x30, 0x1D, 0x73, 0x31, 0x1D, 0x2C, 0x72,
    0x36, 0x1D, 0x27, 0x2C, 0x21, 0x30, 0x3B, 0x32,
    0x36, 0x2B, 0x72, 0x2C, 0x1D, 0x76, 0x1D, 0x12,
    0x0E, 0x01, 0x6B
};

static void banner(void)
{
    printf("==========================================================\n");
    printf("  CybICS PLC Maintenance Tool  v1.2.0\n");
    printf("  Gas Pressure Control System  - Operator Access\n");
    printf("  (c) CybICS Industrial Systems\n");
    printf("==========================================================\n");
    printf("  System:   HPT/GST Pressure Controller\n");
    printf("  Protocol: Modbus TCP\n");
    printf("  Status:   CONNECTED\n");
    printf("----------------------------------------------------------\n\n");
}

static int check_credentials(const char *input)
{
    char pw[PW_LEN + 1];
    memset(pw, 0, sizeof(pw));

    /* Decode the stored password for comparison */
    for (int i = 0; i < PW_LEN; i++) {
        pw[i] = (char)(enc_pw[i] ^ 0x42);
    }

    return (strncmp(input, pw, PW_LEN + 1) == 0);
}

static void print_flag(void)
{
    char flag[FLAG_LEN + 1];
    memset(flag, 0, sizeof(flag));

    for (int i = 0; i < FLAG_LEN; i++) {
        flag[i] = (char)(enc_flag[i] ^ 0x42);
    }

    printf("[+] Maintenance mode ACTIVE\n");
    printf("[+] HPT current pressure : 87 bar  [NORMAL]\n");
    printf("[+] GST current pressure : 142 bar [NORMAL]\n");
    printf("[+] Compressor state     : OFF\n");
    printf("[+] Blowout valve        : CLOSED\n");
    printf("\n");
    printf("[+] Vendor diagnostic code: %s\n", flag);
}

int main(void)
{
    char input[64];
    memset(input, 0, sizeof(input));

    banner();

    printf("Enter operator password: ");
    fflush(stdout);

    if (fgets(input, sizeof(input), stdin) == NULL) {
        fprintf(stderr, "[-] Read error.\n");
        return 1;
    }

    /* Strip newline */
    size_t len = strlen(input);
    if (len > 0 && input[len - 1] == '\n') {
        input[len - 1] = '\0';
    }

    if (check_credentials(input)) {
        print_flag();
    } else {
        printf("[-] Authentication FAILED. Invalid operator code.\n");
        printf("    Contact your system administrator for access.\n");
        printf("    Incident will be logged.\n");
        return 1;
    }

    return 0;
}
