from tkinter import *
from tkinter import simpledialog, messagebox,Scrollbar
import json
import os
from werkzeug.security import generate_password_hash,check_password_hash
import cv2
from datetime import datetime

# Criação da Janela
janela = Tk()
janela.geometry('350x400')
janela.title('Administrador - Fechadura Facial')

# SENHA ATUAL
PASSWORD = generate_password_hash("1234")

# Funções json
def carregar_usuarios_json():
    # Verifica se o arquivo do json existe, se não existir retorna uma lista vazia
    if not os.path.exists('usuarios.json'):
        return []
    
    # Abre o json atual, e transforma em um objeto python
    with open('usuarios.json', "r") as arq:
        return json.load(arq)

def salvar_usuarios(usuarios):
    # Reescreve o json, com a nova lista passada
    with open('usuarios.json', "w") as arq:
        return json.dump(usuarios,arq,indent=4)

# Funções para os widgets
def cadastrarRosto():
    # Nome do usuário a ser adicionado
    nome = simpledialog.askstring("Cadastro", "Digite o nome do usuário a ser adicionado: ")

    # Verifica se não está vazio
    if not nome:
        messagebox.showwarning("Aviso", "O nome do usuário não pode ser vazio")
        return
    
    # Carrega a lista de usuarios e pega o nome deles
    usuarios = carregar_usuarios_json()
    nomes = []
    for usuario in usuarios:
        nomes.append(usuario['nome'])

    # Tenta abrir a câmera
    try:
        cam = cv2.VideoCapture(0)
    except:
        messagebox.showerror("Erro", "Não foi possível acessar a webcam")
        return
    
    messagebox.showinfo("Instruções", "Aperte espaço para capturar a foto e ESC para cancelar") 

    while True:
        # Leitura da câmera aberta
        ret,frame = cam.read()

        # Se ret retorna false, significa que não foi possível ler a camera
        if not ret:
            messagebox.showerror("Erro", "Falha ao capturar imagem")
            cam.release()
            return
        
        cv2.imshow("Captura de rosto - pressione espaço para foto", frame)

        # Se o usuário aperta ESC, fecha a câmera
        if cv2.waitKey(1) == 27:
            cam.release()
            cv2.destroyAllWindows()
            return
        
        # Se ele aperta ESPAÇO, tira a foto e salva ela
        elif cv2.waitKey(1) == 32:
            # Formata o nome do arquivo no padrão
            data_atual = datetime.now().strftime("%Y%m%d%H%M%S")
            nome_arquivo = f'{nome}_{data_atual}.jpg'
            
            # Pega o caminho da imagem, e salva a foto com o nome do arquivo no caminho citado
            caminho_imagem = os.path.join('rostos',nome_arquivo)
            cv2.imwrite(caminho_imagem,frame)
            cam.release()
            cv2.destroyAllWindows()

            # Cria o usuário novo, adiciona ele e recarrega a lista de usuários
            usuario_novo = {
                "nome": nome,
                "arquivo" : nome_arquivo
            }

            usuarios.append(usuario_novo)
            salvar_usuarios(usuarios)

            messagebox.showinfo("Sucesso", f"Usuário {nome} cadastrado com sucesso!")
            carregar_usuarios_janela()
            return

def removerRosto():
    # Pega o usuário que foi selecionado
    selecionado = lista_usuarios.curselection()
    if not selecionado:
        messagebox.showwarning("Aviso", "Selecione um usuário para excluir")
        return
    
    # Caso tenha selecionado mais de um, pega apenas o primeiro
    index = selecionado[0]

    # Lista de usuários atual
    usuarios = carregar_usuarios_json()

    # Usuário atual
    usuario_remover = usuarios[index]

    confirm = messagebox.askyesno("Confirmação", f"Excluir usuário {usuario_remover['nome']}?")
    if not confirm:
        return

    # Pega o nome do arquivo da foto do usuário, verifica sua existência e remove ele
    caminho_imagem = os.path.join('rostos',usuario_remover    ["arquivo"])
    if os.path.exists(caminho_imagem):
        os.remove(caminho_imagem)

    # Remove o usuário da lista e salva a lista nova, sem o usuário no json
    usuarios.pop(index)
    salvar_usuarios(usuarios)
    messagebox.showinfo("Sucesso", "Usuário excluído com sucesso!")

    # Recarrega a nova lista
    carregar_usuarios_janela()


def carregar_usuarios_janela():
    # Deleta os valores que estavam na antiga ListBox
    lista_usuarios.delete(0,END)

    # Adiciona novos valores a ListBox baseado no json
    usuarios = carregar_usuarios_json()
    for usuario in usuarios:
        lista_usuarios.insert(END,usuario['nome'])


# Tela De Senha
def pedir_senha():
    # Cria uma mini tela para pedir a senha, verifica se a senha digitada esta correta, se sim passa para tela principal, se não pede novamente a senha

    senha = simpledialog.askstring("Login", "Digite a senha de administrador", show='*')

    if senha is None:
        janela.destroy()
        return

    if check_password_hash(PASSWORD, senha):
        principal()

    else:
        messagebox.showerror("Erro", "Credencial Incorreta!")
        janela.after(100,pedir_senha)

# Tela Principal
def principal():
    # Limpar a Tela
    for _ in janela.winfo_children():
        _.destroy()
    
    # Criação dos Widgets
    Label(janela,text="Sistema de Gerenciamento de Rostos",font="Ivy 14").place(x=10,y=10)

    Button(janela,text="Cadastrar Rosto",font="Ivy 10",command=cadastrarRosto,width=12).place(x=15,y=60)

    Button(janela,text="Remover Rosto",font="Ivy 10",command=removerRosto,width=12).place(x=225,y=60)
    
    # Criação da ListBox, onde fica a lista de usuários
    global lista_usuarios
    lista_usuarios = Listbox(janela,height=15,width=35)
    lista_usuarios.place(x=65,y=120)

    # Atualizar dps
    scroll = Scrollbar(janela)
    scroll.place(x=290, y=120, height=245) 
    lista_usuarios.config(yscrollcommand=scroll.set)
    scroll.config(command=lista_usuarios.yview)

    carregar_usuarios_janela()

# Abre a tela de senha, assim que o comando inicia
janela.after(100,pedir_senha)

janela.mainloop()