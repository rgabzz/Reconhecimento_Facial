import cv2
import mediapipe as mp
from deepface import DeepFace
import os
from datetime import datetime
import json
import time
import math

# --- Utilitários ---
def registrar_log(usuario, status):
    data = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    with open("logs_acessos.csv", "a") as logs:
        logs.write(f"{data}, {usuario}, {status}\n")

def carregar_arquivos(pasta="rostos"):
    with open("usuarios.json", "r") as arq_json:
        dados_json = json.load(arq_json)

    nome_arquivos = [f for f in os.listdir(pasta) if f.lower().endswith((".jpg", ".png"))]
    rostos, nomes = [], []
    for nome_arquivo in nome_arquivos:
        img = cv2.imread(os.path.join(pasta, nome_arquivo))
        if img is None:
            continue
        for usuario in dados_json:
            if usuario["arquivo"] == nome_arquivo:
                nomes.append(usuario["nome"])
                break
        rostos.append(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    return rostos, nomes

# --- Prova de Vida: Movimento de cabeça ---
def calcular_yaw(face_landmarks, iw):
    # Olho esquerdo: ponto 33, olho direito: ponto 263 (MediaPipe)
    left_eye = face_landmarks.landmark[33]
    right_eye = face_landmarks.landmark[263]
    dx = (right_eye.x - left_eye.x) * iw
    return dx

def prova_de_vida_movimento(cam, direcao='direita', timeout=10):
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

    start_time = time.time()
    movimento_detectado = False
    comando_exibido = False
    yaw_inicial = None

    while time.time() - start_time < timeout:
        ret, frame = cam.read()
        if not ret:
            break

        ih, iw = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        if results.multi_face_landmarks:
            face = results.multi_face_landmarks[0]
            yaw = calcular_yaw(face, iw)

            if not comando_exibido:
                texto = f"Vire a cabeça para a {direcao.upper()}"
                cv2.putText(frame, texto, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,255), 2)
                comando_exibido = True
                yaw_inicial = yaw

            if yaw_inicial is not None:
                diferenca = yaw - yaw_inicial
                if direcao == 'direita' and diferenca > 20:
                    movimento_detectado = True
                    break
                elif direcao == 'esquerda' and diferenca < -20:
                    movimento_detectado = True
                    break

        cv2.imshow("Prova de Vida - Movimento", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    face_mesh.close()
    return movimento_detectado

# --- Programa Principal ---
def main():
    rostos_ref, nomes_ref = carregar_arquivos()
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    cam = cv2.VideoCapture(0)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

    cooldown_segundos = 10
    ultimo_reconhecimento = None
    frame_count = 0
    freq_verificacao = 10

    while True:
        ret, frame = cam.read()
        if not ret:
            break

        frame_count += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5)

        reconhecido = False
        nome_reconhecido = "Desconhecido"

        if len(faces) > 0 and frame_count % freq_verificacao == 0:
            x, y, w, h = faces[0]
            rosto_rgb = cv2.cvtColor(frame[y:y+h, x:x+w], cv2.COLOR_BGR2RGB)
            agora = datetime.now()

            if ultimo_reconhecimento is None or (agora - ultimo_reconhecimento).total_seconds() > cooldown_segundos:
                for i, rosto_ref in enumerate(rostos_ref):
                    try:
                        cv2.imwrite("temp1.jpg", cv2.cvtColor(rosto_rgb, cv2.COLOR_RGB2BGR))
                        cv2.imwrite("temp2.jpg", cv2.cvtColor(rosto_ref, cv2.COLOR_RGB2BGR))
                        result = DeepFace.verify(img1_path="temp1.jpg", img2_path="temp2.jpg", enforce_detection=False)

                        if result["verified"]:
                            nome_reconhecido = nomes_ref[i]
                            print(f"Rosto reconhecido: {nome_reconhecido}")

                            if prova_de_vida_movimento(cam, direcao="direita"):
                                print("Movimento confirmado ✅")
                                registrar_log(nome_reconhecido, "LIBERADO")
                                reconhecido = True
                                ultimo_reconhecimento = agora
                            else:
                                print("Movimento NÃO detectado ❌")
                                registrar_log(nome_reconhecido, "NEGADO - sem movimento")
                            break
                    except Exception as e:
                        print(f"Erro DeepFace: {e}")

                if not reconhecido:
                    registrar_log("Desconhecido", "NEGADO")

        cor = (0,255,0) if reconhecido else (0,0,255)
        texto = f"Acesso: {nome_reconhecido}" if reconhecido else "Acesso Negado"
        for (x1, y1, w1, h1) in faces:
            cv2.rectangle(frame, (x1, y1), (x1+w1, y1+h1), cor, 2)
        cv2.putText(frame, texto, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, cor, 2)

        cv2.imshow("Reconhecimento Facial Seguro", frame)

        if reconhecido:
            time.sleep(3)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    cam.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()