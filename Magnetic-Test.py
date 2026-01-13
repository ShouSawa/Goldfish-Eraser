from picozero import Button
from time import sleep

# ホールセンサー（磁気センサー）の設定
# GPIO 6, 7, 8 に接続されている前提
# picozeroのButtonクラスはデフォルトで内部プルアップが有効
sensor_6 = Button(6)
sensor_7 = Button(7)
sensor_8 = Button(8)

print("--- Magnetic Sensor Test (picozero) ---")
print("Reading GPIO 6, 7, 8...")

try:
    while True:
        # 各センサーの状態を取得 (1: 検出中/押された, 0: 非検出)
        val_6 = sensor_6.value
        val_7 = sensor_7.value
        val_8 = sensor_8.value
        
        # 状態をコンソールに出力
        # 検出時は "ON", 非検出時は "OFF" と表示
        status_6 = "ON " if val_6 else "OFF"
        status_7 = "ON " if val_7 else "OFF"
        status_8 = "ON " if val_8 else "OFF"
        
        print(f"GPIO6: {status_6} | GPIO7: {status_7} | GPIO8: {status_8}")
        
        # 読みやすさのために少し待機
        sleep(0.1)

except KeyboardInterrupt:
    print("\nTest stopped by user")


