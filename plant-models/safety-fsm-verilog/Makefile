IVERILOG = iverilog
VVP = vvp
TARGET = bms_sim.vvp

all: $(TARGET)

$(TARGET): bms_interlock.v tb_bms_interlock.v
	$(IVERILOG) -o $(TARGET) bms_interlock.v tb_bms_interlock.v

test: $(TARGET)
	$(VVP) $(TARGET)

clean:
	rm -f $(TARGET) *.vcd

.PHONY: all test clean
