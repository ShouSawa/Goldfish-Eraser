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
# 左モータ
motor_left_ain1 = Pin(0, Pin.OUT)   # GPIO0: 左前進
motor_left_ain2 = Pin(1, Pin.OUT)   # GPIO1: 左後退
motor_left_pwm = PWM(Pin(2))        # GPIO2: 左PWM
motor_left_pwm.freq(1000)

# 右モータ
motor_right_bin1 = Pin(3, Pin.OUT)  # GPIO3: 右前進
motor_right_bin2 = Pin(4, Pin.OUT)  # GPIO4: 右後退
motor_right_pwm = PWM(Pin(5))       # GPIO5: 右PWM
motor_right_pwm.freq(1000)

# 収集モジュール（回転ブラシモータ：DCモータ RF-300CV）
# モータドライバ不使用（トランジスタ等でON/OFF制御）
brush_pin = Pin(6, Pin.OUT)         # GPIO6: ブラシ電源制御

# 端検出モジュール（マイクロスイッチ）
edge_sensor = Pin(9, Pin.IN, Pin.PULL_UP)    # GPIO9

# 操作モジュール（磁気センサー：ホールセンサ）
magnetic_sensor_1 = Pin(13, Pin.IN, Pin.PULL_UP)  # GPIO13: 時計回り90°
magnetic_sensor_2 = Pin(14, Pin.IN, Pin.PULL_UP)  # GPIO14: 反時計回り90°
magnetic_sensor_3 = Pin(15, Pin.IN, Pin.PULL_UP)  # GPIO15: 180°回転

# ギミックモジュール（サーボモータ：FEETECH FT90B）
mouth_pin = PWM(Pin(16))          # GPIO16: サーボ信号
mouth_pin.freq(50)                # 50Hz

# 電源モジュール（起動ボタン）
start_switch = Pin(17, Pin.IN, Pin.PULL_DOWN)  # GPIO17

# オンボードLED（デバッグ用）
led = Pin("LED", Pin.OUT)

# ==================== グローバル変数 ====================
is_running = False              # システム動作状態

# ==================== モータ制御関数 ====================
def drive_motor(in1, in2, pwm, speed):
    """モータ駆動ヘルパー関数"""
    if speed > 0:
        in1.value(1); in2.value(0)
    elif speed < 0:
        in1.value(0); in2.value(1)
    else:
        in1.value(0); in2.value(0)
    pwm.duty_u16(abs(speed))

def drive(left_speed, right_speed):
    """左右モータ制御"""
    drive_motor(motor_left_ain1, motor_left_ain2, motor_left_pwm, left_speed)
    drive_motor(motor_right_bin1, motor_right_bin2, motor_right_pwm, right_speed)

def brush_motor(on):
    """回転ブラシ制御（ON/OFFのみ）"""
    if on:
        brush_pin.value(1)
    else:
        brush_pin.value(0)

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
    mouth_pin.duty_u16(duty)

# ==================== 走行制御 ====================
def start_forward():
    """前進開始"""
    NORMAL_SPEED = 32768
    print("走行開始")
    drive(NORMAL_SPEED, NORMAL_SPEED)

def stop_all_motors():
    """全モータ停止"""
    print("全モータ停止")
    drive(0, 0)
    brush_motor(False)

# ==================== 回転制御 ====================
def rotate(angle):
    """回転制御（正:時計回り, 負:反時計回り）"""
    ROTATION_SPEED = 26214
    print(f"回転 {angle}°")
    
    # 時計回り: 左正転・右逆転, 反時計: 左逆転・右正転
    l_speed = ROTATION_SPEED if angle > 0 else -ROTATION_SPEED
    r_speed = -ROTATION_SPEED if angle > 0 else ROTATION_SPEED
    
    drive(l_speed, r_speed)
    time.sleep(abs(angle) / 90.0)
    
    drive(0, 0)
    print("回転完了")

