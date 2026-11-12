NASM = nasm
CC = gcc
NASMFLAGS = -f elf64 -g -F dwarf
CFLAGS = -Wall -Wextra -O2 -std=c11
LDFLAGS = -lm

TARGET = phy_fingerprint_runner
OBJS = read_tsc.o phy_fingerprint.o

all: $(TARGET)

read_tsc.o: read_tsc.asm
	$(NASM) $(NASMFLAGS) $< -o $@

phy_fingerprint.o: phy_fingerprint.c
	$(CC) $(CFLAGS) -c $< -o $@

$(TARGET): $(OBJS)
	$(CC) $(OBJS) $(LDFLAGS) -o $@

test: $(TARGET)
	./$(TARGET)

clean:
	rm -f $(OBJS) $(TARGET)

.PHONY: all test clean
