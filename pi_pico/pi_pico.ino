#include <MBED_RP2040_PWM.h>
#include <Wire.h>
#include <SPI.h>

#define STEPS 200

#define TENSION_PIN A2
#define TARGET_TENSION 750
#define MAX_TENSION 800
#define MIN_TENSION 650

#define SPROCKET_LASER_PIN A1
#define SPROCKET_MAX_THRESHOLD 120
#define SPROCKET_DIFF_THRESHOLD 12
#define SPROCKET_RESET_THRESHOLD 100

int sprocketThresholdOffset = 30;

#define FEED_STEP_PIN 2
#define FEED_DIR_PIN 3
#define FEED_EN_PIN 1

#define TAKE_UP_STEP_PIN 6
#define TAKE_UP_DIR_PIN 7
#define TAKE_UP_EN_PIN 8

#define LOW_LIGHT_LED 16
#define NORMAL_LIGHT_LED 17
#define HIGH_LIGHT_LED 18

#define REWIND_BTN 16

#define I2C_ADDR 0x3F
//#define I2C_SDA 4//0
//#define I2C_SCL 5//1

mbed::PwmOut* feedStepper = nullptr;

double Input;

bool log_info = true;

int lowPassValue;
float lowPassFilterAlpha = 0.1f;

bool rewindState = false;


void setup() {
  // put your setup code here, to run once:
  
  pinMode(LOW_LIGHT_LED, OUTPUT);
  pinMode(NORMAL_LIGHT_LED, OUTPUT);
  pinMode(HIGH_LIGHT_LED, OUTPUT);
  digitalWrite(LOW_LIGHT_LED, 0);
  digitalWrite(NORMAL_LIGHT_LED, 0);
  digitalWrite(HIGH_LIGHT_LED, 0);

  pinMode(TAKE_UP_STEP_PIN, OUTPUT);
  pinMode(TAKE_UP_DIR_PIN, OUTPUT);
  pinMode(TAKE_UP_EN_PIN, OUTPUT);
  digitalWrite(TAKE_UP_STEP_PIN, 0);
  digitalWrite(TAKE_UP_DIR_PIN, 0);
  digitalWrite(TAKE_UP_EN_PIN, 0);

  pinMode(FEED_DIR_PIN, OUTPUT);
  pinMode(FEED_EN_PIN, OUTPUT);
  digitalWrite(FEED_DIR_PIN, 0);
  digitalWrite(FEED_EN_PIN, 0);

  setPWM(feedStepper, FEED_STEP_PIN, 100, 0);

  Input = analogRead(TENSION_PIN);

  Wire.begin(I2C_ADDR);
  Wire.setClock(400000);
  Wire.onRequest(requestEvent);
  Wire.onReceive(receiveEvent);

  Serial.begin(9600);
  
  SPI.begin();
  pinMode(MOSI, OUTPUT);
  pinMode(SCK, OUTPUT);
  pinMode(SS, OUTPUT);
  SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE0));

  pinMode(REWIND_BTN, INPUT_PULLUP);

  
}

int lowPassFilter(int value) {
  lowPassValue = lowPassFilterAlpha * value + (1 - lowPassFilterAlpha) * lowPassValue;
  return lowPassValue;
}

