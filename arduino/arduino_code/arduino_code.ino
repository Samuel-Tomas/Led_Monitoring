<!DOCTYPE html>
<html>
<head>
  <title>Hodnoty zo senzora</title>
  <style>
    body { font-family: sans-serif; padding: 20px; }
    ul { list-style-type: none; padding: 0; }
    li { margin-bottom: 5px; }
    input[type=range] { width: 100%; }
    button { margin: 5px; padding: 8px 14px; }
  </style>
</head>
<body>
  <h2>Výpis hodnôt senzora</h2>

  <label for="slider">Jas LED: <span id="val">0</span>%</label>
  <input type="range" min="0" max="100" value="0" id="slider" disabled>
#include <FastLED.h>

#define LED_PIN     6
#define NUM_LEDS    12
#define LIGHT_SENSOR A0

CRGB leds[NUM_LEDS];
int last_brightness = -1;

void setup() {
  Serial.begin(9600);
  FastLED.addLeds<WS2812, LED_PIN, GRB>(leds, NUM_LEDS);
  setAllWhite(0);
}

void loop() {
  static String input = "";
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      int brightness = input.toInt();
      brightness = constrain(brightness, 0, 255);
      if (brightness != last_brightness) {
        setAllWhite(brightness);
        last_brightness = brightness;
      }
      input = "";
    } else if (isDigit(c)) {
      input += c;
    } else {
      input = "";
    }
  }

  int lightValue = analogRead(LIGHT_SENSOR);
  Serial.print("L:");
  Serial.println(lightValue);
  delay(200); // každých 200 ms
}

void setAllWhite(int brightness) {
  for (int i = 0; i < NUM_LEDS; i++) {
    leds[i] = CRGB(brightness, brightness, brightness);
  }
  FastLED.show();
}
