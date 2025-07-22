#!/usr/bin/env python3
"""
Script simples para enviar comando 'start' via porta serial
"""
import serial
import time


def send_start_command(port="COM3", baudrate=9600):
    """
    Função para enviar comando 'start' pela porta serial
    """
    try:
        # Conectar à porta serial
        ser = serial.Serial(port, baudrate, timeout=1)
        print(f"Conectado à porta {port}")

        # Aguardar estabilização
        time.sleep(0.5)

        # Enviar comando 'start'
        command = "start\n"
        ser.write(command.encode("utf-8"))
        print("Comando 'start' enviado")

        # Fechar conexão
        ser.close()
        print("Conexão fechada")

    except serial.SerialException as e:
        print(f"Erro na comunicação serial: {e}")
    except Exception as e:
        print(f"Erro: {e}")


def main():
    send_start_command()


if __name__ == "__main__":
    main()