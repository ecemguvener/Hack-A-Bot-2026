#include <stdio.h>
#include <string.h>
#include <math.h>
#include "pico/stdlib.h"
#include "hardware/i2c.h"
#include "hardware/spi.h"

// ── Onboard LED ───────────────────────────────────────────────────────────────
#define LED_PIN 25

// ── I2C (BMI160) ──────────────────────────────────────────────────────────────
#define I2C_PORT i2c0
#define I2C_SDA 8
#define I2C_SCL 9
#define I2C_BAUD_HZ (400 * 1000)

// ── SPI (NRF24L01) ────────────────────────────────────────────────────────────
// Uses SPI1 to avoid conflict with I2C on GP8/9
// Wiring: SCK=GP10, MOSI=GP11, MISO=GP12, CSN=GP13, CE=GP14
#define NRF_SPI      spi1
#define NRF_SCK_PIN  10
#define NRF_MOSI_PIN 11
#define NRF_MISO_PIN 12
#define NRF_CSN_PIN  13
#define NRF_CE_PIN   14

// NRF24L01 registers
#define NRF_CONFIG      0x00
#define NRF_EN_AA       0x01
#define NRF_EN_RXADDR   0x02
#define NRF_SETUP_AW    0x03
#define NRF_SETUP_RETR  0x04
#define NRF_RF_CH       0x05
#define NRF_RF_SETUP    0x06
#define NRF_STATUS      0x07
#define NRF_TX_ADDR     0x10
#define NRF_RX_ADDR_P0  0x0A
#define NRF_RX_PW_P0    0x11

// NRF24L01 commands
#define NRF_CMD_R_REG       0x00
#define NRF_CMD_W_REG       0x20
#define NRF_CMD_W_TX        0xA0
#define NRF_CMD_FLUSH_TX    0xE1
#define NRF_CMD_NOP         0xFF

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

#define SAMPLE_RATE_HZ   100
#define SAMPLE_PERIOD_US (1000000 / SAMPLE_RATE_HZ)
#define WINDOW_SECONDS   2
#define WINDOW_SIZE      (SAMPLE_RATE_HZ * WINDOW_SECONDS)

// High-pass IIR alpha (removes gravity/DC, keeps tremor >~1 Hz)
#define HP_ALPHA 0.9f

// Payload sent over radio — 20 bytes to match teammate's receiver payload_size=20
// Sent as a packed CSV string e.g. "5.20,0.031,0,5.20\n" (null-padded to 20)
#define RADIO_PAYLOAD_SIZE 20
typedef uint8_t radio_payload_t[RADIO_PAYLOAD_SIZE];

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

// ── NRF24L01 driver ───────────────────────────────────────────────────────────

static inline void nrf_csn_low(void)  { gpio_put(NRF_CSN_PIN, 0); }
static inline void nrf_csn_high(void) { gpio_put(NRF_CSN_PIN, 1); }
static inline void nrf_ce_low(void)   { gpio_put(NRF_CE_PIN, 0); }
static inline void nrf_ce_high(void)  { gpio_put(NRF_CE_PIN, 1); }

static uint8_t nrf_write_reg(uint8_t reg, uint8_t val) {
    uint8_t tx[2] = { (uint8_t)(NRF_CMD_W_REG | reg), val };
    uint8_t rx[2];
    nrf_csn_low();
    spi_write_read_blocking(NRF_SPI, tx, rx, 2);
    nrf_csn_high();
    return rx[0];  // status byte
}

static void nrf_write_reg_buf(uint8_t reg, const uint8_t *buf, size_t len) {
    uint8_t cmd = NRF_CMD_W_REG | reg;
    nrf_csn_low();
    spi_write_blocking(NRF_SPI, &cmd, 1);
    spi_write_blocking(NRF_SPI, buf, len);
    nrf_csn_high();
}

static void nrf_flush_tx(void) {
    uint8_t cmd = NRF_CMD_FLUSH_TX;
    nrf_csn_low();
    spi_write_blocking(NRF_SPI, &cmd, 1);
    nrf_csn_high();
}