# ==================== 端検出処理 ====================
def edge_detected_handler():
    """端検出時の処理"""
    print("!!! 端を検出 !!!")
    
    # 回転方向を時計回りに固定 (1: 時計回り)
    direction = 1
    
    # 回転速度 (rotate関数と合わせる)
    ROTATION_SPEED = 26214
    
    # マイクロスイッチがオフになるまで回転
    print("端から離れるまで回転中...")
    l_speed = ROTATION_SPEED
    r_speed = -ROTATION_SPEED
    drive(l_speed, r_speed)
    
    # センサーが反応(0)している間は待機
    while edge_sensor.value() == 0:
        time.sleep(0.01)
    
    # オフになったら、そこから10°～170°追加回転
    additional_angle = random.randint(10, 170)
    print(f"追加回転: {additional_angle}°")
    
    # そのまま指定角度分回転（rotate関数を使用）
    rotate(direction * additional_angle)
    
    # 回転後、前進再開
    if is_running:
        start_forward()

# ==================== 磁気センサー処理 ====================
def check_magnetic_sensors():
    """磁気センサーの確認"""
    
    # 端回転中でなければ処理
    if is_running:
        # センサー①：時計回り90°
        if magnetic_sensor_1.value() == 0:
            print("磁気センサー1 検出")
            drive(0, 0)
            led.value(1) # LED点灯
            rotate(90)
            led.value(0) # LED消灯
            return
        
        # センサー②：反時計回り90°
        if magnetic_sensor_2.value() == 0:
            print("磁気センサー2 検出")
            drive(0, 0)
            led.value(1) # LED点灯
            rotate(-90)
            led.value(0) # LED消灯
            return
        
        # センサー③：180°回転
        if magnetic_sensor_3.value() == 0:
            print("磁気センサー3 検出")
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

    while True:
        if is_running:
            time.sleep(1.0) # 起動遅延
            if not is_running: continue
            
            brush_motor(True)
            
            # 往復動作ループ
            while is_running:
                # 開く(0->78) -> 閉じる(78->0) の順で角度リストを作成して実行
                for target_start, target_end in [(ANGLE_CLOSE, ANGLE_OPEN), (ANGLE_OPEN, ANGLE_CLOSE)]:
                    if not is_running: break
                    angle_step = (target_end - target_start) / STEPS
                    for i in range(STEPS):
                        if not is_running: break
                        set_mouth_angle(target_start + angle_step * i)
                        time.sleep(STEP_DELAY)
                    if is_running: set_mouth_angle(target_end)

            brush_motor(False)
            set_mouth_angle(ANGLE_CLOSE)
        else:
            time.sleep(0.1)

# ==================== 起動・停止制御 ====================
def check_start(current_is_running, last_time):
    """起動スイッチのチェック（トグルスイッチ用）"""
    current_state = start_switch.value()
    current_time = time.ticks_ms()
    
    # チャタリング対策（前回変化から50ms経過していないなら無視）
    if time.ticks_diff(current_time, last_time) < 50:
        return current_is_running, last_time

    # スイッチがON(1) かつ システムが停止中なら -> 起動
    if current_state == 1 and not current_is_running:
        print("=== システム起動 ===")
        start_forward()
        return True, current_time

    # スイッチがOFF(0) かつ システムが起動中なら -> 停止
    elif current_state == 0 and current_is_running:
        print("=== システム停止 ===")
        stop_all_motors()
        return False, current_time
        
    return current_is_running, last_time

# ==================== メインループ ====================
def main():
    """メインプログラム"""
    global is_running
    
    # 口開閉アニメーションスレッド開始
    _thread.start_new_thread(mouth_animation, ())
    
    print("メインループ開始")
    last_button_time = 0
    
    try:
        while True:
            # 起動ボタンチェック
            is_running, last_button_time = check_start(is_running, last_button_time)
            
            # システム動作中の処理
            if is_running:
                # 端検出チェック
                if edge_sensor.value() == 0:
                    edge_detected_handler()
                
                # 磁気センサーチェック
                check_magnetic_sensors()
            
            time.sleep(0.1)  # 100msごとにループ
            
    except KeyboardInterrupt:
        print("\n=== プログラム終了 ===")
        is_running = False
        stop_all_motors()

# ==================== プログラム開始 ====================
if __name__ == "__main__":
    main()