void findNextFrame() {
  int stepDelayMs = 1;
  long steps = 0;
  long maxSteps = 500; 
  int largestSprocketValue = 0;
  int smallestSprocketValue = 999;
  int sprocketValueDiffThreshold = 4;
  int sprocketValue;

  bool resetPointFound = false;
  bool maxPointFound = false;
  bool sprocketFound = false;

  while(true && steps < maxSteps) {

    Input = analogRead(TENSION_PIN);

    sprocketValue = lowPassFilter(analogRead(SPROCKET_LASER_PIN) + sprocketThresholdOffset);

    Serial.print("resetPoint: ");
    Serial.print(resetPointFound);
    Serial.print(", maxPointFound: ");
    Serial.println(maxPointFound);

    Serial.print(sprocketValue);
    Serial.print(", ");
    Serial.println(largestSprocketValue);

    if(sprocketValue > largestSprocketValue && resetPointFound) {
      largestSprocketValue = sprocketValue;
    }

    if(!resetPointFound) {
      if(sprocketValue < SPROCKET_RESET_THRESHOLD) {
        resetPointFound = true;
      }
    } else if(!maxPointFound) {
      if(sprocketValue > SPROCKET_MAX_THRESHOLD){
        maxPointFound = true;
      }
    } 
    else {
      if(abs(sprocketValue - largestSprocketValue) >= SPROCKET_DIFF_THRESHOLD) {
        sprocketFound = true;
        stopPWM(feedStepper, FEED_STEP_PIN);
        break;
      }
    }

    digitalWrite(TAKE_UP_STEP_PIN, 1);
    delay(stepDelayMs);
    digitalWrite(TAKE_UP_STEP_PIN, 0);
    delay(stepDelayMs);

    int speed = map(Input, MIN_TENSION, MAX_TENSION, 10, 90);

    speed = 100-speed;

    if(Input < TARGET_TENSION-50) {
      stopPWM(feedStepper, FEED_STEP_PIN);
      Serial.println("hold");
    } else if(Input <= MIN_TENSION) {
      stopPWM(feedStepper, FEED_STEP_PIN);
      Serial.println("stop");
      break;
    } else {
      setPWM(feedStepper, FEED_STEP_PIN, 200, speed);
      Serial.print("run: ");
      Serial.println(speed);
    }
    
    steps++;
  }
}

void receiveEvent(int bytes) {
  if(log_info) {
    Serial.print("recv event, bytes: ");
    Serial.println(bytes);
  }

  if(bytes <= 0) {
    return;
  }

  int cmd = Wire.read();
  int args[3];

  if(log_info){
    Serial.print("cmd: ");
    Serial.println(cmd);
  }

  for(int i = 1; i < bytes; i++) {
    int data = Wire.read();

    if(i < 4) {
      args[i-1] = data;
    }

    if(log_info) {
      Serial.print("extra data: ");
      Serial.println(data);
    }
  }

  switch(cmd) {
    case 0:
      //Wire.write((uint8_t)1);
    break;
    case 2:
      for(int i = 0; i < args[0]; i++) {
        findNextFrame();
      }
    break;

    case 3:
      if(log_info) {
        Serial.print("set sprocket offset: ");
        Serial.println(args[0]);
      }

      sprocketThresholdOffset = args[0];
    break;

    case 5:{

      int ledValue = ( args[0] << 1) | ( args[1] >> 7);
      int dacValue = 4095-512 + ledValue;
      uint8_t first4Bits = (dacValue >> 8) & 0xF; // Shift right by 8 to get the first 4 bits
      uint8_t last8Bits = dacValue & 0xFF; // Mask to get the last 8 bits
      if(log_info) {
        Serial.print("Dac value: ");
        Serial.println(dacValue);
      }

      digitalWrite(SS, LOW);
      SPI.transfer(0b00010000 | first4Bits); // DAC configuration bits + MSB
      SPI.transfer(last8Bits); // LSB of DAC data (lower 8 bits)
      digitalWrite(SS, HIGH);

    break;
    }

    case 6:{
      int rewindValue = args[0];

      if(rewindValue > 0) {
        rewindState = true;
      } else {
        rewindState = false;
      }
    
    break;
    }
  }

  Wire.flush();
  if(log_info)
    Serial.println("-----------");

}

void requestEvent() {
  if(log_info)
    Serial.println("requestEvent");
  if(Input < (double)MIN_TENSION) {
    Wire.write((uint8_t)2);
  } else {
    Wire.write((uint8_t)0);
  }
  
  if(log_info)
    Serial.println("-----------");
}

void loop() {
  // put your main code here, to run repeatedly:

  int rewindBtnState = digitalRead(REWIND_BTN);

  if(rewindBtnState == LOW || rewindState) {
    digitalWrite(TAKE_UP_EN_PIN, 1);
    digitalWrite(FEED_DIR_PIN, 1);

    setPWM(feedStepper, FEED_STEP_PIN, 400, 20);
  } else {
    stopPWM(feedStepper, FEED_STEP_PIN);
    digitalWrite(TAKE_UP_EN_PIN, 0);
    digitalWrite(FEED_DIR_PIN, 0);
  }

  if(analogRead(TENSION_PIN) < (double)MIN_TENSION) {
    //only allow rewind from button if tension is low
    rewindState = false;
  }
  

  delay(10);
  
}
