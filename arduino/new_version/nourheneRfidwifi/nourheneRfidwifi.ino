#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <SPI.h>
#include <MFRC522.h>
#include <ESP32Servo.h>
#include <WiFi.h>
#include <HTTPClient.h>

// Network credentials
const char* ssid = "iheb";     // Replace with your WiFi SSID
const char* password = ""; // Replace with your WiFi password

// Server address (PC's IP address where PyQt server is running)
const char* serverUrl = "http://192.168.100.201:3000/verify"; // Replace with your PC's IP

// Pin definitions
#define SS_PIN    5    // SDA pin of RC522 connected to GPIO5
#define RST_PIN   27   // RST pin of RC522 connected to GPIO27
#define SERVO_PIN 13   // Servo control pin
#define GREEN_LED 2    // Green LED pin
#define RED_LED   4    // Red LED pin

// Initialize LCD (address 0x27, 16 columns, 2 rows)
LiquidCrystal_I2C lcd(0x27, 16, 2);

// Initialize RFID reader
MFRC522 rfid(SS_PIN, RST_PIN);

// Initialize servo
Servo doorServo;

// Variables
bool doorOpen = false;
unsigned long doorOpenTime = 0;
const unsigned long autoCloseDelay = 4000; // 4 seconds in milliseconds
unsigned long lastCardReadTime = 0;
const unsigned long cardReadCooldown = 2000; // 2 second cooldown between reads

void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  
  // Initialize LCD
  Wire.begin(21, 22);  // SDA=GPIO21, SCL=GPIO22
  lcd.init();
  lcd.backlight();
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("System Starting");
  
  // Initialize SPI bus for RFID
  SPI.begin(); // This initializes the SPI bus using default SPI pins (18,19,23)
  
  // Initialize RFID reader
  rfid.PCD_Init();
  Serial.println("RFID Reader initialized");
  
  // Check RFID reader version
  byte version = rfid.PCD_ReadRegister(rfid.VersionReg);
  Serial.print("RFID Reader Version: 0x");
  Serial.println(version, HEX);
  
  if (version == 0x91 || version == 0x92) {
    Serial.println("RFID Reader detected successfully");
    lcd.setCursor(0, 1);
    lcd.print("RFID Ready");
  } else {
    Serial.println("Warning: RFID Reader may not be connected correctly");
    lcd.setCursor(0, 1);
    lcd.print("RFID Error!");
    delay(2000);
  }
  
  // Initialize servo
  doorServo.attach(SERVO_PIN);
  doorServo.write(0);  // Set initial position to closed
  Serial.println("Servo initialized");
  
  // Initialize LEDs
  pinMode(GREEN_LED, OUTPUT);
  pinMode(RED_LED, OUTPUT);
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(RED_LED, LOW);
  Serial.println("LEDs initialized");
  
  // Connect to Wi-Fi
  connectToWiFi();
  
  // Ready state
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Access Control");
  lcd.setCursor(0, 1);
  lcd.print("Scan RFID Card");
  
  Serial.println("System Ready");
}

void loop() {
  // Check if door needs to be auto-closed
  if (doorOpen && (millis() - doorOpenTime >= autoCloseDelay)) {
    closeDoor();
  }
  
  // Check WiFi connection and reconnect if needed
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi connection lost. Reconnecting...");
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("WiFi Disconnected");
    lcd.setCursor(0, 1);
    lcd.print("Reconnecting...");
    
    connectToWiFi();
    
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Access Control");
    lcd.setCursor(0, 1);
    lcd.print("Scan RFID Card");
  }
  
  // Check for new card only if we're not in cooldown period
  if (millis() - lastCardReadTime >= cardReadCooldown) {
    // Check if new card is present
    if (rfid.PICC_IsNewCardPresent()) {
      // Try to read the card
      if (rfid.PICC_ReadCardSerial()) {
        lastCardReadTime = millis(); // Start cooldown timer
        
        // Get UID as string
        String cardUID = "";
        for (byte i = 0; i < rfid.uid.size; i++) {
          cardUID.concat(String(rfid.uid.uidByte[i] < 0x10 ? "0" : ""));
          cardUID.concat(String(rfid.uid.uidByte[i], HEX));
        }
        cardUID.toUpperCase();
        
        // Print to serial monitor
        Serial.print("Card UID: ");
        Serial.println(cardUID);
        
        // Display on LCD
        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("Card Detected!");
        lcd.setCursor(0, 1);
        lcd.print("Verifying...");
        
        // Verify card against database
        bool authorized = verifyCardWithServer(cardUID);
        
        if (authorized) {
          accessGranted();
        } else {
          accessDenied();
        }
        
        // Halt PICC and stop encryption
        rfid.PICC_HaltA();
        rfid.PCD_StopCrypto1();
      }
    }
  }
}

