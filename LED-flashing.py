from machine import Pin
import time

led = Pin('LED', Pin.OUT) # Pico W は 'LED' と設定

for i in range(10):
    led.on()
    time.sleep(1)
    led.off()
    time.sleep(1)

print("LEDチカチカを、10回やりました！")