static void nrf_init(void) {
    spi_init(NRF_SPI, 4000000);
    gpio_set_function(NRF_SCK_PIN,  GPIO_FUNC_SPI);
    gpio_set_function(NRF_MOSI_PIN, GPIO_FUNC_SPI);
    gpio_set_function(NRF_MISO_PIN, GPIO_FUNC_SPI);

    gpio_init(NRF_CSN_PIN); gpio_set_dir(NRF_CSN_PIN, GPIO_OUT); nrf_csn_high();
    gpio_init(NRF_CE_PIN);  gpio_set_dir(NRF_CE_PIN,  GPIO_OUT); nrf_ce_low();

    sleep_ms(5);

    // Must match teammate's receiver receive_pipe = b"\xe1\xf0\xf0\xf0\xf0"
    static const uint8_t addr[5] = {0xe1, 0xf0, 0xf0, 0xf0, 0xf0};

    nrf_write_reg(NRF_CONFIG,     0x0E);  // TX mode, 2-byte CRC, power up
    nrf_write_reg(NRF_EN_AA,      0x01);  // auto-ack on pipe 0
    nrf_write_reg(NRF_EN_RXADDR,  0x01);  // enable pipe 0
    nrf_write_reg(NRF_SETUP_AW,   0x03);  // 5-byte addresses
    nrf_write_reg(NRF_SETUP_RETR, 0x68);  // 1750µs delay, 8 retries — matches teammate
    nrf_write_reg(NRF_RF_CH,      46);    // channel 46 — matches teammate's default
    nrf_write_reg(NRF_RF_SETUP,   0x26);  // 250 Kbps, 0 dBm — matches teammate's SPEED_250K
    nrf_write_reg_buf(NRF_TX_ADDR,    addr, 5);
    nrf_write_reg_buf(NRF_RX_ADDR_P0, addr, 5);  // needed for auto-ack
    nrf_write_reg(NRF_RX_PW_P0, RADIO_PAYLOAD_SIZE);

    nrf_flush_tx();
    nrf_write_reg(NRF_STATUS, 0x70);  // clear flags
}

// Send payload, block until sent or max retries hit (< 5 ms total)
static void nrf_send(const radio_payload_t payload) {
    nrf_write_reg(NRF_STATUS, 0x70);
    nrf_flush_tx();

    uint8_t cmd = NRF_CMD_W_TX;
    nrf_csn_low();
    spi_write_blocking(NRF_SPI, &cmd, 1);
    spi_write_blocking(NRF_SPI, payload, RADIO_PAYLOAD_SIZE);
    nrf_csn_high();

    // Pulse CE to start transmission
    nrf_ce_high();
    sleep_us(15);
    nrf_ce_low();

    // Wait for TX_DS (bit 5) or MAX_RT (bit 4) in STATUS
    for (int i = 0; i < 50; i++) {
        sleep_us(100);
        nrf_csn_low();
        uint8_t nop = NRF_CMD_NOP;
        uint8_t status;
        spi_write_read_blocking(NRF_SPI, &nop, &status, 1);
        nrf_csn_high();
        if (status & 0x30) break;  // done
    }
}

// ── Signal processing ─────────────────────────────────────────────────────────

// Per-axis high-pass filter state
static float hp_prev_in[3]  = {0};
static float hp_prev_out[3] = {0};

static float highpass(int axis, float in) {
    float out = HP_ALPHA * (hp_prev_out[axis] + in - hp_prev_in[axis]);
    hp_prev_in[axis]  = in;
    hp_prev_out[axis] = out;
    return out;
}

static float compute_rms(const float *data, int len) {
    float sum = 0;
    for (int i = 0; i < len; i++) sum += data[i] * data[i];
    return sqrtf(sum / (float)len);
}

static float zero_crossing_freq(const float *data, int len) {
    float mean = 0;
    for (int i = 0; i < len; i++) mean += data[i];
    mean /= (float)len;

    int crossings = 0;
    bool prev_above = (data[0] - mean) >= 0.0f;
    for (int i = 1; i < len; i++) {
        bool curr_above = (data[i] - mean) >= 0.0f;
        if (curr_above != prev_above) crossings++;
        prev_above = curr_above;
    }
    float window_time = (float)len / (float)SAMPLE_RATE_HZ;
    return (float)(crossings / 2) / window_time;
}

// 5-sample moving average for frequency smoothing
static float freq_history[5] = {0};
static int   freq_hist_idx   = 0;

static float smooth_freq(float new_freq) {
    freq_history[freq_hist_idx % 5] = new_freq;
    freq_hist_idx++;
    float sum = 0;
    for (int i = 0; i < 5; i++) sum += freq_history[i];
    return sum / 5.0f;
}

// Filtered sample storage (one float buffer per axis)
static float fbuf_x[WINDOW_SIZE];
static float fbuf_y[WINDOW_SIZE];
static float fbuf_z[WINDOW_SIZE];

