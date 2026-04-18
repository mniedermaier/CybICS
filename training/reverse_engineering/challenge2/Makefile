CC      := gcc
CFLAGS  := -O0 -g0 -Wall -Wextra -static
TARGET  := hmi_validator
SRC     := src/hmi_validator.c
DOCKER_DEST := ../../../software/landing/static/challenges/$(TARGET)/$(TARGET)

.PHONY: all clean deploy

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) -o $@ $<

# Copy built binary into the Docker challenge folder
deploy: $(TARGET)
	cp $(TARGET) $(DOCKER_DEST)

clean:
	rm -f $(TARGET)
