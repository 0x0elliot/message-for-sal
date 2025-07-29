# ESP32 Birthday Music Player - MicroPython
# Features:
# - Button plays/stops music
# - Randomly picks between two songs
# - OLED display shows "HBD Saloni <3" or fetched message
# - PWM buzzer for music playback
# - WiFi connectivity to fetch messages

from machine import Pin, PWM, I2C
import time
import random
import ssd1306
import network
import urequests

# Pin definitions
BUTTON_PIN = 2
BUZZER_PIN = 18
I2C_SDA_PIN = 21
I2C_SCL_PIN = 22
OLED_ADDRESS = 0x3C

# WiFi credentials dictionary (Wokwi defaults)
WIFI_NETWORKS = {
    "Wokwi-GUEST": "",  # Wokwi's default open network
    "IoTNetwork": "ThingsNetwork",  # Common Wokwi test network
    "ESP32-Access-Point": "123456789"  # Another common test network
}

# GitHub raw URL for the message
MESSAGE_URL = "https://raw.githubusercontent.com/0x0elliot/message-for-sal/main/message.txt"

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
        self.buzzer = PWM(Pin(BUZZER_PIN), freq=440, duty=0)
        
        # I2C and OLED setup
        self.i2c = I2C(0, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=100000)
        self.oled = ssd1306.SSD1306_I2C(128, 64, self.i2c, addr=OLED_ADDRESS)
        
        # Music state
        self.playing = False
        self.note_index = 0
        self.last_note_time = 0
        self.current_song = 0
        self.last_button = True
        
        # Message state
        self.message_lines = ["HBD Saloni", "   <3"]
        self.wifi_connected = False
        
        print("ESP32 Birthday Player Ready!")
        self.setup_wifi()
        self.display_message()
    
    def setup_wifi(self):
        """Setup WiFi connection"""
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        
        print("Scanning for WiFi networks...")
        networks = wlan.scan()
        
        # Try to connect to known networks
        for ssid, bssid, channel, RSSI, authmode, hidden in networks:
            ssid_str = ssid.decode('utf-8')
            print(f"Found network: {ssid_str}")
            
            if ssid_str in WIFI_NETWORKS:
                password = WIFI_NETWORKS[ssid_str]
                print(f"Attempting to connect to {ssid_str}...")
                
                if password:
                    wlan.connect(ssid_str, password)
                else:
                    wlan.connect(ssid_str)
                
                # Wait for connection
                for _ in range(20):  # 10 second timeout
                    if wlan.isconnected():
                        self.wifi_connected = True
                        print(f"Connected to {ssid_str}!")
                        print(f"IP address: {wlan.ifconfig()[0]}")
                        self.fetch_message()
                        return
                    time.sleep(0.5)
                
                print(f"Failed to connect to {ssid_str}")
        
        print("No suitable WiFi networks found or connection failed")
        print("Using default message")
    
    def fetch_message(self):
        """Fetch message from GitHub"""
        if not self.wifi_connected:
            return
        
        try:
            print("Fetching message from GitHub...")
            response = urequests.get(MESSAGE_URL)
            
            if response.status_code == 200:
                message_text = response.text.strip()
                print(f"Fetched message: {message_text}")
                
                # Split message into lines for display (max 21 chars per line for OLED)
                lines = []
                words = message_text.split()
                current_line = ""
                
                for word in words:
                    if len(current_line + " " + word) <= 21:  # OLED character limit
                        if current_line:
                            current_line += " " + word
                        else:
                            current_line = word
                    else:
                        if current_line:
                            lines.append(current_line)
                        current_line = word
                
                if current_line:
                    lines.append(current_line)
                
                # Limit to 4 lines (OLED height limitation)
                self.message_lines = lines[:4] if lines else ["HBD Saloni", "   <3"]
                print(f"Message lines: {self.message_lines}")
            else:
                print(f"HTTP error: {response.status_code}")
            
            response.close()
            
        except Exception as e:
            print(f"Error fetching message: {e}")
            print("Using default message")
    
    def display_message(self):
        """Display birthday message on OLED"""
        self.oled.fill(0)  # Clear display
        
        # Display message lines (centered)
        start_y = 10 if len(self.message_lines) <= 2 else 5
        for i, line in enumerate(self.message_lines):
            # Center text horizontally
            x_pos = max(0, (128 - len(line) * 8) // 2)  # 8 pixels per character
            y_pos = start_y + (i * 12)  # 12 pixels between lines
            
            if y_pos < 55:  # Make sure we don't go off screen
                self.oled.text(line, x_pos, y_pos)
        
        # Show WiFi status
        if self.wifi_connected:
            self.oled.text("WiFi: ON", 0, 56)
        else:
            self.oled.text("WiFi: OFF", 0, 56)
        
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
