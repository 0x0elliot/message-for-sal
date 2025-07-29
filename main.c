/*
 * Simple ESP32 Music Player - No WiFi, Just Music and Simple Display
 * - Button plays/stops music
 * - Randomly picks between two songs
 * - Display shows "HBD Saloni <3" 
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "driver/gpio.h"
#include "driver/ledc.h"
#include "driver/i2c.h"
#include "esp_random.h"

#define BUTTON_PIN GPIO_NUM_2
#define BUZZER_PIN GPIO_NUM_18
#define I2C_SDA_PIN GPIO_NUM_21
#define I2C_SCL_PIN GPIO_NUM_22
#define OLED_ADDRESS 0x3C

// Happy Birthday Melody (in Hz)
int melody1[] = {
    264, 264, 297, 264, 352, 330,     // Happy birthday to you
    264, 264, 297, 264, 396, 352,     // Happy birthday to you
    264, 264, 528, 440, 352, 330, 297,// Happy birthday dear
    466, 466, 440, 352, 396, 352      // Happy birthday to you
};

// Note durations in ms
int durations1[] = {
    250, 250, 500, 500, 500, 1000,
    250, 250, 500, 500, 500, 1000,
    250, 250, 500, 500, 500, 500, 1000,
    250, 250, 500, 500, 500, 1000
};

int melody2[] = {
    261, 293, 293, 261, 246, 164, 220, 246,
    246, 220, 195, 195, 184, 195, 195, 195,
    184, 184, 184, 195, 220, 261, 293, 293,
    261, 246, 164, 220, 246, 246, 220, 195,
    195, 184, 195, 195, 195, 184, 184, 184,
    195, 220, 220, 246, 293, 369, 369, 329,
    329, 329, 329, 329, 293, 329, 293, 246,
    220, 293, 246, 220, 195, 184, 164, 261,
    293, 293, 261, 246, 164, 220, 246, 246,
    220, 195, 195, 184, 195, 195, 195, 184,
    184, 184, 195, 220, 261, 293, 293, 261,
    246, 164, 220, 246, 246, 220, 195, 195,
    184, 195, 195, 195, 184, 184, 184, 195,
    220, 220, 246, 293, 369, 369, 329, 329,
    329, 329, 329, 293, 329, 293, 246, 220,
    293, 246, 220, 195, 184, 164, 164, 246,
    246, 246, 220, 195, 164, 329, 329, 329,
    329, 329, 293, 261, 246, 293, 293, 293,
    293, 293, 261, 246, 220, 220, 220, 220,
    220, 220, 220, 293, 246, 246, 246, 246,
    246, 220, 220, 195, 164, 164, 329, 329,
    329, 329, 329, 293, 261, 246, 293, 293,
    293, 293, 293, 261, 246, 220, 220, 220,
    220, 220, 195, 184, 195, 164, 261, 293,
    293, 261, 246, 164, 220, 246, 246, 220,
    195, 195, 184, 195, 195, 195, 184, 184,
    184, 195, 220, 261, 293, 293, 261, 246,
    164, 220, 246, 246, 220, 195, 195, 184,
    195, 195, 195, 184, 184, 184, 195, 220,
    220, 246, 293, 369, 369, 329, 329, 329,
    329, 329, 293, 329, 293, 246, 220, 293,
    246, 220, 195, 184, 164
};

int durations2[] = {
    166, 361, 542, 361, 361, 361, 166, 361,
    535, 361, 361, 361, 166, 339, 512, 339,
    339, 339, 339, 346, 685, 166, 361, 542,
    361, 361, 361, 166, 361, 535, 361, 361,
    361, 166, 339, 512, 339, 339, 361, 339,
    361, 670, 339, 1024, 361, 361, 361, 693,
    166, 361, 700, 361, 723, 339, 361, 166,
    813, 1047, 1084, 339, 339, 700, 685, 166,
    361, 542, 361, 361, 361, 166, 361, 535,
    361, 361, 361, 166, 339, 512, 339, 339,
    339, 339, 346, 685, 166, 361, 542, 361,
    361, 361, 166, 361, 535, 361, 361, 361,
    166, 339, 512, 339, 339, 361, 339, 361,
    670, 339, 1024, 361, 361, 361, 693, 166,
    361, 700, 361, 723, 339, 361, 166, 813,
    1047, 1084, 339, 339, 700, 685, 723, 331,
    723, 331, 723, 331, 361, 331, 685, 339,
    723, 331, 339, 723, 685, 331, 685, 361,
    723, 331, 339, 723, 670, 339, 685, 339,
    678, 361, 723, 331, 685, 361, 670, 339,
    723, 331, 723, 339, 181, 361, 331, 685,
    339, 723, 331, 339, 723, 685, 331, 685,
    361, 723, 331, 339, 723, 670, 339, 685,
    339, 339, 346, 670, 1024, 1024, 166, 361,
    542, 361, 361, 361, 166, 361, 535, 361,
    361, 361, 166, 339, 512, 339, 339, 339,
    339, 346, 685, 166, 361, 542, 361, 361,
    361, 166, 361, 535, 361, 361, 361, 166,
    339, 512, 339, 339, 361, 339, 361, 670,
    339, 1024, 361, 361, 361, 693, 166, 361,
    700, 361, 723, 339, 361, 166, 813, 1047,
    1084, 339, 339, 700, 685
};

#define MELODY1_LENGTH (sizeof(melody1) / sizeof(melody1[0]))
#define MELODY2_LENGTH (sizeof(melody2) / sizeof(melody2[0]))

// Global variables
bool playing = false;
int note_index = 0;
uint32_t last_note_time = 0;
int current_song = 0; // 0 = melody1, 1 = melody2

static const char *TAG = "PLAYER";

void setup_hardware() {
    // Button
    gpio_config_t btn_config = {
        .pin_bit_mask = (1ULL << BUTTON_PIN),
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_ENABLE,
    };
    gpio_config(&btn_config);
    
    // Buzzer
    ledc_timer_config_t timer_config = {
        .duty_resolution = LEDC_TIMER_13_BIT,
        .freq_hz = 440,
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .timer_num = LEDC_TIMER_0,
    };
    ledc_timer_config(&timer_config);
    
    ledc_channel_config_t channel_config = {
        .channel = LEDC_CHANNEL_0,
        .duty = 0,
        .gpio_num = BUZZER_PIN,
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .timer_sel = LEDC_TIMER_0,
    };
    ledc_channel_config(&channel_config);
    
    // I2C for display
    i2c_config_t i2c_config = {
        .mode = I2C_MODE_MASTER,
        .sda_io_num = I2C_SDA_PIN,
        .scl_io_num = I2C_SCL_PIN,
        .sda_pullup_en = GPIO_PULLUP_ENABLE,
        .scl_pullup_en = GPIO_PULLUP_ENABLE,
        .master.clk_speed = 100000,
    };
    i2c_param_config(I2C_NUM_0, &i2c_config);
    i2c_driver_install(I2C_NUM_0, I2C_MODE_MASTER, 0, 0, 0);
}

void init_oled() {
    // Initialize OLED display
    uint8_t init_cmds[] = {
        0x00,       // Command mode
        0xAE,       // Display off
        0xD5, 0x80, // Set display clock
        0xA8, 0x3F, // Set multiplex ratio
        0xD3, 0x00, // Set display offset
        0x40,       // Set start line
        0x8D, 0x14, // Enable charge pump
        0x20, 0x00, // Set memory addressing mode
        0xA1,       // Set segment remap
        0xC8,       // Set COM output scan direction
        0xDA, 0x12, // Set COM pins
        0x81, 0xCF, // Set contrast
        0xD9, 0xF1, // Set precharge
        0xDB, 0x40, // Set VCOMH
        0xA4,       // Display resume
        0xA6,       // Set normal display
        0xAF        // Display on
    };
    
    i2c_cmd_handle_t cmd = i2c_cmd_link_create();
    i2c_master_start(cmd);
    i2c_master_write_byte(cmd, (OLED_ADDRESS << 1) | I2C_MASTER_WRITE, true);
    i2c_master_write(cmd, init_cmds, sizeof(init_cmds), true);
    i2c_master_stop(cmd);
    esp_err_t ret = i2c_master_cmd_begin(I2C_NUM_0, cmd, 1000 / portTICK_PERIOD_MS);
    i2c_cmd_link_delete(cmd);
    
    ESP_LOGI(TAG, "OLED init: %s", ret == ESP_OK ? "OK" : "FAILED");
}

void clear_oled() {
    // Clear all pages
    for (int page = 0; page < 8; page++) {
        // Set page
        uint8_t page_cmd[] = {0x00, 0xB0 + page, 0x00, 0x10};
        i2c_cmd_handle_t cmd = i2c_cmd_link_create();
        i2c_master_start(cmd);
        i2c_master_write_byte(cmd, (OLED_ADDRESS << 1) | I2C_MASTER_WRITE, true);
        i2c_master_write(cmd, page_cmd, sizeof(page_cmd), true);
        i2c_master_stop(cmd);
        i2c_master_cmd_begin(I2C_NUM_0, cmd, 1000 / portTICK_PERIOD_MS);
        i2c_cmd_link_delete(cmd);
        
        // Send zeros
        uint8_t zeros[128] = {0};
        cmd = i2c_cmd_link_create();
        i2c_master_start(cmd);
        i2c_master_write_byte(cmd, (OLED_ADDRESS << 1) | I2C_MASTER_WRITE, true);
        i2c_master_write_byte(cmd, 0x40, true); // Data mode
        i2c_master_write(cmd, zeros, 128, true);
        i2c_master_stop(cmd);
        i2c_master_cmd_begin(I2C_NUM_0, cmd, 1000 / portTICK_PERIOD_MS);
        i2c_cmd_link_delete(cmd);
    }
}

void display_message() {
    clear_oled();
    
    // Create simple patterns for "HBD Saloni" with a heart
    
    // Page 2 - Letters
    uint8_t line1[] = {
        // H
        0xFF, 0x08, 0x08, 0xFF, 0x00,
        // B  
        0xFF, 0x89, 0x89, 0x76, 0x00,
        // D
        0xFF, 0x81, 0x81, 0x7E, 0x00, 0x00,
        
        // S
        0x46, 0x89, 0x89, 0x71, 0x00,
        // a
        0x20, 0x54, 0x54, 0x78, 0x00,
        // l
        0xFF, 0x00,
        // o
        0x38, 0x44, 0x44, 0x38, 0x00,
        // n
        0x7C, 0x08, 0x04, 0x78, 0x00,
        // i
        0x7D, 0x00, 0x00,
        
        // Bigger heart pattern
        0x00, 0x66, 0xFF, 0x7E, 0x3C, 0x18, 0x00
    };
    
    // Set page 2
    uint8_t page_cmd[] = {0x00, 0xB2, 0x00, 0x10};
    i2c_cmd_handle_t cmd = i2c_cmd_link_create();
    i2c_master_start(cmd);
    i2c_master_write_byte(cmd, (OLED_ADDRESS << 1) | I2C_MASTER_WRITE, true);
    i2c_master_write(cmd, page_cmd, sizeof(page_cmd), true);
    i2c_master_stop(cmd);
    i2c_master_cmd_begin(I2C_NUM_0, cmd, 1000 / portTICK_PERIOD_MS);
    i2c_cmd_link_delete(cmd);
    
    // Send the pattern
    cmd = i2c_cmd_link_create();
    i2c_master_start(cmd);
    i2c_master_write_byte(cmd, (OLED_ADDRESS << 1) | I2C_MASTER_WRITE, true);
    i2c_master_write_byte(cmd, 0x40, true); // Data mode
    i2c_master_write(cmd, line1, sizeof(line1), true);
    i2c_master_stop(cmd);
    i2c_master_cmd_begin(I2C_NUM_0, cmd, 1000 / portTICK_PERIOD_MS);
    i2c_cmd_link_delete(cmd);
    
    ESP_LOGI(TAG, "Message displayed");
}

void stop_tone() {
    ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0, 0);
    ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0);
}

void play_tone(int freq) {
    if (freq == 0) {
        // Silence/rest - turn off the buzzer
        stop_tone();
    } else {
        // Play the frequency
        ledc_set_freq(LEDC_LOW_SPEED_MODE, LEDC_TIMER_0, freq);
        ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0, 2048);
        ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0);
    }
}

void start_song() {
    // Randomly pick a song (0 or 1)
    current_song = esp_random() % 2;
    
    playing = true;
    note_index = 0;
    last_note_time = xTaskGetTickCount() * portTICK_PERIOD_MS;
    
    ESP_LOGI(TAG, "Playing song %d!", current_song + 1);
}

void stop_song() {
    playing = false;
    stop_tone();
    ESP_LOGI(TAG, "Song stopped!");
}

void update_song() {
    if (!playing) return;
    
    uint32_t now = xTaskGetTickCount() * portTICK_PERIOD_MS;
    
    // Get current melody and durations based on selected song
    int *current_melody = (current_song == 0) ? melody1 : melody2;
    int *current_durations = (current_song == 0) ? durations1 : durations2;
    int melody_length = (current_song == 0) ? MELODY1_LENGTH : MELODY2_LENGTH;
    
    if (now - last_note_time >= current_durations[note_index]) {
        if (note_index < melody_length) {
            play_tone(current_melody[note_index]);
            note_index++;
            last_note_time = now;
        } else {
            stop_tone();
            playing = false;
            ESP_LOGI(TAG, "Song finished!");
        }
    }
}

void app_main() {
    // Initialize
    nvs_flash_init();
    setup_hardware();
    init_oled();
    
    ESP_LOGI(TAG, "ESP32 Birthday Player Ready!");
    display_message();
    
    bool last_button = true;
    
    while (1) {
        // Check button
        bool button = gpio_get_level(BUTTON_PIN);
        if (last_button && !button) { // Button pressed (falling edge)
            if (playing) {
                stop_song(); // Stop if currently playing
            } else {
                start_song(); // Start if not playing
            }
        }
        last_button = button;
        
        // Update music
        update_song();
        
        vTaskDelay(50 / portTICK_PERIOD_MS);
    }
}
