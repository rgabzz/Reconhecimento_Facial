# Sistema de Fechadura Facial com Reconhecimento Facial

Este projeto implementa um sistema básico de fechadura facial que utiliza reconhecimento facial para liberar ou negar o acesso. O sistema captura imagens via webcam, compara com rostos previamente cadastrados e registra logs das tentativas de acesso.

---

## Funcionalidades

- Cadastro de rostos através da webcam.
- Remoção de rostos cadastrados.
- Reconhecimento facial em tempo real utilizando a webcam.
- Registro de logs das tentativas de acesso (liberado ou negado) com data e hora.
- Interface simples com Tkinter para gerenciamento dos usuários.

---

## Como funciona

1. **Cadastro:** O usuário cadastra o rosto com nome e foto tirada pela webcam. A foto é salva na pasta `rostos` e as informações no arquivo `usuarios.json`.

2. **Reconhecimento:** O sistema usa a webcam para detectar rostos em tempo real e compara com os rostos cadastrados usando a biblioteca DeepFace.

3. **Acesso:** Se o rosto for reconhecido, o acesso é liberado e registrado no arquivo `logs_acessos.csv`. Caso contrário, o acesso é negado e também registrado.

---

## Requisitos

- Python 3.10.11
- Biblioteca DeepFace
- OpenCV
- Tkinter (geralmente já vem com Python)
- Werkzeug (para hashing de senhas)

---

## Instalação

1. Clone este repositório ou faça o download dos arquivos.

2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Certifique-se que as pastas `rostos` e o arquivo `usuarios.json` existam (pode criar manualmente se necessário).

---

## Como usar

- Execute o script principal com:

```bash
python interface.py
```

- Insira a senha de administrador padrão `1234` para acessar o sistema.

- Use os botões para cadastrar ou remover rostos.

- O reconhecimento facial será ativado para liberar acesso.

---

## Estrutura dos arquivos

- `interface.py`: Interface gráfica para cadastro e gerenciamento dos usuários.
- `usuarios.json`: Arquivo JSON que armazena os dados dos usuários cadastrados.
- `rostos/`: Pasta onde são salvas as imagens dos rostos capturados.
- `logs_acessos.csv`: Arquivo de log com data, usuário e status (LIBERADO ou NEGADO).

---

---

## Observações

- Este sistema é um projeto básico para fins didáticos e prototipagem.

- Para uso em produção, considere implementar verificações adicionais para evitar fraudes (ex: spoofing com fotos).

---

Se precisar de ajuda ou quiser contribuir, fique à vontade!

---

**Desenvolvido por rgabzz.**  
2025
