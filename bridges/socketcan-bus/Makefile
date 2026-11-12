CC = gcc
CFLAGS = -Wall -Wextra -O2 -std=c11
TARGET = can_ecu_tx

all: $(TARGET)

$(TARGET): can_ecu_tx.c
	$(CC) $(CFLAGS) $< -o $@

test: $(TARGET)
	python3 can_telemetry_rx.py vcan0 5 & \
	RX_PID=$$!; \
	sleep 0.2; \
	./$(TARGET) vcan0; \
	wait $$RX_PID

clean:
	rm -f $(TARGET)

.PHONY: all test clean
