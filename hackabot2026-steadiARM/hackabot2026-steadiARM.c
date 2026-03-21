#include <stdio.h>
#include <string.h>
#include "pico/stdlib.h"
#include "hardware/i2c.h"

// I2C defines
// This project uses I2C0 on GPIO8 (SDA) and GPIO9 (SCL) at 400 kHz.
#define I2C_PORT i2c0
#define I2C_SDA 8
#define I2C_SCL 9
#define I2C_BAUD_HZ (400 * 1000)

#define BMI160_ADDR 0x68
#define BMI160_REG_CHIP_ID 0x00
#define BMI160_REG_CMD 0x7E
#define BMI160_REG_GYR_DATA 0x0C
#define BMI160_REG_GYR_CONF 0x42
#define BMI160_REG_GYR_RANGE 0x43
#define BMI160_REG_ACC_DATA 0x12
#define BMI160_REG_ACC_CONF 0x40
#define BMI160_REG_ACC_RANGE 0x41

#define BMI160_CMD_ACC_NORMAL 0x11
#define BMI160_CMD_GYR_NORMAL 0x15
#define BMI160_CHIP_ID 0xD1

#define SAMPLE_RATE_HZ 100
#define SAMPLE_PERIOD_US (1000000 / SAMPLE_RATE_HZ)
#define WINDOW_SECONDS 2
#define WINDOW_SIZE (SAMPLE_RATE_HZ * WINDOW_SECONDS)

typedef struct {
    int16_t ax;
    int16_t ay;
    int16_t az;
    int16_t gx;
    int16_t gy;
    int16_t gz;
    uint64_t timestamp_us;
    bool valid;
} imu_sample_t;

typedef struct {
    imu_sample_t samples[WINDOW_SIZE];
    uint32_t head;
    uint32_t count;
    uint64_t total_pushes;
} sample_ring_t;

static inline int16_t le_i16(const uint8_t lo, const uint8_t hi) {
    return (int16_t)((((uint16_t)hi) << 8) | lo);
}

static void ring_push(sample_ring_t *ring, const imu_sample_t *sample) {
    ring->samples[ring->head] = *sample;
    ring->head = (ring->head + 1u) % WINDOW_SIZE;
    if (ring->count < WINDOW_SIZE) {
        ring->count++;
    }
    ring->total_pushes++;
}

static bool bmi160_read_regs(const uint8_t reg, uint8_t *dst, const size_t len) {
    if (i2c_write_blocking(I2C_PORT, BMI160_ADDR, &reg, 1, true) != 1) {
        return false;
    }
    return i2c_read_blocking(I2C_PORT, BMI160_ADDR, dst, (int)len, false) == (int)len;
}

static bool bmi160_write_reg(const uint8_t reg, const uint8_t value) {
    uint8_t buf[2] = {reg, value};
    return i2c_write_blocking(I2C_PORT, BMI160_ADDR, buf, 2, false) == 2;
}

static bool bmi160_init(void) {
    uint8_t chip_id = 0;

    if (!bmi160_read_regs(BMI160_REG_CHIP_ID, &chip_id, 1)) {
        return false;
    }
    if (chip_id != BMI160_CHIP_ID) {
        return false;
    }

    if (!bmi160_write_reg(BMI160_REG_CMD, BMI160_CMD_ACC_NORMAL)) {
        return false;
    }
    sleep_ms(50);
    if (!bmi160_write_reg(BMI160_REG_CMD, BMI160_CMD_GYR_NORMAL)) {
        return false;
    }
    sleep_ms(100);

    // ACC_CONF: ODR ~100 Hz, normal mode bandwidth.
    if (!bmi160_write_reg(BMI160_REG_ACC_CONF, 0x28)) {
        return false;
    }
    // ACC_RANGE: +/-4g
    if (!bmi160_write_reg(BMI160_REG_ACC_RANGE, 0x05)) {
        return false;
    }
    // GYR_CONF: ODR ~100 Hz, normal mode bandwidth.
    if (!bmi160_write_reg(BMI160_REG_GYR_CONF, 0x28)) {
        return false;
    }
    // GYR_RANGE: +/-500 dps
    if (!bmi160_write_reg(BMI160_REG_GYR_RANGE, 0x02)) {
        return false;
    }

    return true;
}

