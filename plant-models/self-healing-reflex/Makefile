IVERILOG = iverilog
VVP = vvp
TARGET = self_heal_sim.vvp

all: $(TARGET)

$(TARGET): self_healing_matrix.v tb_self_healing_matrix.v
	$(IVERILOG) -o $(TARGET) self_healing_matrix.v tb_self_healing_matrix.v

test: $(TARGET)
	$(VVP) $(TARGET)

clean:
	rm -f $(TARGET) *.vcd

.PHONY: all test clean
