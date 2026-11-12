; bridges/can-phy-fingerprint/read_tsc.asm
; Reads the 64-bit hardware CPU Time Stamp Counter (TSC) using serializing rdtscp.
; Returns:
;   rax = 64-bit monotonic hardware cycle count

section .text
    global read_hw_tsc

read_hw_tsc:
    rdtscp                  ; Read 64-bit TSC into EDX:EAX and serialize instruction stream
    shl     rdx, 32         ; Shift upper 32 bits of TSC into upper half of RDX
    or      rax, rdx        ; Combine EDX and EAX into full 64-bit return value in RAX
    ret
