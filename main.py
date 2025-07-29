import cv2
from deepface import DeepFace
import os
from datetime import datetime
import json
import time
import serial

porta_serial = serial.Serial("COM5", 9600)  # 9600 é a taxa padrão do Arduino
time.sleep(2)  # Espera o Arduino resetar

def registrar_log(usuario, status):
    # Pegamos a data e o horário atual de hoje
    data = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # Registramos no log: a data, o usuario, e se ele abriu ou não a fechadura
    # Se o usuario não estiver cadastrado será Desconhecido
    with open("logs_acessos.csv", "a") as logs:
        logs.write(f"{data}, {usuario}, {status}\n")

def carregar_arquivos(pasta="rostos"):
    try:
        # Pegamos os dados do json, onde tem as pessoas cadastradas
        with open("usuarios.json", "r") as arq_json:
            dados_json = json.load(arq_json)
    except:
        print('Arquivo Vazio')

    # Pegamos o nome dos arquivos dentro da pasta
    nome_arquivos = []
    for arquivo in os.listdir(pasta):
        # Se o nome do arquivo terminar com jpg ou png
        if arquivo.lower().endswith((".jpg",".png")):
            nome_arquivos.append(arquivo)
    
    rostos,nomes = [],[] # Criamos as listas onde estão os nomes, e as imagens dos rostos

    # Pega os arquivos
    for nome_arquivo in nome_arquivos:
        # Carrega a imagem do arquivo, pelo caminho
        img = cv2.imread(os.path.join(pasta, nome_arquivo))

        # Verifica se tem algo no arquivo, se n passa pro proximo arquivo
        if img is None:
            print(f"Não foi possível carregar: {nome_arquivo}")
            continue

        # Se o nome do arquivo, for igual ao nome q esta no json, pega o nome do usuario
        for usuario in dados_json:
            if usuario["arquivo"] == nome_arquivo:
                nomes.append(usuario["nome"])
                break
        
        # Adiciona o rosto se for possível carregá-lo
        rostos.append(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    

    # Se a pastas rostos estiver vazia
    if not rostos: 
        print('Nenhuma imagem válida encontrada')
        exit() # Para o programa

    return rostos,nomes

def main():
    rostos_ref, nomes_ref = carregar_arquivos()
    
    # Carrega o classificador Haar Cascade pré-treinado para detecção de rostos frontais
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    # Possível câmera que poderá ser utilizada
    # CAMERA_URL = "http://10.176.4.53:8080/video"

    # Define a câmera, e configura o tamanho do frame que será mostrado ao usuário.
    cam = cv2.VideoCapture(0)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    cooldown_segundos = 10  # intervalo mínimo entre reconhecimentos
    ultimo_reconhecimento = None # defini a variavel do ultimo reconhecimento, usada na logica do cooldown
    freq_verificacao = 10  # frequência da verificação (a cada 10 frames)
    frame_count = 0        # contador dos frames processados desde o início

    print("Iniciando reconhecimento facial. Pressione ESC para sair.")

    while True:
        ret, frame = cam.read()

        # Verifica se ret retorna false, isso significa que não foi possível acessar a webcam
        if not ret:
            print('Erro ao acessar a webcam')
            break

        # Detecta rostos na camera convertida para escala de cinza usando o classificador em cascata Haar
        faces = face_cascade.detectMultiScale(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), 1.1, 5)

        # Contador de frames
        frame_count += 1

        # Cria variáveis usadas futuramente, para verificação e update do log
        reconhecido = False
        nome_reconhecido = "Desconhecido"

        # Se tiver alguma face verificada e se esta dentro da contagem de 10 frames
        if len(faces) > 0 and frame_count % freq_verificacao == 0:
            
            # Pega os pontos do rosto do rosto detectado
            x, y, w, h = faces[0]

            # Recorta a região do rosto da imagem original (colorida) e converte para RGB para uso posterior
            rosto_capturado = cv2.cvtColor(frame[y:y+h, x:x+w], cv2.COLOR_BGR2RGB)

            # Marca o momento atual
            agora = datetime.now()

            # Se o ultimo reconhecimento estiver dentro do cooldown estabelecido, ou for a primeira vez rodando o código
            if (ultimo_reconhecimento is None) or ((agora-ultimo_reconhecimento).total_seconds() > cooldown_segundos):

                # Loop sobre a lista de rostos que temos
                for i, rosto_ref in enumerate(rostos_ref):
                    try:
                        # Faz a verificação se o rosto atual é igual a algum dos rostos armazenados
                        if DeepFace.verify(img1_path=rosto_capturado,img2_path=rosto_ref, enforce_detection=False, model_name="Facenet")["verified"]:

                            # Atualiza o status de reconhecido e salva o nome
                            reconhecido = True
                            nome_reconhecido = nomes_ref[i]

                            # Define o ultimo reconhecimento para agora, para que o cooldown funcione
                            ultimo_reconhecimento = agora

                            # Exibi no console de quem é o rosto reconhecido
                            print(f'Rosto Reconhecido:{nome_reconhecido}')

                            # Registra no arquivo que o usuário reconhecido abriu a porta
                            registrar_log(usuario=nome_reconhecido,status='LIBERADO')

                            print('Abrindo Porta...')
                            porta_serial.write(b'A')

                            time.sleep(5)
                            print("Fechando porta.")
                            porta_serial.write(b'F')    

                            # Quebra o loop, pois já encontrou o rosto
                            break

                    # Se houve algum erro, exibi-o
                    except Exception as erro:
                        print(f'Erro na verificação {erro}')

                # Se o rosto não for reconhecido, registra no log que um rosto não reconhecido tentou utilizar
                # o metódo de reconhecimento da fechadura
                if not reconhecido:
                    registrar_log(usuario="Desconhecido",status="NEGADO")
                    print(f'Rosto não reconhecido')

        # Define a cor que vai aparecer na tela do notebook, que mostra a câmera
        # Se o usuário for reconhecido fica verde, caso não, fica vermelho
        cor = (0,0,0)
        if reconhecido:
            cor = (0, 255, 0)
        else:
            cor = (0, 0, 255)

        # Cria um texto que fica no canto da tela do notebook, que mostra se o usuário tem acesso negado ou não
        if reconhecido:
            texto = f"Acesso: {nome_reconhecido}"
        else:
            texto = "Acesso Negado"


        # Cria um retângulo ao redor do rosto, de acordo com a variável cor
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), cor, 2)

        # Coloca e posiciona o texto, citado anteriormente
        cv2.putText(frame, texto, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, cor, 2)

        # Mostra o que está aparecendo na webcam, em uma tela de frame
        cv2.imshow("Reconhecimento Facial", frame)

        # Se a tecla 27 (ESC) for pressionada, fecha o programa
        if cv2.waitKey(1) == 27:  
            break

    cam.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()