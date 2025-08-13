from flask import Flask, jsonify, request
from flask_cors import CORS
import serial
import threading
import time
import requests
from dotenv import load_dotenv
import os


app = Flask(__name__)
CORS(app)
load_dotenv()

SERIAL_PORT = '/dev/ttyACM0'  # Ajuste se necessário
BAUD_RATE = 115200

ultimo_bpm = None
leitura_ativa = True
alerta_ativo = False
tempo_inicio_alerta = None
LIMITE_BPM_ALTO = 110
TEMPO_ALERTA = 7  # segundos

# Variáveis para armazenar dados do usuário (em memória)
dados_usuario = {
    "nome": None,
    "telegram_id": None
}

TOKEN = os.getenv('TOKEN_BOT')

def enviar_alerta(mensagem, chat_id):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": mensagem,
        "parse_mode": "Markdown"
    }
    resp = requests.post(url, data=data)
    return resp.json()

def ler_serial():
    global ultimo_bpm, leitura_ativa, alerta_ativo, tempo_inicio_alerta
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print("Conectado na serial, aguardando dados...")
        while leitura_ativa:
            linha = ser.readline().decode('utf-8', errors='ignore').strip()
            if linha:
                print(f"Recebido da serial: '{linha}'")
            if linha.startswith("BPM (média):"):
                try:
                    valor_str = linha.split(":")[1].strip()
                    ultimo_bpm = int(valor_str)
                    print(f"BPM atualizado: {ultimo_bpm}")

                    if ultimo_bpm > LIMITE_BPM_ALTO:
                        if tempo_inicio_alerta is None:
                            tempo_inicio_alerta = time.time()
                        elif time.time() - tempo_inicio_alerta >= TEMPO_ALERTA:
                            if not alerta_ativo:
                                alerta_ativo = True
                                if dados_usuario["telegram_id"] and dados_usuario["nome"]:
                                    msg = (f"🚨 *Alerta de BPM Alto* 🚨\n"
                                           f"Paciente: {dados_usuario['nome']}\n"
                                           f"BPM atual: {ultimo_bpm}\n"
                                           f"Há mais de {TEMPO_ALERTA} segundos.")
                                    enviar_alerta(msg, dados_usuario["telegram_id"])
                    else:
                        tempo_inicio_alerta = None
                        alerta_ativo = False

                except Exception as e:
                    print(f"Erro convertendo BPM: {e}")
            time.sleep(0.1)
    except Exception as e:
        print(f"Erro na leitura serial: {e}")
    finally:
        if ser.is_open:
            ser.close()
            print("Serial fechada.")

@app.route('/api/bpm')
def api_bpm():
    if ultimo_bpm is not None:
        return jsonify({"bpm": ultimo_bpm, "alert": alerta_ativo})
    else:
        return jsonify({"bpm": None, "message": "Aguardando dados...", "alert": False})

# Rota para cadastrar dados do usuário
@app.route('/api/usuario', methods=['POST'])
def api_usuario():
    data = request.json
    nome = data.get('nome')
    telegram_id = data.get('telegram_id')
    if not nome or not telegram_id:
        return jsonify({"error": "nome e telegram_id são obrigatórios"}), 400
    dados_usuario['nome'] = nome
    dados_usuario['telegram_id'] = telegram_id
    print(f"Dados do usuário atualizados: {dados_usuario}")
    return jsonify({"message": "Dados salvos com sucesso"})

if __name__ == "__main__":
    thread = threading.Thread(target=ler_serial, daemon=True)
    thread.start()
    app.run(debug=True)
