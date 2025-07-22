import sys
import serial
from ev3mailbox import EV3Mailbox

def enviar_numero_ev3_serial(porta_serial, mailbox_name, numero, baudrate=57600):
    try:
        ser = serial.Serial(porta_serial, baudrate, timeout=1)
        print(f"[OK] Conectado ao EV3 via USB: {porta_serial}")

        mensagem = EV3Mailbox.encode(mailbox_name, float(numero))
        ser.write(mensagem.payload)
        print(f"[ENVIADO] {mailbox_name} = {numero} (tipo: {type(numero).__name__})")

    except Exception as e:
        print(f"[ERRO] Falha ao enviar: {e}")

    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("[INFO] Conexão Serial encerrada.")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso: python enviar.py <COMx> <mailbox> <numero>")
        print("Exemplo: python enviar.py COM3 contador 10")
        sys.exit(1)

    porta_serial = sys.argv[1]
    mailbox = sys.argv[2]
    numero = sys.argv[3]

    enviar_numero_ev3_serial(porta_serial, mailbox, numero)