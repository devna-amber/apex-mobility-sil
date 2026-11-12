#define _DEFAULT_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdint.h>
#include <net/if.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <linux/can.h>
#include <linux/can/raw.h>

static uint8_t compute_can_crc8(const uint8_t *data, size_t len) {
    uint8_t crc = 0xFF;
    for (size_t i = 0; i < len; i++) {
        crc ^= *(data + i);
        for (int b = 0; b < 8; b++) {
            crc = (crc & 0x80) ? (uint8_t)((crc << 1) ^ 0x1D) : (uint8_t)(crc << 1);
        }
    }
    return crc;
}

int main(int argc, char **argv) {
    const char *ifname = (argc > 1) ? *(argv + 1) : "vcan0";
    int sock = socket(PF_CAN, SOCK_RAW, CAN_RAW);
    if (sock < 0) {
        perror("socket(PF_CAN)");
        return 1;
    }

    struct ifreq ifr;
    memset(&ifr, 0, sizeof(ifr));
    strncpy(ifr.ifr_name, ifname, IFNAMSIZ - 1);
    if (ioctl(sock, SIOCGIFINDEX, &ifr) < 0) {
        perror("ioctl(SIOCGIFINDEX)");
        close(sock);
        return 1;
    }

    struct sockaddr_can addr;
    memset(&addr, 0, sizeof(addr));
    addr.can_family = AF_CAN;
    addr.can_ifindex = ifr.ifr_ifindex;

    if (bind(sock, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("bind(AF_CAN)");
        close(sock);
        return 1;
    }

    for (int i = 0; i < 5; i++) {
        struct can_frame frame;
        memset(&frame, 0, sizeof(frame));
        frame.can_id  = 0x101;
        frame.can_dlc = 8;

        uint16_t pack_voltage_dv = (uint16_t)(4020 - i * 5);
        int16_t  pack_current_da = (int16_t)(180 + i * 25);
        uint8_t  soc_percent     = (uint8_t)(85 - i);
        uint8_t  max_temp_c      = (uint8_t)(38 + i * 4);
        uint8_t  alive_counter   = (uint8_t)(i & 0x0F);

        *(frame.data + 0) = (uint8_t)(pack_voltage_dv >> 8);
        *(frame.data + 1) = (uint8_t)(pack_voltage_dv & 0xFF);
        *(frame.data + 2) = (uint8_t)((uint16_t)pack_current_da >> 8);
        *(frame.data + 3) = (uint8_t)((uint16_t)pack_current_da & 0xFF);
        *(frame.data + 4) = soc_percent;
        *(frame.data + 5) = max_temp_c;
        *(frame.data + 6) = alive_counter;
        *(frame.data + 7) = compute_can_crc8(frame.data, 7);

        if (write(sock, &frame, sizeof(struct can_frame)) != sizeof(struct can_frame)) {
            perror("write(CAN frame)");
            close(sock);
            return 1;
        }
        printf("[C-ECU-TX] Sent CAN ID 0x%03X | V=%.1fV | I=%.1fA | SoC=%u%% | Temp=%uC | CRC=0x%02X\n",
               frame.can_id, pack_voltage_dv / 10.0, pack_current_da / 10.0,
               soc_percent, max_temp_c, *(frame.data + 7));
        usleep(50000);
    }

    close(sock);
    return 0;
}