static bool bmi160_read_sample(imu_sample_t *out) {
    uint8_t gyr_raw[6];
    uint8_t acc_raw[6];

    if (!bmi160_read_regs(BMI160_REG_GYR_DATA, gyr_raw, sizeof(gyr_raw))) {
        return false;
    }
    if (!bmi160_read_regs(BMI160_REG_ACC_DATA, acc_raw, sizeof(acc_raw))) {
        return false;
    }

    out->gx = le_i16(gyr_raw[0], gyr_raw[1]);
    out->gy = le_i16(gyr_raw[2], gyr_raw[3]);
    out->gz = le_i16(gyr_raw[4], gyr_raw[5]);

    out->ax = le_i16(acc_raw[0], acc_raw[1]);
    out->ay = le_i16(acc_raw[2], acc_raw[3]);
    out->az = le_i16(acc_raw[4], acc_raw[5]);
    out->timestamp_us = time_us_64();
    out->valid = true;
    return true;
}

int main(void) {
    stdio_init_all();

    i2c_init(I2C_PORT, I2C_BAUD_HZ);
    gpio_set_function(I2C_SDA, GPIO_FUNC_I2C);
    gpio_set_function(I2C_SCL, GPIO_FUNC_I2C);
    gpio_pull_up(I2C_SDA);
    gpio_pull_up(I2C_SCL);

    sleep_ms(250);
    printf("VibraARM STORY-101 sampler boot\n");

    if (!bmi160_init()) {
        printf("BMI160 init failed (check wiring/address)\n");
        while (true) {
            sleep_ms(1000);
        }
    }

    sample_ring_t ring;
    memset(&ring, 0, sizeof(ring));

    uint64_t next_sample_us = time_us_64() + SAMPLE_PERIOD_US;
    uint64_t report_samples = 0;
    uint64_t dropped_samples = 0;
    uint64_t last_report_us = time_us_64();

    while (true) {
        const uint64_t now_us = time_us_64();
        if ((int64_t)(next_sample_us - now_us) > 0) {
            sleep_until(from_us_since_boot(next_sample_us));
        }

        imu_sample_t sample = {0};
        if (!bmi160_read_sample(&sample)) {
            sample.timestamp_us = time_us_64();
            sample.valid = false;
            dropped_samples++;
        }
        ring_push(&ring, &sample);
        report_samples++;

        // Elapsed-time compensation: advance in fixed steps even if loop jitter occurs.
        next_sample_us += SAMPLE_PERIOD_US;
        const uint64_t after_read_us = time_us_64();
        while ((int64_t)(next_sample_us - after_read_us) <= 0) {
            next_sample_us += SAMPLE_PERIOD_US;
        }

        const uint64_t since_report_us = after_read_us - last_report_us;
        if (since_report_us >= 1000000ULL) {
            const float effective_hz = (float)report_samples * 1000000.0f / (float)since_report_us;
            const imu_sample_t *latest = &ring.samples[(ring.head + WINDOW_SIZE - 1u) % WINDOW_SIZE];
            printf("rate~%.1fHz total=%llu drop=%llu window=%u/%u t=%llu valid=%d\n",
                   effective_hz,
                   (unsigned long long)ring.total_pushes,
                   (unsigned long long)dropped_samples,
                   ring.count,
                   WINDOW_SIZE,
                   (unsigned long long)latest->timestamp_us,
                   latest->valid ? 1 : 0);
            last_report_us = after_read_us;
            report_samples = 0;
        }
    }

    return 0;
}
