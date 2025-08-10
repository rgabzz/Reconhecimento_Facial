
'''
Esse código tem objetivo único de testar o arduíno sem precisar do reconhecimento facial.
Ele envia os 3 tipos de sinais que o arduíno pode receber, para teste de funcionamento de cada uma das opções.
'''

import serial
import time

# Ajuste a porta serial do seu Arduino
porta_serial = 'COM5'  
baud_rate = 9600    

try:
    arduino = serial.Serial(porta_serial, baud_rate, timeout=1)
    time.sleep(2)  # espera Arduino reiniciar

    while True:
        print("\nComandos:")
        print("1 - Acesso Liberado ('A')")
        print("2 - Acesso Negado ('F')")
        print("3 - Fechar Porta ('C')")
        print("4 - Sair")   
        escolha = input("Escolha: ")

        if escolha == '1':
            arduino.write(b'A')
            print("Enviado: Acesso Liberado ('A')")
        elif escolha == '2':
            arduino.write(b'F')
            print("Enviado: Acesso Negado ('F')")
        elif escolha == '3':
            arduino.write(b'C')
            print("Enviado: Fechar Porta ('C')")
        elif escolha == '4':
            print("Saindo...")
            break
        else:
            print("Opção inválida.")

except serial.SerialException:
    print(f"Erro ao abrir porta {porta_serial}")
except KeyboardInterrupt:
    print("\nPrograma interrompido pelo usuário.")
finally:
    if 'arduino' in locals() and arduino.is_open:
        arduino.close()