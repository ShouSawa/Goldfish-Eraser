from machine import Pin, PWM, ADC
import time
import random
import _thread


# ==================== GPIO設定 ====================
# 走行モジュール（モータードライバ TB6612FNG使用）
# 右モータ
motor_m1a = PWM(Pin(0, Pin.OUT))  # GPIO0: 右前進用PWM
motor_m1b = PWM(Pin(1, Pin.OUT))  # GPIO1: 右後退PWM
motor_m2a = PWM(Pin(2, Pin.OUT))  # GPIO2: 左前進PWM
motor_m2b = PWM(Pin(3, Pin.OUT))  # GPIO3: 左後退PWM

motor_m1a.freq(500)
motor_m1b.freq(500)
motor_m2a.freq(500)
motor_m2b.freq(500)

# 端検出モジュール（マイクロスイッチ）
edge_sensor = Pin(17, Pin.IN, Pin.PULL_DOWN)    # GPIO17

# 操作モジュール（磁気センサー：ホールセンサ）
magnetic_sensor_1 = ADC(26)  # GPIO26: 時計回り90°
magnetic_sensor_2 = ADC(27)  # GPIO27: 反時計回り90°
magnetic_sensor_3 = ADC(28)  # GPIO28: 180°回転

# ギミックモジュール（サーボモータ：FEETECH FT90B）
mouth_pwm = PWM(Pin(14, Pin.OUT))          # GPIO14: サーボ信号
mouth_pwm.freq(50)                # 50Hz

# オンボードLED（デバッグ用）
led = Pin("LED", Pin.OUT)

try:
    while True:
        # アナログ値を読み取り（0-65535の範囲）
        value1 = magnetic_sensor_1.read_u16()
        value2 = magnetic_sensor_2.read_u16()
        value3 = magnetic_sensor_3.read_u16()
    
        # 電圧に変換（0-3.3V）
        voltage1 = value1 * 3.3 / 65535
        voltage2 = value2 * 3.3 / 65535
        voltage3 = value3 * 3.3 / 65535
    
        print(f"Sensor1: {value1} ({voltage1:.2f}V)")
        print(f"Sensor2: {value2} ({voltage2:.2f}V)")
        print(f"Sensor3: {value3} ({voltage3:.2f}V)")
        print("---")
        
        time.sleep(0.5)


except KeyboardInterrupt:
    print("\nTest stopped by user")


