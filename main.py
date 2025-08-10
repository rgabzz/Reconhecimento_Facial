# Importação das Bíbliotecas necessárias para funcionamento do sistema
import cv2
from deepface import DeepFace
import os
from datetime import datetime
import json
import time
import serial
from scipy.spatial.distance import cosine

#Definição da porta serial
porta_serial = serial.Serial("COM5", 9600)
time.sleep(2)

# Função que registra os logs de funcionamento da porta
def registrar_log(usuario, status):
    # Data e Hora atuais
    data = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # Abre o arquivo e registra o log, de acordo com a predefinição que fizemos
    with open("logs_acessos.csv", "a") as logs:
        logs.write(f"{data}, {usuario}, {status}\n")

# Carrega os rostos para comparação
def carregar_arquivos(pasta="rostos"):

    # Abre o arquivo json e pega os usuários que estão lá
    try:
        with open("usuarios.json", "r") as arq_json:
            dados_json = json.load(arq_json)
    except:
        print('Arquivo Vazio')
        dados_json = []

    #
    embeddings, nomes = [], []
    for usuario in dados_json:
        # Monta o caminho completo da imagem do rosto do usuário
        caminho = os.path.join(pasta, usuario["arquivo"])

         # Se o arquivo da imagem não existir, pula para o próximo usuário
        if not os.path.exists(caminho): 
            continue
        
        # Aqui pegamos a foto do rosto e pedimos pro FaceNet512 transformar ela em um "código de números" que descreve o formato e os traços dessa pessoa.
        # É como se fosse a identidade digital do rosto.
        # O enforce_detection=True significa que, se não tiver rosto na imagem, o programa vai parar e avisar.
        try:
            representacao = DeepFace.represent(
                img_path=caminho,
                model_name="Facenet512",
                enforce_detection=True
            )[0]["embedding"]
            
            # Adicionamos essa identidade digital do rosto, na pasta delas
            embeddings.append(representacao)
            
            # Adiciona o nome do usuário à lista de nomes
            nomes.append(usuario["nome"])

        # Caso haja algum erro (imagem corrompida, sem rosto, etc.), imprime a mensagem de erro
        except Exception as e:
            print(f"Erro ao processar {usuario['arquivo']}: {e}")

    # Se a lista embeddings termianr vazia após o loop, mostra que nenhuma imagem válida foi encontrada
    if not embeddings:
        print('Nenhuma imagem válida encontrada')
        exit()

    # Retornar as imagens e o nome de cada usuário pra aquela imagem
    return embeddings, nomes

