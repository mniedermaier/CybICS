/*
 * CybICS HMI Safety Parameter Validator
 * High Pressure Tank Override Authorization Module
 *
 * Found on the HMI workstation during forensic analysis.
 * This tool allows authorized engineers to override the
 * HPT/GST safety interlock configuration.
 *
 * The tool requires a 16-character authorization code that
 * is tied to the specific plant installation.
 *
 * CTF Challenge: Reverse engineer the authorization algorithm
 * and derive a valid code to retrieve the override key.
 */

#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <stdlib.h>

#define CODE_LEN  16
#define FLAG_LEN  39

/* Per-byte encoding key applied during code validation.
 * Validation: encoded[i] == (input[i] ^ key[i % 4]) + i  (mod 256) */
static const uint8_t validate_key[4] = { 0x13, 0x37, 0x42, 0x05 };

/* Pre-computed expected values for the authorization code */
static const uint8_t expected_code[CODE_LEN] = {
    0x46, 0x7A, 0x10, 0x4D,
    0x54, 0x81, 0x23, 0x5C,
    0x67, 0x7D, 0x27, 0x61,
    0x5E, 0x7E, 0x15, 0x33
};

/* Override activation key - revealed after successful validation */
static const uint8_t enc_flag[FLAG_LEN] = {
    0x74, 0x4E, 0x55, 0x7E, 0x74, 0x64, 0x1F, 0x7F,
    0x7A, 0x7E, 0x68, 0x55, 0x4E, 0x47, 0x03, 0x44,
    0x44, 0x68, 0x67, 0x7B, 0x74, 0x68, 0x44, 0x03,
    0x51, 0x04, 0x43, 0x4E, 0x68, 0x06, 0x59, 0x43,
    0x04, 0x45, 0x5B, 0x07, 0x54, 0x5C, 0x1E
};

static void banner(void)
{
    printf("############################################################\n");
    printf("#  CybICS HMI Safety Override Tool  v2.4.1                #\n");
    printf("#  High Pressure Tank Interlock Configuration              #\n");
    printf("#  ** AUTHORIZED PERSONNEL ONLY **                        #\n");
    printf("############################################################\n");
    printf("\n");
    printf("  WARNING: This tool modifies safety-critical parameters.\n");
    printf("  Unauthorized use may cause HPT overpressure events.\n");
    printf("  A blowout valve activation releases TOXIC GAS.\n");
    printf("\n");
    printf("------------------------------------------------------------\n");
    printf("  HPT Safe Range  : 60 - 90 bar\n");
    printf("  GST Safe Range  : 60 - 240 bar\n");
    printf("  Blowout trigger : > 220 bar\n");
    printf("------------------------------------------------------------\n\n");
}

/*
 * Validates the 16-character authorization code.
 *
 * For each byte i of the input code, the following must hold:
 *   ((input[i] ^ validate_key[i % 4]) + i) & 0xFF == expected_code[i]
 *
 * This ties the authorization code to the plant's configuration key,
 * making each installation's code unique.
 */
static int validate_code(const char *code, size_t len)
{
    if (len != CODE_LEN) {
        return 0;
    }

    for (int i = 0; i < CODE_LEN; i++) {
        uint8_t transformed = (uint8_t)(((uint8_t)code[i] ^ validate_key[i % 4]) + (uint8_t)i);
        if (transformed != expected_code[i]) {
            return 0;
        }
    }
    return 1;
}

static void activate_override(void)
{
    char flag[FLAG_LEN + 1];
    memset(flag, 0, sizeof(flag));

    for (int i = 0; i < FLAG_LEN; i++) {
        flag[i] = (char)(enc_flag[i] ^ 0x37);
    }

    printf("[+] Authorization ACCEPTED\n");
    printf("[+] Safety interlock configuration unlocked.\n");
    printf("\n");
    printf("[+] Current safety parameters:\n");
    printf("    HPT low  threshold : 60 bar\n");
    printf("    HPT high threshold : 90 bar\n");
    printf("    GST low  threshold : 60 bar\n");
    printf("    GST high threshold : 240 bar\n");
    printf("    Blowout valve open : 220 bar\n");
    printf("\n");
    printf("[+] Override activation key: %s\n", flag);
    printf("\n");
    printf("[!] WARNING: Modifying these thresholds can cause\n");
    printf("    catastrophic overpressure events!\n");
}

int main(void)
{
    char input[64];
    memset(input, 0, sizeof(input));

    banner();

    printf("Enter 16-character authorization code: ");
    fflush(stdout);

    if (fgets(input, sizeof(input), stdin) == NULL) {
        fprintf(stderr, "[-] Read error.\n");
        return 1;
    }

    /* Strip newline */
    size_t len = strlen(input);
    if (len > 0 && input[len - 1] == '\n') {
        input[--len] = '\0';
    }

    if (validate_code(input, len)) {
        activate_override();
    } else {
        printf("[-] INVALID authorization code.\n");
        printf("    Code must be exactly 16 characters.\n");
        printf("    Unauthorized override attempt logged.\n");
        return 1;
    }

    return 0;
}
