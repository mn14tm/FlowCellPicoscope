/******************************************************************************

LCD display code from:
http://www.dfrobot.com/wiki/index.php?title=Arduino_LCD_KeyPad_Shield_(SKU:_DFR0009)

Connections:
Analog 0     ->  Button (select, up, right, down and left)
Digital 4    ->  DB4
Digital 5    ->  DB5
Digital 6    ->  DB6
Digital 7    ->  DB7
Digital 8    ->  RS (Data or Signal Display Selection)
Digital 9    ->  Enable
Digital 10   ->  Backlit Control

SHT15 Ambient Temperature and Humidity logger code from:
https://github.com/sparkfun/SparkFun_ISL29125_Breakout_Arduino_Library

Connections:
GND  -> A2
Vcc  -> A3
DATA -> A4
SCK  -> A5

******************************************************************************/

// ------------------------- LIBRARIES

#include <LiquidCrystal.h>
#include <SHT1X.h>

// ------------------------- CONSTANTS

// LCD
#define btnRIGHT  0
#define btnUP     1
#define btnDOWN   2
#define btnLEFT   3
#define btnSELECT 4
#define btnNONE   5

// ------------------------- DEFINITIONS & INITIALISATIONS

// Room temperature and humidity
float tempC = 0;
float humidity = 0;

// SHT15

//delacre output pins for powering the sensor
int power = A3;
int gnd = A2;

// Create an instance of the SHT1X sensor
SHT1x sht15(A4, A5);  //Data, SCK

// LCD

LiquidCrystal lcd(8, 9, 4, 5, 6, 7);  // select the pins used on the LCD panel

// define some values used by the panel and buttons
int lcd_key     = 0;
int adc_key_in  = 0;

// ------------------------- SETUP

void setup() {

  // Open serial connection to report values to host
  Serial.begin(9600);
  
  /*
  Initialize SHT15 sensor
  */
  pinMode(power, OUTPUT);
  pinMode(gnd, OUTPUT);
  digitalWrite(power, HIGH);
  digitalWrite(gnd, LOW);

  /*
  Initialize LCD
  */
  
  // set up the LCD's number of columns and rows
  lcd.begin(16, 2);
  
  // Display temperature
  lcd.setCursor(0, 0);
  lcd.print("Temp:");
  lcd.setCursor(14, 0);
  lcd.print((char)223);
  lcd.setCursor(15, 0);
  lcd.print("C");

  // Display humidity
  lcd.setCursor(0, 1);
  lcd.print("Humid:");
  lcd.setCursor(15, 1);
  lcd.print("\%");
}


// ------------------------- MAIN LOOP

void loop() {
  
  // Take SHT15 reading
  readSensor();
  
  // Print results to serial and LCD
  serialPrintOut();
  lcdPrintOut();
  
  // pause loop
  delay(1000);
}

// ------------------------- HELPER FUNCTIONS

void readSensor() {
  // Read values from the SHT15 sensor
  tempC = sht15.readTemperatureC();
  humidity = sht15.readHumidity();  
}

void serialPrintOut() {
  Serial.print(" Temp = ");
  Serial.print(tempC);
  Serial.print("*C,");
  Serial.print(" Humidity = ");
  Serial.print(humidity); 
  Serial.println("%");
}

void lcdPrintOut() {
  // display seconds elapsed since power-up
//  float time = millis()/1000;
  
  lcd.setCursor(9, 0);
  lcd.print(tempC, 2);

  lcd.setCursor(9, 1);
  lcd.print(humidity, 2);
}
  
