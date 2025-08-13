import serial

SERIAL_PORT = '/dev/ttyACM0'  # ajuste para a porta correta
BAUD_RATE = 115200

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print("Conectado na serial, esperando dados...")
    while True:
        linha = ser.readline().decode('utf-8', errors='ignore').strip()
        if linha:
            print(f"Linha recebida: {linha}")
except Exception as e:
    print(f"Erro: {e}")
finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
