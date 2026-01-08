"""
金魚消しカスイマー制御プログラム
Raspberry Pi Pico W用
MicroPython
"""

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

# ==================== モータ制御関数 ====================
def drive_motor(in1_pwm, in2_pwm, speed):
    """モータ駆動ヘルパー関数（PWMで速度制御）"""
    abs_speed = abs(speed)
    max_duty = 65535
    
    if speed > 0:  # 前進
        in1_pwm.duty_u16(abs_speed)  # IN1にPWM
        in2_pwm.duty_u16(0)          # IN2をLow
    elif speed < 0:  # 後退
        in1_pwm.duty_u16(0)          # IN1をLow
        in2_pwm.duty_u16(abs_speed)  # IN2にPWM
    else:  # 停止
        in1_pwm.duty_u16(0)
        in2_pwm.duty_u16(0)
    
    # print(f"Duty: {abs_speed}")

def drive(left_speed, right_speed):
    """左右モータ制御"""
    drive_motor(motor_m1a, motor_m1b, right_speed)
    drive_motor(motor_m2a, motor_m2b, left_speed)

def set_mouth_angle(angle):
    """サーボモータの角度設定（0〜180度）"""
    # FT90B仕様: 500us(0°)〜2500us(180°)
    # 50Hz(20ms)におけるduty_u16換算:
    # 500us  -> 1638
    # 2500us -> 8192
    min_duty = 1638
    max_duty = 8192
    
    if angle < 0: angle = 0
    if angle > 180: angle = 180
    
    duty = int(min_duty + (max_duty - min_duty) * angle / 180)
    mouth_pwm.duty_u16(duty)

# ==================== 走行制御 ====================
def start_forward():
    """前進開始"""
    NORMAL_SPEED = 32768
    # print("走行開始")
    drive(NORMAL_SPEED, NORMAL_SPEED)

# ==================== 回転制御 ====================
def rotate(angle):
    """回転制御（正:時計回り, 負:反時計回り）"""
    ROTATION_SPEED = 26214
    print(f"回転 {angle}°")
    
    # 時計回り: 左正転・右逆転, 反時計: 左逆転・右正転
    l_speed = ROTATION_SPEED if angle > 0 else -ROTATION_SPEED
    r_speed = -ROTATION_SPEED if angle > 0 else ROTATION_SPEED
    
    drive(l_speed, r_speed)
    print(abs(angle) / 9.0,"秒回転")
    time.sleep(abs(angle) / 9.0) # 回転し終わるまで待機

    print("回転終了")
    
    start_forward()

# ==================== 端検出処理 ====================
def edge_detected_handler():
    """端検出時の処理"""
    print("!!! 端を検出 !!! sensor value:", edge_sensor.value())
    
    # 回転方向を時計回りに固定 (1: 時計回り)
    direction = 1
    
    # 回転速度 (rotate関数と合わせる)
    ROTATION_SPEED = 26214
    
    # マイクロスイッチがオフになるまで回転
    # print("端から離れるまで回転中...")
    l_speed = ROTATION_SPEED
    r_speed = -ROTATION_SPEED
    drive(l_speed, r_speed)
    
    # センサーが反応(1)している間は待機（押下時HIGHに変更）
    while edge_sensor.value() == 1:
        time.sleep(0.01)
    
    print("端から離れた")
    # オフになったら、そこから10°～80°または100°～170°追加回転
    if random.randint(0, 1) == 0:
        additional_angle = random.randint(10, 80)
    else:
        additional_angle = random.randint(100, 170)
    
    # そのまま指定角度分回転（rotate関数を使用）
    rotate(direction * additional_angle)
    
    # 回転後、前進再開
    start_forward()

# ==================== 磁気センサー処理 ====================
def check_magnetic_sensors():
    """磁気センサーの確認"""
    
    # センサー①：時計回り90°
    if magnetic_sensor_1.value() == 0:
        print("上方")
        drive(0, 0)
        led.value(1) # LED点灯
        rotate(90)
        led.value(0) # LED消灯
        return
    
    # センサー②：反時計回り90°
    if magnetic_sensor_2.value() == 0:
        print("下方")
        drive(0, 0)
        led.value(1) # LED点灯
        rotate(-90)
        led.value(0) # LED消灯
        return
    
    # センサー③：180°回転
    if magnetic_sensor_3.value() == 0:
        print("後方")
        drive(0, 0)
        led.value(1) # LED点灯
        rotate(180)
        led.value(0) # LED消灯
        return

# ==================== 口開閉アニメーション ====================
def mouth_animation():
    """口開閉アニメーション（別スレッド実行）"""
    ANGLE_CLOSE = 0
    ANGLE_OPEN = 78
    DURATION = 2000  # 動作時間（ms）
    STEPS = 50       # 分割数
    STEP_DELAY = DURATION / STEPS / 1000.0

    # 初期化：口を閉じる
    set_mouth_angle(ANGLE_CLOSE)
    time.sleep(1.0) # 起動遅延
    print("ギミック開始")
    
    while True:
        # 往復動作ループ
        # 開く(0->78) -> 閉じる(78->0) の順で角度リストを作成して実行
        for target_start, target_end in [(ANGLE_CLOSE, ANGLE_OPEN), (ANGLE_OPEN, ANGLE_CLOSE)]:
            angle_step = (target_end - target_start) / STEPS
            for i in range(STEPS):
                set_mouth_angle(target_start + angle_step * i)
                time.sleep(STEP_DELAY)
            set_mouth_angle(target_end)

# ==================== メインループ ====================
def main():
    """メインプログラム"""
    
    # システム起動
    print("=== システム起動 ===")
    start_forward()
    
    # 口開閉アニメーションスレッド開始
    _thread.start_new_thread(mouth_animation, ())
    
    print("メインループ開始")
    
    try:
        while True:
            print(edge_sensor.value())

            # 端検出チェック（押下時HIGHに変更）
            if edge_sensor.value() == 1:
                edge_detected_handler()
            
            # 磁気センサーチェック
            check_magnetic_sensors()
            
            time.sleep(0.1)  # 10msごとにループ
            
    except KeyboardInterrupt:
        print("\n=== プログラム終了 ===")
        drive(0, 0)

# ==================== プログラム開始 ====================
if __name__ == "__main__":
    main()