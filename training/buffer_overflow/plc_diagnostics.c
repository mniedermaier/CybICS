/*
 * CybICS - PLC Diagnostics Service
 * Version: 1.3.37
 *
 * Internal ICS diagnostic tool for querying PLC status.
 * WARNING: This binary is only intended for internal maintenance use.
 *
 * Usage: ./plc_diagnostics
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>

/* --------------------------------------------------------------------------
 * Internal maintenance backdoor - DO NOT EXPOSE TO NETWORK
 * -------------------------------------------------------------------------- */
void maintenance_shell(void) {
    unsigned char encoded[] = {
        0x19, 0x23, 0x38, 0x13, 0x19, 0x09, 0x72, 0x38,
        0x2f, 0x3c, 0x3c, 0x69, 0x28, 0x05, 0x6a, 0x2c,
        0x69, 0x28, 0x3c, 0x36, 0x6a, 0x2d, 0x05, 0x2a,
        0x2d, 0x34, 0x69, 0x3e, 0x73,
    };
    unsigned char key = 0x5A;

    char flag[sizeof(encoded) + 1];
    for (size_t i = 0; i < sizeof(encoded); i++)
        flag[i] = encoded[i] ^ key;
    flag[sizeof(encoded)] = '\0';

    printf("\n");
    printf("  *** MAINTENANCE MODE ACTIVATED ***\n");
    printf("  PLC Diagnostic System - Internal Access\n");
    printf("  ----------------------------------------\n");
    printf("  FLAG: %s\n", flag);
    printf("\n");
    fflush(stdout);
    exit(0);
}




/* --------------------------------------------------------------------------
 * Process a diagnostic command string from the operator console
 * -------------------------------------------------------------------------- */
void run_diagnostic(char *input) {
    char cmd_buffer[64];   /* Fixed-size command buffer */

    printf("[*] Running diagnostic: %s\n", input);

    strcpy(cmd_buffer, input);

    printf("[*] Diagnostic command stored at: %p\n", (void *)cmd_buffer);
    printf("[+] Diagnostic completed successfully.\n");
}

/* --------------------------------------------------------------------------
 * Banner
 * -------------------------------------------------------------------------- */
void print_banner(void) {
    printf("╔══════════════════════════════════════════╗\n");
    printf("║   CybICS PLC Diagnostics Service v1.3   ║\n");
    printf("║   Internal Maintenance Tool              ║\n");
    printf("╚══════════════════════════════════════════╝\n");
    printf("\n");
}

/* --------------------------------------------------------------------------
 * Main – reads a single diagnostic command from stdin
 * -------------------------------------------------------------------------- */
int main(void) {
    char input[256];

    print_banner();

    printf("Enter diagnostic command (max 64 chars): ");
    fflush(stdout);

    if (fgets(input, sizeof(input), stdin) == NULL) {
        fprintf(stderr, "[-] Read error.\n");
        return 1;
    }

    /* Strip trailing newline */
    input[strcspn(input, "\n")] = '\0';

    run_diagnostic(input);

    return 0;
}