void connectToWiFi() {
  Serial.println("Connecting to WiFi...");
  
  // Start WiFi connection
  WiFi.begin(ssid, password);
  
  // Wait for connection with timeout
  int attempts = 0;
  int maxAttempts = 20;
  
  while (WiFi.status() != WL_CONNECTED && attempts < maxAttempts) {
    delay(500);
    Serial.print(".");
    attempts++;
    
    // Flash red LED while connecting
    digitalWrite(RED_LED, !digitalRead(RED_LED));
  }
  
  // Turn off red LED after connection attempt
  digitalWrite(RED_LED, LOW);
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("");
    Serial.print("Connected to WiFi. IP: ");
    Serial.println(WiFi.localIP());
    
    // Flash green LED when connected
    for (int i = 0; i < 3; i++) {
      digitalWrite(GREEN_LED, HIGH);
      delay(200);
      digitalWrite(GREEN_LED, LOW);
      delay(200);
    }
  } else {
    Serial.println("");
    Serial.println("Failed to connect to WiFi. Operating in offline mode.");
    
    // Flash red LED to indicate failure
    for (int i = 0; i < 5; i++) {
      digitalWrite(RED_LED, HIGH);
      delay(100);
      digitalWrite(RED_LED, LOW);
      delay(100);
    }
  }
}

bool verifyCardWithServer(String cardUID) {
  // Default to unauthorized if not connected to WiFi
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected. Cannot verify card.");
    return false;
  }
  
  HTTPClient http;
  bool authorized = false;
  
  // Construct the full URL with the RFID parameter
  String url = String(serverUrl) + "?rfid=" + cardUID;
  
  Serial.print("Sending request to: ");
  Serial.println(url);
  
  // Begin HTTP connection
  http.begin(url);
  
  // Set timeout
  http.setTimeout(5000); // 5 second timeout
  
  // Send HTTP GET request
  int httpResponseCode = http.GET();
  
  if (httpResponseCode > 0) {
    Serial.print("HTTP Response code: ");
    Serial.println(httpResponseCode);
    String payload = http.getString();
    Serial.print("Response: ");
    Serial.println(payload);
    
    // Check if server response indicates authorization
    if (payload == "authorized") {
      authorized = true;
    }
  }
  else {
    Serial.print("Error code: ");
    Serial.println(httpResponseCode);
    Serial.println("Server connection failed");
  }
  
  // Free resources
  http.end();
  
  return authorized;
}

void accessGranted() {
  Serial.println("Access granted");
  
  // Update LCD
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Access Granted");
  lcd.setCursor(0, 1);
  lcd.print("Door Opening");
  
  // Turn on green LED
  digitalWrite(GREEN_LED, HIGH);
  digitalWrite(RED_LED, LOW);
  
  // Open door
  doorServo.write(90);
  doorOpen = true;
  doorOpenTime = millis(); // Start the timer for auto-close
}

void accessDenied() {
  Serial.println("Access denied");
  
  // Update LCD
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Access Denied");
  lcd.setCursor(0, 1);
  lcd.print("Unauthorized");
  
  // Flash red LED
  digitalWrite(GREEN_LED, LOW);
  for (int i = 0; i < 3; i++) {
    digitalWrite(RED_LED, HIGH);
    delay(200);
    digitalWrite(RED_LED, LOW);
    delay(200);
  }
  
  // Wait a moment before resetting
  delay(1000);
  
  // Reset display
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Access Control");
  lcd.setCursor(0, 1);
  lcd.print("Scan RFID Card");
}

void closeDoor() {
  Serial.println("Door auto-closing");
  
  // Turn off green LED
  digitalWrite(GREEN_LED, LOW);
  
  // Close door
  doorServo.write(0);
  doorOpen = false;
  
  // Update LCD
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Door Closed");
  delay(1000);
  
  // Reset display
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Access Control");
  lcd.setCursor(0, 1);
  lcd.print("Scan RFID Card");
}
