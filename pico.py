"""
金魚消しカスイマー制御プログラム
Raspberry Pi Pico W用
MicroPython
"""

from machine import Pin, PWM
import time
import random

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

# 収集モジュール（回転ブラシモータ）
brush_cin1 = Pin(6, Pin.OUT)        # GPIO6: ブラシ前進
brush_cin2 = Pin(7, Pin.OUT)        # GPIO7: ブラシ後退
brush_pwm = PWM(Pin(8))             # GPIO8: ブラシPWM
brush_pwm.freq(1000)

# 端検出モジュール（マイクロスイッチ）
edge_sensor_front_left = Pin(9, Pin.IN, Pin.PULL_UP)    # GPIO9
edge_sensor_front_center = Pin(10, Pin.IN, Pin.PULL_UP) # GPIO10
edge_sensor_front_right = Pin(11, Pin.IN, Pin.PULL_UP)  # GPIO11
edge_sensor_side = Pin(12, Pin.IN, Pin.PULL_UP)         # GPIO12

# 操作モジュール（磁気センサー：ホールセンサ）
magnetic_sensor_1 = Pin(13, Pin.IN, Pin.PULL_UP)  # GPIO13: 時計回り90°
magnetic_sensor_2 = Pin(14, Pin.IN, Pin.PULL_UP)  # GPIO14: 反時計回り90°
magnetic_sensor_3 = Pin(15, Pin.IN, Pin.PULL_UP)  # GPIO15: 180°回転

# ギミックモジュール（サーボモータ）
servo_mouth = PWM(Pin(16))          # GPIO16: 口開閉サーボ
servo_mouth.freq(50)                # サーボは50Hz

# 電源モジュール（起動ボタン）
start_button = Pin(17, Pin.IN, Pin.PULL_DOWN)  # GPIO17

# オンボードLED（デバッグ用）
led = Pin("LED", Pin.OUT)

# ==================== グローバル変数 ====================
is_running = False              # システム動作状態
rotation_in_progress = False    # 回転動作中フラグ
edge_rotation_priority = False  # 端検出回転の優先フラグ
normal_speed = 32768            # 通常走行速度（0～65535）
rotation_speed = 26214          # 回転速度（約40%）
mouth_open = False              # 口の開閉状態
last_button_state = 0           # ボタンの前回状態（チャタリング対策）
last_button_time = 0            # ボタン押下時刻

# ==================== モータ制御関数 ====================
def motor_left_forward(speed):
    """左モータ前進"""
    motor_left_ain1.value(1)
    motor_left_ain2.value(0)
    motor_left_pwm.duty_u16(speed)

def motor_left_backward(speed):
    """左モータ後退"""
    motor_left_ain1.value(0)
    motor_left_ain2.value(1)
    motor_left_pwm.duty_u16(speed)

def motor_left_stop():
    """左モータ停止"""
    motor_left_ain1.value(0)
    motor_left_ain2.value(0)
    motor_left_pwm.duty_u16(0)

def motor_right_forward(speed):
    """右モータ前進"""
    motor_right_bin1.value(1)
    motor_right_bin2.value(0)
    motor_right_pwm.duty_u16(speed)

def motor_right_backward(speed):
    """右モータ後退"""
    motor_right_bin1.value(0)
    motor_right_bin2.value(1)
    motor_right_pwm.duty_u16(speed)

def motor_right_stop():
    """右モータ停止"""
    motor_right_bin1.value(0)
    motor_right_bin2.value(0)
    motor_right_pwm.duty_u16(0)

def brush_motor_start():
    """回転ブラシ起動"""
    brush_cin1.value(1)
    brush_cin2.value(0)
    brush_pwm.duty_u16(32768)  # 50%速度

def brush_motor_stop():
    """回転ブラシ停止"""
    brush_cin1.value(0)
    brush_cin2.value(0)
    brush_pwm.duty_u16(0)

def servo_close_mouth():
    """口を閉じる（0°）"""
    # 0°: 500us → 50Hzで duty = 500/20000 * 65535 ≈ 1638
    servo_mouth.duty_u16(1638)

def servo_open_mouth():
    """口を開く（90°）"""
    # 90°: 1500us → 50Hzで duty = 1500/20000 * 65535 ≈ 4915
    servo_mouth.duty_u16(4915)

# ==================== 初期化処理 ====================
def init_system():
    """システム初期化"""
    print("=== 金魚消しカスイマー システム起動 ===")
    print("初期化中...")
    
    # 全モータ停止
    motor_left_stop()
    motor_right_stop()
    brush_motor_stop()
    
    # サーボ初期位置（口を閉じる）
    servo_close_mouth()
    time.sleep(0.5)
    
    # LED点滅（初期化完了の合図）
    for _ in range(3):
        led.value(1)
        time.sleep(0.1)
        led.value(0)
        time.sleep(0.1)
    
    print("初期化完了")
    print("起動ボタンを押してください")

# ==================== 走行制御 ====================
def start_forward():
    """前進開始（走行状態のentry）"""
    global is_running
    if not rotation_in_progress:
        print("走行開始：前進・収集・ギミック")
        motor_left_forward(normal_speed)
        motor_right_forward(normal_speed)
        brush_motor_start()
        led.value(1)  # LED点灯（動作中を示す）

def stop_all_motors():
    """全モータ停止（停止状態のentry）"""
    print("全モータ停止")
    motor_left_stop()
    motor_right_stop()
    brush_motor_stop()
    servo_close_mouth()
    led.value(0)  # LED消灯

