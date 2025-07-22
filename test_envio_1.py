import sys
import bluetooth
from ev3mailbox import EV3Mailbox

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

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso: python enviar.py <MAC> <mailbox> <numero>")
        print("Exemplo: python enviar.py 00:16:53:82:0E:20 contador 10")
        sys.exit(1)

    mac = sys.argv[1]
    mailbox = sys.argv[2]
    numero = sys.argv[3]

    enviar_numero_ev3(mac, mailbox, numero)


# python send_mailbox.py 00:16:53:82:0E:20 contador 10