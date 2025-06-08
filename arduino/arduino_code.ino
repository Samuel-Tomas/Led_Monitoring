#include <FastLED.h>

#define LED_PIN     6
#define NUM_LEDS    12
CRGB leds[NUM_LEDS];

void setup() {
  Serial.begin(9600);
  FastLED.addLeds<WS2812, LED_PIN, GRB>(leds, NUM_LEDS);
  FastLED.clear();
  FastLED.show();
}

void loop() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    int brightness = input.toInt();
    brightness = constrain(brightness, 0, 255);

    for (int i = 0; i < NUM_LEDS; i++) {
      leds[i] = CRGB(brightness, brightness, brightness);  // biela farba
    }
    FastLED.show();
  }

  // Simulácia senzora – odosiela hodnotu do Raspberry Pi
  int sensorValue = analogRead(A0);
  Serial.print("L:");
  Serial.println(sensorValue);
  delay(500);
}
