from machine import Pin, PWM
import time
import random
import _thread


# ==================== GPIO設定 ====================
# 走行モジュール（モータードライバ TB6612FNG使用）
# 右モータ
motor_m1a = PWM(Pin(0))  # GPIO0: 右前進用PWM
motor_m1b = PWM(Pin(1))  # GPIO1: 右後退PWM
motor_m2a = PWM(Pin(2))  # GPIO2: 左前進PWM
motor_m2b = PWM(Pin(3))  # GPIO3: 左後退PWM

# 端検出モジュール（マイクロスイッチ）
edge_sensor = Pin(17, Pin.IN)    # GPIO9

# 操作モジュール（磁気センサー：ホールセンサ）
magnetic_sensor_1 = Pin(6, Pin.IN, Pin.PULL_UP)  # GPIO13: 時計回り90°
magnetic_sensor_2 = Pin(7, Pin.IN, Pin.PULL_UP)  # GPIO14: 反時計回り90°
magnetic_sensor_3 = Pin(8, Pin.IN, Pin.PULL_UP)  # GPIO15: 180°回転

# ギミックモジュール（サーボモータ：FEETECH FT90B）
mouth_pwm = PWM(Pin(14))          # GPIO16: サーボ信号
mouth_pwm.freq(50)                # 50Hz

# オンボードLED（デバッグ用）
led = Pin("LED", Pin.OUT)

# ==================== メインループ ====================
def main():
    """メインプログラム"""
    
    print("メインループ開始")
    
    try:
        while True:
            print("Magnetic Sensor 1:", magnetic_sensor_1.value())
            print("Magnetic Sensor 2:", magnetic_sensor_2.value())
            print("Magnetic Sensor 3:", magnetic_sensor_3.value())

            time.sleep(0.1)  # 10msごとにループ
            
    except KeyboardInterrupt:
        print("\n=== プログラム終了 ===")

# ==================== プログラム開始 ====================
if __name__ == "__main__":
    main()

