# ESP32 Birthday Music Player - MicroPython
# Features:
# - Button plays/stops music
# - Randomly picks between two songs
# - OLED display shows "HBD Saloni <3"
# - PWM buzzer for music playback

from machine import Pin, PWM, I2C
import time
import random
import ssd1306

# Pin definitions
BUTTON_PIN = 2
BUZZER_PIN = 18
I2C_SDA_PIN = 21
I2C_SCL_PIN = 22
OLED_ADDRESS = 0x3C

# Happy Birthday Melody (in Hz)
melody1 = [
    264, 264, 297, 264, 352, 330,     # Happy birthday to you
    264, 264, 297, 264, 396, 352,     # Happy birthday to you
    264, 264, 528, 440, 352, 330, 297,# Happy birthday dear
    466, 466, 440, 352, 396, 352      # Happy birthday to you
]

# Note durations in ms
durations1 = [
    250, 250, 500, 500, 500, 1000,
    250, 250, 500, 500, 500, 1000,
    250, 250, 500, 500, 500, 500, 1000,
    250, 250, 500, 500, 500, 1000
]

# Longer melody (simplified version for demo)
melody2 = [
    261, 293, 293, 261, 246, 164, 220, 246,
    246, 220, 195, 195, 184, 195, 195, 195,
    184, 184, 184, 195, 220, 261, 293, 293,
    261, 246, 164, 220, 246, 246, 220, 195,
    195, 184, 195, 195, 195, 184, 184, 184,
    195, 220, 220, 246, 293, 369, 369, 329,
    329, 329, 329, 329, 293, 329, 293, 246,
    220, 293, 246, 220, 195, 184, 164, 261
]

durations2 = [
    166, 361, 542, 361, 361, 361, 166, 361,
    535, 361, 361, 361, 166, 339, 512, 339,
    339, 339, 339, 346, 685, 166, 361, 542,
    361, 361, 361, 166, 361, 535, 361, 361,
    361, 166, 339, 512, 339, 339, 361, 339,
    361, 670, 339, 1024, 361, 361, 361, 693,
    166, 361, 700, 361, 723, 339, 361, 166,
    813, 1047, 1084, 339, 339, 700, 685, 166
]

class MusicPlayer:
    def __init__(self):
        # Hardware setup
        self.button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
        self.buzzer = PWM(Pin(BUZZER_PIN), freq=440, duty=0)  # Initialize with freq and duty=0
        
        # I2C and OLED setup
        self.i2c = I2C(0, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=100000)
        self.oled = ssd1306.SSD1306_I2C(128, 64, self.i2c, addr=OLED_ADDRESS)
        
        # Music state
        self.playing = False
        self.note_index = 0
        self.last_note_time = 0
        self.current_song = 0
        self.last_button = True
        
        print("ESP32 Birthday Player Ready!")
        self.display_message()
    
    def display_message(self):
        """Display birthday message on OLED"""
        self.oled.fill(0)  # Clear display
        
        # Center the text
        self.oled.text("HBD Saloni", 25, 20)
        self.oled.text("   <3", 45, 35)
        
        self.oled.show()
        print("Message displayed")
    
    def stop_tone(self):
        """Stop buzzer"""
        self.buzzer.duty(0)
    
    def play_tone(self, freq):
        """Play frequency on buzzer"""
        if freq == 0:
            # Silence/rest
            self.stop_tone()
        else:
            # Ensure frequency is within valid range (20Hz - 20kHz)
            if freq < 20:
                freq = 20
            elif freq > 20000:
                freq = 20000
            
            try:
                self.buzzer.freq(freq)
                self.buzzer.duty(256)  # Reduced duty cycle (25%) for cleaner sound
            except Exception as e:
                print(f"Error setting frequency {freq}: {e}")
                self.stop_tone()
    
    def start_song(self):
        """Start playing a randomly selected song"""
        self.current_song = random.randint(0, 1)
        self.playing = True
        self.note_index = 0
        self.last_note_time = time.ticks_ms()
        print(f"Playing song {self.current_song + 1}!")
    
    def stop_song(self):
        """Stop the current song"""
        self.playing = False
        self.stop_tone()
        print("Song stopped!")
    
    def update_song(self):
        """Update music playback"""
        if not self.playing:
            return
        
        now = time.ticks_ms()
        
        # Get current melody and durations
        if self.current_song == 0:
            current_melody = melody1
            current_durations = durations1
        else:
            current_melody = melody2
            current_durations = durations2
        
        # Check if it's time for the next note
        if time.ticks_diff(now, self.last_note_time) >= current_durations[self.note_index]:
            if self.note_index < len(current_melody):
                self.play_tone(current_melody[self.note_index])
                self.note_index += 1
                self.last_note_time = now
            else:
                # Song finished
                self.stop_tone()
                self.playing = False
                print("Song finished!")
    
    def check_button(self):
        """Check for button press"""
        button = self.button.value()
        
        # Detect button press (falling edge)
        if self.last_button and not button:
            if self.playing:
                self.stop_song()
            else:
                self.start_song()
        
        self.last_button = button
    
    def run(self):
        """Main application loop"""
        while True:
            self.check_button()
            self.update_song()
            time.sleep_ms(50)

# Run the music player
def main():
    try:
        player = MusicPlayer()
        player.run()
    except KeyboardInterrupt:
        print("Stopping music player...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