def main():
    # Pega os rostos e as fotos, da função "carregar_arquivos"
    rostos_ref, nomes_ref = carregar_arquivos()

    # Carrega um "detector de rostos" pronto, que já sabe encontrar rostos de frente em uma imagem.
    # Esse detector vem no OpenCV e usa um método chamado Haar Cascade.
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    
    # Define a câmera e sua resolução
    cam = cv2.VideoCapture(0)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # Variáveis usadas durante o loop para cooldown do sistema
    cooldown_segundos = 10
    ultimo_reconhecimento = None
    freq_verificacao = 10
    frame_count = 0

    print("Iniciando reconhecimento facial. Pressione ESC para sair.")

    # Loop Infinito que faz o funcionamento do sistema
    while True:

        # Funcionamento da câmera e frame capturado da câmera
        ret, frame = cam.read()
        
        # Se não der certo a captura do frame
        if not ret:
            print('Erro ao acessar a webcam')
            break

        # Detecta rostos na imagem convertida para tons de cinza
        faces = face_cascade.detectMultiScale(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), 1.1, 5)
        frame_count += 1 

        # Variável para saber se o rosto foi reconhecido no frame atual
        reconhecido = False

        # Nome padrão caso ninguém seja reconhecido
        nome_reconhecido = "Desconhecido"

        # Se detectou pelo menos um rosto e já se passaram 10 frames
        if len(faces) > 0 and frame_count % freq_verificacao == 0: 

            x, y, w, h = faces[0] # Pega as coordenadas do primeiro rosto detectado (posição e tamanho)

             # Tamanho mínimo de largura e altura para considerar o rosto válido
            MIN_LARGURA = 100
            MIN_ALTURA = 100

            # Ignora rostos que estão muito pequenos na imagem
            if w < MIN_LARGURA or h < MIN_ALTURA:
                print(f"Rosto ignorado (muito pequeno - {w}x{h} px)")


            else:

                # Recorta o rosto da imagem original e converte para RGB, formato esperado pelo DeepFace
                rosto_capturado = cv2.cvtColor(frame[y:y+h, x:x+w], cv2.COLOR_BGR2RGB)
                agora = datetime.now() # Pega a data e hora atuais

                # Se for o primeiro reconhecimento ou o ultimo reconhecimento tiver sido feito em 10 segundos
                if (ultimo_reconhecimento is None) or ((agora-ultimo_reconhecimento).total_seconds() > cooldown_segundos):
                    try:

                        # Pegamos a identidade digital do rosto capturado pela câmera
                        embedding_capturado = DeepFace.represent(
                            rosto_capturado, model_name="Facenet512", enforce_detection=False
                        )[0]["embedding"]

                        # Compara o rosto capturado com todos os rostos de referência já cadastrados
                        for i, emb_ref in enumerate(rostos_ref):

                            # Pega a distância atual do rosto capturado
                            distancia = cosine(embedding_capturado, emb_ref)
                            # print(f"Distância até {nomes_ref[i]}: {distancia:.4f}")  # debug

                            # Se a distância for pequena, não abre o reconhecimento
                            if distancia < 0.25:

                                # Altera as váriaveis usadas no sistema
                                reconhecido = True
                                nome_reconhecido = nomes_ref[i]
                                ultimo_reconhecimento = agora

                                # Diz de quem foi o rosto reconhecido e registra o log
                                print(f'Rosto Reconhecido: {nome_reconhecido}')
                                registrar_log(usuario=nome_reconhecido, status='LIBERADO')

                                # Abre a Porta
                                print('Abrindo Porta...')
                                porta_serial.write(b'A') # (Envia sinal pro arduíno)

                                time.sleep(8) # Espera a porta abrir e a pessoa entrar

                                # Fecha a porta e passa para o próximo reconhecimento facial
                                print("Fechando porta.")
                                porta_serial.write(b'C') # (Envia sinal pro arduíno)

                                break # Sai do loop de comparação de rostos
                        
                        # Se o rosto não for reconhecido
                        if not reconhecido:
                            # Registra o log de que alguém desconhecido tentou abrir a porta
                            registrar_log(usuario="Desconhecido", status="NEGADO")
                            print(f'Rosto não reconhecido')
                            porta_serial.write(b'F') # (Envia sinal pro arduíno)

                    # Caso dê erro na extração do vetor, mostra mensagem
                    except Exception as erro:
                        print(f'Erro ao representar rosto: {erro}')

        # Define a cor da borda do rosto e texto na tela (verde se reconhecido, vermelho se não)
        cor = (0, 255, 0) if reconhecido else (0, 0, 255)
        texto = f"Acesso: {nome_reconhecido}" if reconhecido else "Acesso Negado"

        # Desenha um retângulo em volta de cada rosto detectado na imagem
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), cor, 2)

        # Exibe o texto do resultado (nome ou "Acesso Negado") no topo da janela
        cv2.putText(frame, texto, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, cor, 2)

        # Mostra a janela com o vídeo e as marcações
        cv2.imshow("Reconhecimento Facial", frame)

        # Ao apertar a tecla ESC fecha o programa
        if cv2.waitKey(1) == 27:  
            break

    # Quando finaliza o programa, fecha a câmera
    cam.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()