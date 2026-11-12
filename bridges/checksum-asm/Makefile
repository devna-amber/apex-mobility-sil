NASM = nasm
CC = gcc
NASMFLAGS = -f elf64 -g -F dwarf
CFLAGS = -Wall -Wextra -O2 -std=c11

TARGET = checksum_runner
OBJS = telemetry_crc.o test_checksum.o

all: $(TARGET)

telemetry_crc.o: telemetry_crc.asm
	$(NASM) $(NASMFLAGS) $< -o $@

test_checksum.o: test_checksum.c
	$(CC) $(CFLAGS) -c $< -o $@

$(TARGET): $(OBJS)
	$(CC) $(OBJS) -o $@

test: $(TARGET)
	./$(TARGET)

clean:
	rm -f $(OBJS) $(TARGET)

.PHONY: all test clean