int main(void) {
    stdio_init_all();

    // Onboard LED — blinks to show the Pico is alive
    gpio_init(LED_PIN);
    gpio_set_dir(LED_PIN, GPIO_OUT);
    gpio_put(LED_PIN, 1);  // on during boot

    // I2C for BMI160
    i2c_init(I2C_PORT, I2C_BAUD_HZ);
    gpio_set_function(I2C_SDA, GPIO_FUNC_I2C);
    gpio_set_function(I2C_SCL, GPIO_FUNC_I2C);
    gpio_pull_up(I2C_SDA);
    gpio_pull_up(I2C_SCL);

    sleep_ms(250);
    printf("steadiARM boot\n");

    if (!bmi160_init()) {
        printf("BMI160 init FAILED (check wiring/address)\n");
        // Fast blink = error
        while (true) {
            gpio_put(LED_PIN, 1); sleep_ms(100);
            gpio_put(LED_PIN, 0); sleep_ms(100);
        }
    }
    printf("BMI160 OK\n");

    // NRF24L01 on SPI1
    nrf_init();
    printf("NRF24L01 ready\n");

    // Calibration factor k (motor_freq = k * tremor_freq)
    float k = 1.0f;

    sample_ring_t ring;
    memset(&ring, 0, sizeof(ring));
    memset(fbuf_x, 0, sizeof(fbuf_x));
    memset(fbuf_y, 0, sizeof(fbuf_y));
    memset(fbuf_z, 0, sizeof(fbuf_z));

    int fbuf_idx = 0;

    uint64_t next_sample_us = time_us_64() + SAMPLE_PERIOD_US;
    uint64_t report_samples = 0;
    uint64_t dropped_samples = 0;
    uint64_t last_report_us = time_us_64();
    bool     led_state = true;

    while (true) {
        const uint64_t now_us = time_us_64();
        if ((int64_t)(next_sample_us - now_us) > 0) {
            sleep_until(from_us_since_boot(next_sample_us));
        }

        // ── Read raw IMU sample ───────────────────────────────────────────────
        imu_sample_t sample = {0};
        if (!bmi160_read_sample(&sample)) {
            sample.timestamp_us = time_us_64();
            sample.valid = false;
            dropped_samples++;
        }
        ring_push(&ring, &sample);

        // ── High-pass filter into float buffers ───────────────────────────────
        if (sample.valid) {
            // ACC_RANGE is ±4g → sensitivity = 8192 LSB/g
            fbuf_x[fbuf_idx] = highpass(0, sample.ax / 8192.0f);
            fbuf_y[fbuf_idx] = highpass(1, sample.ay / 8192.0f);
            fbuf_z[fbuf_idx] = highpass(2, sample.az / 8192.0f);
        }
        fbuf_idx = (fbuf_idx + 1) % WINDOW_SIZE;

        report_samples++;

        // Timing compensation
        next_sample_us += SAMPLE_PERIOD_US;
        const uint64_t after_read_us = time_us_64();
        while ((int64_t)(next_sample_us - after_read_us) <= 0) {
            next_sample_us += SAMPLE_PERIOD_US;
        }

        // ── Every 1 second: process + send over radio ─────────────────────────
        const uint64_t since_report_us = after_read_us - last_report_us;
        if (since_report_us >= 1000000ULL) {
            const float effective_hz =
                (float)report_samples * 1000000.0f / (float)since_report_us;

            // Dominant axis by RMS
            float rx = compute_rms(fbuf_x, WINDOW_SIZE);
            float ry = compute_rms(fbuf_y, WINDOW_SIZE);
            float rz = compute_rms(fbuf_z, WINDOW_SIZE);

            uint8_t axis;
            float   mag;
            const float *dom_buf;
            if (rx >= ry && rx >= rz) { axis = 0; mag = rx; dom_buf = fbuf_x; }
            else if (ry >= rz)        { axis = 1; mag = ry; dom_buf = fbuf_y; }
            else                      { axis = 2; mag = rz; dom_buf = fbuf_z; }

            float raw_freq    = zero_crossing_freq(dom_buf, WINDOW_SIZE);
            float tremor_freq = smooth_freq(raw_freq);
            float f_motor     = k * tremor_freq;

            // Print to USB serial (for your Mac serial monitor)
            printf("rate~%.1fHz axis=%c mag=%.4fg freq=%.2fHz f_motor=%.2fHz drop=%llu\n",
                   effective_hz,
                   "xyz"[axis], mag, tremor_freq, f_motor,
                   (unsigned long long)dropped_samples);

            // Send over NRF24L01 as CSV string — matches teammate's string-based receiver
            // Format: "freq,magnitude,axis,f_motor\n" padded to 20 bytes with nulls
            radio_payload_t pkt;
            memset(pkt, 0, RADIO_PAYLOAD_SIZE);
            snprintf((char *)pkt, RADIO_PAYLOAD_SIZE, "%.2f,%.4f,%d,%.2f\n",
                     tremor_freq, mag, axis, f_motor);
            nrf_send(pkt);

            // Slow blink = healthy
            led_state = !led_state;
            gpio_put(LED_PIN, led_state ? 1 : 0);

            last_report_us = after_read_us;
            report_samples = 0;
        }
    }

    return 0;
}
