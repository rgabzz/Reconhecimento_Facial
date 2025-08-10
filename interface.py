from tkinter import *
from tkinter import simpledialog, messagebox, Scrollbar
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash
import cv2
from datetime import datetime
from deepface import DeepFace

# Inicializa o backend usado pela DeepFace (pode ser 'retinaface', 'mtcnn', etc)
backend = 'opencv'  # Usamos 'opencv' por ser leve e rápido

# Criação da janela principal
janela = Tk()
janela.geometry('350x400')
janela.title('Administrador - Fechadura Facial')

# Geração da senha (criptografada) para login
PASSWORD = generate_password_hash("1234")

# Função que carrega a lista de usuários a partir de um arquivo JSON
def carregar_usuarios_json():
    if not os.path.exists('usuarios.json'):
        return []
    try:
        with open('usuarios.json', "r") as arq:
            return json.load(arq)
    except:
        return []

# Função que salva a lista de usuários no arquivo JSON
def salvar_usuarios(usuarios):
    with open('usuarios.json', "w") as arq:
        return json.dump(usuarios, arq, indent=4)

# Função que detecta o rosto no frame, recorta e salva apenas o rosto
def detectar_rosto_e_salvar(frame, nome_arquivo):
    try:
        # Usa DeepFace para extrair rostos do frame
        faces = DeepFace.extract_faces(img_path=frame, detector_backend='opencv', enforce_detection=True)

        # Se não encontrar rostos, retorna False
        if not faces:
            return False

        # Pega o primeiro rosto detectado
        rosto = faces[0]['face']

        # Se a imagem estiver em float (0 a 1), converte para 8 bits (0 a 255)
        if rosto.dtype != 'uint8':
            rosto = (rosto * 255).astype('uint8')

        # Converte de RGB para BGR (formato padrão do OpenCV)
        rosto = cv2.cvtColor(rosto, cv2.COLOR_RGB2BGR)

        # Define caminho de salvamento e salva imagem do rosto
        caminho_imagem = os.path.join('rostos', nome_arquivo)
        cv2.imwrite(caminho_imagem, rosto)
        return True

    except Exception as e:
        print(f"[ERRO AO DETECTAR ROSTO]: {e}")
        return False

# Função que permite cadastrar um novo rosto
def cadastrarRosto():
    # Solicita o nome do usuário
    nome = simpledialog.askstring("Cadastro", "Digite o nome do usuário a ser adicionado: ")

    # Verifica se o nome não está vazio
    if not nome:
        messagebox.showwarning("Aviso", "O nome do usuário não pode ser vazio")
        return

    # Carrega a lista de usuários existente
    usuarios = carregar_usuarios_json()

    try:
        cam = cv2.VideoCapture(0)  # Tenta abrir a webcam
    except:
        messagebox.showerror("Erro", "Não foi possível acessar a webcam")
        return

    messagebox.showinfo("Instruções", "Aperte espaço para capturar a foto e ESC para cancelar") 

    # Loop de captura da câmera
    while True:
        ret, frame = cam.read()
        if not ret:
            messagebox.showerror("Erro", "Falha ao capturar imagem")
            cam.release()
            return

        # Exibe o frame ao vivo
        cv2.imshow("Captura de rosto - pressione espaço para foto", frame)

        tecla = cv2.waitKey(1)
        if tecla == 27:  # Tecla ESC para cancelar
            cam.release()
            cv2.destroyAllWindows()
            return
        
        elif tecla == 32:  # Tecla ESPAÇO tira a foto

            # Gera nome único para o arquivo da imagem
            data_atual = datetime.now().strftime("%Y%m%d%H%M%S")
            nome_arquivo = f'{nome}_{data_atual}.jpg'

            # Garante que a pasta 'rostos' exista
            if not os.path.exists('rostos'):
                os.makedirs('rostos')

            # Tenta detectar o rosto e salvar
            sucesso = detectar_rosto_e_salvar(frame, nome_arquivo)
            cam.release()
            cv2.destroyAllWindows()

            # Se não conseguir detectar o rosto
            if not sucesso:
                messagebox.showerror("Erro", "Nenhum rosto detectado. Tente novamente!")
                return

            # Cria o dicionário do novo usuário e salva
            usuario_novo = {
                "nome": nome,
                "arquivo": nome_arquivo
            }

            # Adiciona o usuário na lista de usuários
            usuarios.append(usuario_novo)

            # Salva os usuários atuais
            salvar_usuarios(usuarios)

            messagebox.showinfo("Sucesso", f"Usuário {nome} cadastrado com sucesso!")
            carregar_usuarios_janela()
            return

# Função para remover rosto selecionado da lista
def removerRosto():

    # Verifica qual usuário foi selecionado
    selecionado = lista_usuarios.curselection()
    if not selecionado:
        messagebox.showwarning("Aviso", "Selecione um usuário para excluir")
        return

    # Pega as informações desse usuário
    index = selecionado[0]
    usuarios = carregar_usuarios_json()
    usuario_remover = usuarios[index]

    # Confirmação antes de excluir
    confirm = messagebox.askyesno("Confirmação", f"Excluir usuário {usuario_remover['nome']}?")
    if not confirm:
        return

    # Remove a imagem do rosto se existir
    caminho_imagem = os.path.join('rostos', usuario_remover["arquivo"])
    if os.path.exists(caminho_imagem):
        os.remove(caminho_imagem)

    # Remove o usuário do JSON
    usuarios.pop(index)

    # Salva os usuários sem o usuário excluido
    salvar_usuarios(usuarios)
    messagebox.showinfo("Sucesso", "Usuário excluído com sucesso!")
    carregar_usuarios_janela()

# Atualiza a listbox com os usuários salvos
def carregar_usuarios_janela():
    lista_usuarios.delete(0, END)
    usuarios = carregar_usuarios_json()
    for usuario in usuarios:
        lista_usuarios.insert(END, usuario['nome'])

# Tela de login: pede a senha do administrador
def pedir_senha():

    # Cria tela pra escrever a senha
    senha = simpledialog.askstring("Login", "Digite a senha de administrador", show='*')

    # Faz a verificação da senha
    if senha is None:
        janela.destroy()
        return
    
    if check_password_hash(PASSWORD, senha):
        principal()
        
    else:
        messagebox.showerror("Erro", "Credencial Incorreta!")
        janela.after(100, pedir_senha)

# Interface principal do sistema (após login)
def principal():

    # Limpa os widgets antigos da janela
    for _ in janela.winfo_children():
        _.destroy()

    # Título
    Label(janela, text="Sistema de Gerenciamento de Rostos", font="Ivy 14").place(x=10, y=10)

    # Botão para cadastrar novo rosto
    Button(janela, text="Cadastrar Rosto", font="Ivy 10", command=cadastrarRosto, width=12).place(x=15, y=60)

    # Botão para remover rosto selecionado
    Button(janela, text="Remover Rosto", font="Ivy 10", command=removerRosto, width=12).place(x=225, y=60)

    # Lista de usuários cadastrados
    global lista_usuarios
    lista_usuarios = Listbox(janela, height=15, width=35)
    lista_usuarios.place(x=65, y=120)

    # Scrollbar para a lista
    scroll = Scrollbar(janela)
    scroll.place(x=290, y=120, height=245) 
    lista_usuarios.config(yscrollcommand=scroll.set)
    scroll.config(command=lista_usuarios.yview)

    # Carrega os usuários na lista
    carregar_usuarios_janela()

# Inicia pedindo a senha assim que o programa abre
janela.after(100, pedir_senha)

# Inicia o loop principal da janela Tkinter
janela.mainloop()
