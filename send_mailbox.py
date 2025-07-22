import os
import time
import cv2
import bluetooth
from ev3mailbox import EV3Mailbox
import subprocess  # Para rodar o arquivo send_arduino.py

# Caminho da pasta com as imagens de referência
PATH_IMAGES = 'C:\\Users\\weste\\Documents\\test\\ev3-mailbox-python\\captured_images'

# Limiar mínimo de similaridade para considerar uma detecção (em %)
MIN_DISPLAY_SCORE = 10.0  # agora em 25%

# Número mínimo de frames consecutivos com detecção válida
MIN_CONSECUTIVE_FRAMES = 5

# Tempo em segundos para manter o resultado na tela
DISPLAY_DURATION = 5.0

# Função para enviar número para o EV3
def enviar_numero_ev3(mac_address, mailbox_name, numero, porta=1):
    try:
        sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        sock.connect((mac_address, porta))
        print(f"[OK] Conectado ao EV3: {mac_address}")

        mensagem = EV3Mailbox.encode(mailbox_name, float(numero))  # força float
        sock.send(mensagem.payload)
        print(f"[ENVIADO] {mailbox_name} = {numero} (tipo: {type(numero).__name__})")

    except Exception as e:
        print(f"[ERRO] Falha ao enviar: {e}")

    finally:
        sock.close()
        print("[INFO] Conexão Bluetooth encerrada.")

# Função para carregar as imagens de referência
def load_reference_images(path):
    orb = cv2.ORB_create()
    refs = []
    for filename in os.listdir(path):
        filepath = os.path.join(path, filename)
        img = cv2.imread(filepath, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        kp, des = orb.detectAndCompute(img, None)
        refs.append({
            'name': os.path.splitext(filename)[0],
            'descriptors': des
        })
    return refs, orb

# Função para comparar e calcular a pontuação
def match_and_score(des_ref, des_frame, matcher):
    if des_ref is None or des_frame is None or len(des_ref) == 0:
        return 0.0, 0
    matches = matcher.knnMatch(des_ref, des_frame, k=2)
    good = []
    for pair in matches:
        if len(pair) < 2:
            continue
        m, n = pair
        if m.distance < 0.75 * n.distance:
            good.append(m)
    score = (len(good) / len(des_ref)) * 100
    return score, len(good)

# Função para rodar o script send_arduino.py
def run_send_arduino_script():
    try:
        subprocess.run(['python', 'C:\\Users\\weste\\Documents\\test\\ev3-mailbox-python\\send_arduino.py'], check=True)
        print("Comando 'start' enviado ao Arduino com sucesso!")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao rodar o script send_arduino.py: {e}")
    except Exception as e:
        print(f"Erro inesperado: {e}")

# Função principal de detecção e envio
def main():
    refs, orb = load_reference_images(PATH_IMAGES)
    if not refs:
        print(f'Nenhuma imagem encontrada em "{PATH_IMAGES}".')
        return

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print('Não foi possível acessar a câmera.')
        return

    last_name = None
    consec_count = 0
    showing = False
    show_until = 0.0
    show_text = ''
    frame_idx = 0

    # Defina o MAC address do EV3
    mac_address = '00:16:53:82:0E:20'
    mailbox_name = 'ab'  # Nome do mailbox no EV3

    # Variável para controlar o tempo de envio de comandos
    last_sent_time = 0  # Controle global de tempo
    cooldown_time = 50  # Tempo de cooldown (em segundos) antes de enviar o comando novamente

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, des_frame = orb.detectAndCompute(gray, None)

        now = time.time()

        # Se estivermos exibindo o resultado temporariamente
        if showing:
            cv2.putText(frame, show_text, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            if now >= show_until:
                showing = False
                consec_count = 0
                last_name = None
        else:
            # Detecta melhor match
            best_score = 0.0
            best_name = '—'
            for ref in refs:
                score, _ = match_and_score(ref['descriptors'], des_frame, bf)
                if score > best_score:
                    best_score = score
                    best_name = ref['name']

            # Mostra no terminal o progresso
            print(f"[Frame {frame_idx}] {best_name}: {best_score:.1f}% (consec: {consec_count})")

            # Atualiza contador de frames consecutivos
            if best_score >= MIN_DISPLAY_SCORE and best_name == last_name:
                consec_count += 1
            elif best_score >= MIN_DISPLAY_SCORE:
                consec_count = 1
                last_name = best_name
            else:
                consec_count = 0
                last_name = None

            # Inicia exibição temporizada se atingir o mínimo
            if consec_count >= MIN_CONSECUTIVE_FRAMES:
                show_text = f'{best_name}: {best_score:.1f}%'
                show_until = now + DISPLAY_DURATION
                showing = True

                # Enviar número para o EV3 baseado no nome do arquivo
                if now - last_sent_time >= cooldown_time:
                    if best_name.lower().startswith('quadrado'):
                        print(f"[ENVIADO] Comando para 'quadrado'")
                        enviar_numero_ev3(mac_address, mailbox_name, 0)
                        run_send_arduino_script()  # Rodar o comando para Arduino
                        last_sent_time = now  # Atualiza o tempo de envio

                    elif best_name.lower().startswith('bala'):
                        print(f"[ENVIADO] Comando para 'bala'")
                        enviar_numero_ev3(mac_address, mailbox_name, 1)
                        run_send_arduino_script()  # Rodar o comando para Arduino
                        last_sent_time = now  # Atualiza o tempo de envio

                    elif best_name.lower().startswith('peao'):
                        print(f"[ENVIADO] Comando para 'peao'")
                        enviar_numero_ev3(mac_address, mailbox_name, 2)
                        run_send_arduino_script()  # Rodar o comando para Arduino
                        last_sent_time = now  # Atualiza o tempo de envio

        cv2.imshow('Deteccao de Objetos', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