# ==================== 回転制御 ====================
def rotate_clockwise(angle):
    """時計回り回転"""
    global rotation_in_progress
    rotation_in_progress = True
    
    print(f"時計回り {angle}° 回転開始")
    
    # 走行モータを回転モードに（収集・ギミックは継続）
    motor_left_forward(rotation_speed)
    motor_right_backward(rotation_speed)
    
    # 角速度90°/s → 回転時間計算
    rotation_time = abs(angle) / 90.0
    time.sleep(rotation_time)
    
    # 回転終了
    motor_left_stop()
    motor_right_stop()
    rotation_in_progress = False
    print("回転完了")

def rotate_counterclockwise(angle):
    """反時計回り回転"""
    global rotation_in_progress
    rotation_in_progress = True
    
    print(f"反時計回り {angle}° 回転開始")
    
    # 走行モータを回転モードに
    motor_left_backward(rotation_speed)
    motor_right_forward(rotation_speed)
    
    # 角速度90°/s → 回転時間計算
    rotation_time = abs(angle) / 90.0
    time.sleep(rotation_time)
    
    # 回転終了
    motor_left_stop()
    motor_right_stop()
    rotation_in_progress = False
    print("回転完了")

# ==================== 端検出処理 ====================
def check_edge_sensors():
    """端検出センサーの確認"""
    # マイクロスイッチはプルアップなので、押されると0（False）
    if (edge_sensor_front_left.value() == 0 or 
        edge_sensor_front_center.value() == 0 or 
        edge_sensor_front_right.value() == 0 or 
        edge_sensor_side.value() == 0):
        return True
    return False

def edge_detected_handler():
    """端検出時の処理"""
    global edge_rotation_priority, rotation_in_progress
    
    if rotation_in_progress and not edge_rotation_priority:
        # 磁気センサーによる回転中の場合は、完了を待つ
        print("端検出：回転完了待機中")
        while rotation_in_progress:
            time.sleep(0.1)
    
    print("!!! 端を検出 !!!")
    edge_rotation_priority = True
    
    # ランダム角度生成（100°～260°）
    direction = random.choice([-1, 1])
    angle = random.randint(100, 260)
    
    if direction == 1:
        rotate_clockwise(angle)
    else:
        rotate_counterclockwise(angle)
    
    edge_rotation_priority = False
    
    # 回転後、前進再開
    if is_running:
        start_forward()

# ==================== 磁気センサー処理 ====================
def check_magnetic_sensors():
    """磁気センサーの確認"""
    global edge_rotation_priority
    
    if is_running and not edge_rotation_priority and not rotation_in_progress:
        # センサー①：時計回り90°
        if magnetic_sensor_1.value() == 0:
            print("磁気センサー① 検出")
            motor_left_stop()
            motor_right_stop()
            rotate_clockwise(90)
            if is_running:
                start_forward()
            time.sleep(0.5)  # 連続検出防止
            return True
        
        # センサー②：反時計回り90°
        if magnetic_sensor_2.value() == 0:
            print("磁気センサー② 検出")
            motor_left_stop()
            motor_right_stop()
            rotate_counterclockwise(90)
            if is_running:
                start_forward()
            time.sleep(0.5)
            return True
        
        # センサー③：180°回転
        if magnetic_sensor_3.value() == 0:
            print("磁気センサー③ 検出")
            motor_left_stop()
            motor_right_stop()
            rotate_clockwise(180)
            if is_running:
                start_forward()
            time.sleep(0.5)
            return True
    
    return False

# ==================== 口開閉アニメーション ====================
mouth_animation_counter = 0

def update_mouth_animation():
    """口開閉アニメーション更新"""
    global mouth_open, mouth_animation_counter
    
    if is_running:
        mouth_animation_counter += 1
        # 10回のループ（約1秒）ごとに開閉
        if mouth_animation_counter >= 10:
            mouth_animation_counter = 0
            if mouth_open:
                servo_close_mouth()
                mouth_open = False
            else:
                servo_open_mouth()
                mouth_open = True
    else:
        # 停止中は口を閉じたまま
        servo_close_mouth()
        mouth_open = False
        mouth_animation_counter = 0

# ==================== 起動・停止制御 ====================
def check_start_button():
    """起動ボタンのチェック（チャタリング対策付き）"""
    global is_running, last_button_state, last_button_time
    
    current_state = start_button.value()
    current_time = time.ticks_ms()
    
    # 立ち上がりエッジ検出＋チャタリング対策（50ms）
    if (current_state == 1 and 
        last_button_state == 0 and 
        time.ticks_diff(current_time, last_button_time) > 50):
        
        toggle_system()
        last_button_time = current_time
    
    last_button_state = current_state

def toggle_system():
    """起動/停止切り替え"""
    global is_running
    
    if is_running:
        # 停止処理
        print("=== システム停止 ===")
        is_running = False
        stop_all_motors()
    else:
        # 起動処理
        print("=== システム起動 ===")
        is_running = True
        start_forward()

# ==================== メインループ ====================
def main():
    """メインプログラム"""
    # 初期化
    init_system()
    
    print("メインループ開始")
    loop_counter = 0
    
    try:
        while True:
            # 起動ボタンチェック
            check_start_button()
            
            # システム動作中の処理
            if is_running:
                # 端検出チェック
                if check_edge_sensors():
                    edge_detected_handler()
                
                # 磁気センサーチェック
                check_magnetic_sensors()
                
                # 口開閉アニメーション更新（約100msごと）
                if loop_counter % 1 == 0:
                    update_mouth_animation()
            
            loop_counter += 1
            time.sleep(0.1)  # 100msごとにループ
            
    except KeyboardInterrupt:
        print("\n=== プログラム終了 ===")
        is_running = False
        stop_all_motors()

# ==================== プログラム開始 ====================
if __name__ == "__main__":
    main()


