section .text
    global compute_telemetry_checksum

compute_telemetry_checksum:
    xor     eax, eax
    test    rdi, rdi
    jz      .done
    test    rsi, rsi
    jz      .done
    xor     rcx, rcx

.loop:
    movzx   edx, byte [rdi + rcx]
    rol     eax, 5
    xor     eax, edx
    add     eax, 0x9E3779B9
    inc     rcx
    cmp     rcx, rsi
    jl      .loop

.done:
    ret
