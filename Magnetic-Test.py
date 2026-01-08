from picozero import Button, Servo, Motor, pico_led
from time import sleep

# ==================== GPIO設定 ====================
# 走行モジュール（モータードライバ TB6612FNG使用）
# picozeroのMotorクラスは forward/backward ピンを指定します
# 内部でPWM処理が行われるため、速度制御(0.0〜1.0)も可能です
motor_right = Motor(forward=0, backward=1)  # GPIO0: 右前進, GPIO1: 右後退
motor_left = Motor(forward=2, backward=3)   # GPIO2: 左前進, GPIO3: 左後退

# 端検出モジュール（マイクロスイッチ）
# GPIO17 (picozeroのButtonはデフォルトでPull-up有効です)
edge_sensor = Button(17)

# 操作モジュール（磁気センサー：ホールセンサ）
# ホールICは通常Pull-upで使用し、磁石接近でLow(Active)になります
magnetic_sensor_1 = Button(6)  # GPIO6: 時計回り90°
magnetic_sensor_2 = Button(7)  # GPIO7: 反時計回り90°
magnetic_sensor_3 = Button(8)  # GPIO8: 180°回転

# ギミックモジュール（サーボモータ：FEETECH FT90B）
# GPIO14
mouth_servo = Servo(14)

# ==================== コールバック関数 ====================
def on_magnet_1():
    print("Magnetic Sensor 1 Detected! (Clockwise)")
    pico_led.blink(on_time=0.1, off_time=0.1, n=1)

def on_magnet_2():
    print("Magnetic Sensor 2 Detected! (Quarter Turn)")
    pico_led.blink(on_time=0.1, off_time=0.1, n=1)
    
def on_magnet_3():
    print("Magnetic Sensor 3 Detected! (Half Turn)")
    pico_led.blink(on_time=0.1, off_time=0.1, n=2)

# ==================== イベント登録 ====================
# when_pressed はボタンが押された(Lowになった)ときに発火します
magnetic_sensor_1.when_pressed = on_magnet_1
magnetic_sensor_2.when_pressed = on_magnet_2
magnetic_sensor_3.when_pressed = on_magnet_3

# ==================== メインループ ====================
def main():
    """メインプログラム (picozero版)"""
    print("Magnetic Test Started (picozero version)")
    print("Waiting for magnets...")
    
    try:
        # イベント駆動なのでループ内は空でOK
        while True:
            sleep(1)
            
    except KeyboardInterrupt:
        print("\n=== プログラム終了 ===")

# ==================== プログラム開始 ====================
if __name__ == "__main__":
    main()


