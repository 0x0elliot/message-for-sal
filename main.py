# ESP32 Birthday Music Player - MicroPython
# Features:
# - Button plays/stops music
# - Randomly picks between two songs
# - OLED display shows "HBD Saloni <3" or fetched message
# - PWM buzzer for music playback
# - WiFi connectivity to fetch messages
# - XOR encryption for messages

from machine import Pin, PWM, I2C
import time
import random
import ssd1306
import network
import urequests
import binascii

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

# XOR encryption key (must match the Python encrypter key)
ENCRYPTION_KEY = "SaloniKey2025"  # Change this to match your Python encrypter

# Complete Happy Birthday Melody (in Hz) - Key of C
melody1 = [
    # "Happy birthday to you" (1st time)
    264, 264, 297, 264, 352, 330,
    # "Happy birthday to you" (2nd time) 
    264, 264, 297, 264, 396, 352,
    # "Happy birthday dear [Name]"
    264, 264, 528, 440, 352, 330, 297,
    # "Happy birthday to you" (final)
    466, 466, 440, 352, 396, 352,
    # Extended ending with flourish
    0, 352, 330, 297, 264, 0  # Rest, then descending notes, final rest
]

# Note durations in ms - more musical timing
durations1 = [
    # "Happy birthday to you" (1st)
    200, 200, 400, 400, 400, 800,
    # "Happy birthday to you" (2nd) 
    200, 200, 400, 400, 400, 800,
    # "Happy birthday dear [Name]"
    200, 200, 400, 400, 400, 400, 800,
    # "Happy birthday to you" (final)
    200, 200, 400, 400, 400, 800,
    # Extended ending
    200, 300, 300, 300, 600, 400
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
        self.last_wifi_check = 0
        self.wifi_check_interval = 10000  # 10 seconds in milliseconds
        self.wifi_connecting = False
        self.wifi_connect_start = 0
        self.wifi_connect_timeout = 5000  # 5 second timeout
        self.last_message_fetch = 0
        # self.message_fetch_interval = 600000  # 10 minutes in milliseconds
        self.message_fetch_interval = 5000
        
        print("ESP32 Birthday Player Ready!")
        self.display_message()  # Show default message first
    
    def setup_wifi(self):
        """Setup WiFi connection - completely non-blocking version"""
        if self.wifi_connecting:
            return  # Already trying to connect
        
        try:
            wlan = network.WLAN(network.STA_IF)
            wlan.active(True)
            
            print("Scanning for WiFi networks...")
            networks = wlan.scan()
            
            # Try to connect to known networks
            for ssid, bssid, channel, RSSI, authmode, hidden in networks:
                ssid_str = ssid.decode('utf-8')
                
                if ssid_str in WIFI_NETWORKS:
                    password = WIFI_NETWORKS[ssid_str]
                    print(f"Attempting to connect to {ssid_str}...")
                    
                    if password:
                        wlan.connect(ssid_str, password)
                    else:
                        wlan.connect(ssid_str)
                    
                    # Start non-blocking connection
                    self.wifi_connecting = True
                    self.wifi_connect_start = time.ticks_ms()
                    break
            
            # Clean up
            del networks  # Free memory
            
        except Exception as e:
            print(f"WiFi setup error: {e}")
            self.wifi_connecting = False
    
    def check_wifi_connection(self):
        """Check WiFi connection status without blocking"""
        if not self.wifi_connecting:
            return
        
        wlan = network.WLAN(network.STA_IF)
        
        if wlan.isconnected():
            self.wifi_connected = True
            self.wifi_connecting = False
            print("Connected to WiFi!")
            self.fetch_message()
        elif time.ticks_diff(time.ticks_ms(), self.wifi_connect_start) >= self.wifi_connect_timeout:
            # Timeout - stop trying
            self.wifi_connecting = False
            print("WiFi connection timeout - will retry in 10 seconds")
    
    def xor_decrypt(self, hex_string):
        """XOR decrypt a hex string to readable text - matches Python encrypter"""
        try:
            # Remove any whitespace
            hex_string = hex_string.strip().replace('\n', '').replace('\r', '')
            
            # Convert hex to bytes
            encrypted_bytes = binascii.unhexlify(hex_string)
            
            # XOR decrypt using the key
            decrypted = ""
            key_len = len(ENCRYPTION_KEY)
            
            for i, byte in enumerate(encrypted_bytes):
                key_char = ENCRYPTION_KEY[i % key_len]
                decrypted_char = chr(byte ^ ord(key_char))
                decrypted += decrypted_char
            
            return decrypted
            
        except Exception as e:
            print(f"XOR decryption error: {e}")
            return None
    
    def fetch_message(self):
        """Fetch and decrypt message from GitHub - memory efficient version"""
        if not self.wifi_connected:
            return
        
        try:
            print("Fetching message from GitHub...")
            response = urequests.get(MESSAGE_URL)
            
            if response.status_code == 200:
                encrypted_hex = response.text.strip()
                print("Fetched encrypted message")
                
                # Try to decrypt the message using XOR
                message_text = self.xor_decrypt(encrypted_hex)
                
                if message_text:
                    print(f"Decrypted message: {message_text}")
                    
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
                    
                    # Update display with new message
                    self.display_message()
                    
                    # Update fetch timestamp
                    self.last_message_fetch = time.ticks_ms()
                else:
                    print("Failed to decrypt message - using default")
            else:
                print(f"HTTP error: {response.status_code}")
            
            response.close()
            del response  # Free memory
            
        except Exception as e:
            print(f"Error fetching message: {e}")
    
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
        """Stop buzzer simply and reliably"""
        try:
            self.buzzer.duty(0)
        except Exception as e:
            print(f"Error stopping buzzer: {e}")
    
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
        # Make sure buzzer is stopped before starting
        self.stop_tone()
        self.current_song = random.randint(0, 1)
        self.playing = True
        self.note_index = 0
        self.last_note_time = time.ticks_ms()
        print(f"Playing song {self.current_song + 1}!")
    
    def stop_song(self):
        """Stop the current song"""
        self.playing = False
        self.stop_tone()  # Ensure buzzer stops
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
        
        # Bounds check to prevent index errors
        if self.note_index >= len(current_melody) or self.note_index >= len(current_durations):
            # Song finished - stop everything
            self.playing = False
            self.stop_tone()
            print("Song finished!")
            return
        
        # Check if it's time for the next note
        if time.ticks_diff(now, self.last_note_time) >= current_durations[self.note_index]:
            # Play current note
            self.play_tone(current_melody[self.note_index])
            self.note_index += 1
            self.last_note_time = now
            
            # Check if we've reached the end
            if self.note_index >= len(current_melody):
                # Song finished
                self.playing = False
                self.stop_tone()
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
            current_time = time.ticks_ms()
            
            # Check if it's time to retry WiFi connection (but not while playing music)
            if (not self.wifi_connected and 
                not self.wifi_connecting and 
                not self.playing and  # Don't scan WiFi while music is playing
                time.ticks_diff(current_time, self.last_wifi_check) >= self.wifi_check_interval):
                self.last_wifi_check = current_time
                self.setup_wifi()
            
            # Check if it's time to fetch new message (every 10 minutes when connected and not playing)
            if (self.wifi_connected and 
                not self.playing and
                time.ticks_diff(current_time, self.last_message_fetch) >= self.message_fetch_interval):
                print("Fetching updated message...")
                self.fetch_message()
            
            # Check WiFi connection status (non-blocking)
            if self.wifi_connecting:
                self.check_wifi_connection()
            
            # Always check button and update music - never block these!
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
