/******************************************************************************
SHT15 and 2 K thermocouple sensors connected.

Get the temperature in C and humidity.
Get the liquid in and out temperature in C.

SHT15 Connections:
GND  -> A2
Vcc  -> A3
DATA -> A4
SCK  -> A5
******************************************************************************/
#include <SHT1X.h>

/* -- SHT1x -- */
//Create an instance of the SHT1X sensor
SHT1x sht15(A4, A5);//Data, SCK

//delacre output pins for powering the sensor
int power = A3;
int gnd = A2;

/* -- Thermocouples -- */
#include <OneWire.h>
#include <DallasTemperature.h>

// Data wire is plugged into port 2 on the Arduino
#define ONE_WIRE_BUS 2
#define TEMPERATURE_PRECISION 9

// Setup a oneWire instance to communicate with any OneWire devices (not just Maxim/Dallas temperature ICs)
OneWire oneWire(ONE_WIRE_BUS);

// Pass our oneWire reference to Dallas Temperature. 
DallasTemperature sensors(&oneWire);

// arrays to hold device addresses
DeviceAddress inThermocouple, outThermocouple;

/* -- Serial -- */
String serialStr = "";
boolean serialStrReady = false;

/* -- variables for storing values -- */
float tempC = 0;
float humidity = 0;
float t_in = 0;
float t_out = 0;

void setup()
{
  Serial.begin(115200); // Open serial connection to report values to host

/* -- SHT1x -- */
  pinMode(power, OUTPUT);
  digitalWrite(power, HIGH);
  pinMode(gnd, OUTPUT);
  digitalWrite(gnd, LOW);

/* -- Thermocouples -- */
  // Start up the library
  sensors.begin();
  
/* -- Thermocouples -- */
  // set the resolution to 9 bit
  sensors.setResolution(inThermocouple, TEMPERATURE_PRECISION);
  sensors.setResolution(outThermocouple, TEMPERATURE_PRECISION);

  sensors.getAddress(inThermocouple, 0);  // 3B66418803DC6C05
  sensors.getAddress(outThermocouple, 1); // 3BB91D1900000008

//  Serial.println("Ready");

}
//-------------------------------------------------------------------------------------------
void loop()
{  
  //check serial port for new commands
  readSerial();
  if(serialStrReady){
    processSerial();
  }
}

void readSerial(){
  //pulls in characters from serial port as they arrive
  //builds serialStr and sets ready flag when newline is found
  while (Serial.available()) {
    char inChar = (char)Serial.read(); 
    if (inChar != '\n') {
      serialStr += inChar;
    } 
    else {
      serialStrReady = true;
    }
  }
}

void processSerial(){
  //process serial commands as they are read in
  if(serialStr.equals("UPDATE")){
    readSHT();
    t_in = readThermocouple(inThermocouple);
    t_out = readThermocouple(outThermocouple);
    Serial.print("Ambient Temp ");
    Serial.print(tempC);
    Serial.print(" C and humidity ");
    Serial.print(humidity); 
    Serial.print(" %. ");
    Serial.print("Temperature in ");
    Serial.print(t_in);
    Serial.print(" C and temperature out ");
    Serial.print(t_out);
    Serial.println(" C.");
  }
  else if(serialStr.equals("SHT")){
    readSHT();
    Serial.print("Ambient Temp ");
    Serial.print(tempC);
    Serial.print(" C and humidity ");
    Serial.print(humidity); 
    Serial.println(" %");
  }
  else if(serialStr.equals("TK")){
    t_in = readThermocouple(inThermocouple);
    t_out = readThermocouple(outThermocouple);
    Serial.print("Temperature in ");
    Serial.print(t_in);
    Serial.print(" C and temperature out ");
    Serial.print(t_out);
    Serial.println(" C");
  }
  else{
     Serial.write("Invalid command: ["); 
     char buf[40];
     serialStr.toCharArray(buf, 40);
     Serial.write(buf); 
     Serial.write("]\n"); 
  }
  serialStrReady = false;
  serialStr = "";
}
//-------------------------------------------------------------------------------------------
void readSHT()
{
  // Read values from the sensor
  tempC = sht15.readTemperatureC();
  humidity = sht15.readHumidity();  
}
//-------------------------------------------------------------------------------------------
float readThermocouple(DeviceAddress deviceAddress)
{
  //Read thermocouple temp in and out
  sensors.requestTemperatures();
  return sensors.getTempC(deviceAddress);
}
//-------------------------------------------------------------------------------------------

