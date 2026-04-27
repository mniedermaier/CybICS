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
 * Flag is stored here and printed only when diagnostics pass integrity check
 * -------------------------------------------------------------------------- */
void maintenance_shell(void) {
    printf("\n");
    printf("  *** MAINTENANCE MODE ACTIVATED ***\n");
    printf("  PLC Diagnostic System - Internal Access\n");
    printf("  ----------------------------------------\n");
    printf("  Congratulations, you have gained control\n");
    printf("  of the PLC diagnostics process!\n");
    printf("\n");
    printf("  FLAG: CybICS(buff3r_0v3rfl0w_pwn3d)\n");
    printf("\n");
    printf("  In a real ICS environment, this level of\n");
    printf("  access would allow full control over the\n");
    printf("  physical process. Stay ethical.\n");
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

    /* BUG: strcpy() does not check the length of `input`!
     * If `input` is longer than 64 bytes the stack will be overwritten. */
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

    /* fgets IS safe here – it limits to sizeof(input).
     * The vulnerability is inside run_diagnostic(), not here. */
    if (fgets(input, sizeof(input), stdin) == NULL) {
        fprintf(stderr, "[-] Read error.\n");
        return 1;
    }

    /* Strip trailing newline */
    input[strcspn(input, "\n")] = '\0';

    run_diagnostic(input);

    return 0;
}
