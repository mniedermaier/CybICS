# CybICS Buffer Overflow Challenge – Build System
#
# Compiler flags chosen deliberately for the challenge:
#   -fno-stack-protector   disable stack canaries (no SSP cookie)
#   -no-pie                produce a non-position-independent executable
#                          so that function addresses are fixed at link time
#   -O0                    no optimisation – keeps stack frames predictable
#   -z execstack           mark the stack executable
#
# ASLR must be disabled at runtime (see README).

CC      = gcc
CFLAGS  = -O0 -fno-stack-protector -no-pie -z execstack -g
TARGET  = plc_diagnostics
SRC     = plc_diagnostics.c

.PHONY: all clean run

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) -o $(TARGET) $(SRC)
	@echo ""
	@echo "[+] Binary compiled: ./$(TARGET)"
	@echo "[+] Compile flags: $(CFLAGS)"
	@echo ""

clean:
	rm -f $(TARGET)

run: $(TARGET)
	./$(TARGET)
