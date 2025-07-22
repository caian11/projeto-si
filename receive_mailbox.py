import bluetooth
import struct
from ev3mailbox import EV3Mailbox

def recv_all(sock, size):
    data = b''
    while len(data) < size:
        more = sock.recv(size - len(data))
        if not more:
            raise ConnectionError("Conexão encerrada inesperadamente.")
        data += more
    return data

def format_value(value):
    """
    Converte floats inteiros para int, mantém outros tipos
    """
    if isinstance(value, float) and value.is_integer():
        return int(value), 'int'
    return value, type(value).__name__

# Substitua com o MAC do seu EV3
EV3_MAC = '00:16:53:82:0E:20'
PORT = 1

sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
sock.connect((EV3_MAC, PORT))
print("Conectado ao EV3, aguardando mensagens...")

try:
    while True:
        # Lê os 2 primeiros bytes do header
        header = recv_all(sock, 2)
        size = int.from_bytes(header, byteorder='little')
        print(f"[DEBUG] Tamanho esperado: {size} bytes")

        # Lê o corpo da mensagem
        body = recv_all(sock, size - 2)
        payload = header + body

        print(f"[DEBUG] Bytes recebidos: {len(payload)}")
        print("[DEBUG] Payload bruto:", ' '.join(f'{b:02x}' for b in payload))

        # Decodificação robusta com padding automático
        try:
            mailbox = EV3Mailbox.decode(payload)
        except struct.error as e:
            if "unpack_from requires a buffer of at least" in str(e):
                print("[WARN] Payload incompleto. Aplicando padding com 0x00...")
                expected_len = int(str(e).split("at least ")[1].split(" ")[0])
                padding_needed = expected_len - len(payload)
                payload += b'\x00' * padding_needed
                mailbox = EV3Mailbox.decode(payload)
            else:
                raise

        # Formata o valor para exibição
        value, tipo = format_value(mailbox.value)

        if isinstance(value, str):
            print(f"[RECEBIDO] {mailbox.name} = \"{value}\" (tipo: {tipo})")
        else:
            print(f"[RECEBIDO] {mailbox.name} = {value} (tipo: {tipo})")

except KeyboardInterrupt:
    print("\nEncerrado pelo usuário.")
except Exception as e:
    print(f"[ERRO] {e}")
finally:
    sock.close()
