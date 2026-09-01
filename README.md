# 🦋 Windows Live / MSN Messenger (Python Edition)

Recriação autêntica e nostálgica do clássico **MSN Messenger (Windows Live Messenger)** em **Python (PyQt6 + WebSockets + SQLite)** com suporte a:
- 📝 **Registo Real de Contas (Windows Live ID):** Criação de conta persistente com email, palavra-passe encriptada, alcunha e avatar.
- ⚡ **Chamar a Atenção (Nudge / Zumbido):** Janela a tremer no ecrã com som autêntico!
- 📹 **Câmara de Vídeo / Webcam:** Chamadas de vídeo em tempo real entre contactos.
- 😊 **Emoticons Clássicos:** Atalhos como `:)`, `:D`, `(L)`, `(Y)`, `(H)`, `(6)`, `(A)`, `(K)`, `(8)`, etc.
- 🔔 **Notificações Toast:** Popups deslizantes animados no canto inferior direito do ecrã quando amigos entram online.
- 🎮 **Mini-Jogos:** Jogo do Galo (*Tic-Tac-Toe*) interativo e em tempo real.
- 🔊 **Sons Nostálgicos:** Síntese procedural de sons do MSN sem requerer ficheiros externos.
- 🎨 **Estilo Visual Fiel:** Folha de estilos Aero/Aqua gloss do Windows Live.

### 🚀 Como Usar a Aplicação Real (Com Registo de Conta):
```bash
# Iniciar a aplicação do MSN Messenger:
python run_msn.py
```
1. No ecrã que abre, clica em **"✨ Não tem conta? Criar uma conta do Windows Live ID"**.
2. Preenche o teu email (ex: `o_teu_nome@hotmail.com`), a tua palavra-passe, alcunha e escolhe o teu avatar.
3. Clica em **"Criar Conta e Registar"**.
4. Inicia sessão com as tuas credenciais!

---

### 🌐 Para Falar com Amigos noutros Computadores:
1. No PC Servidor: `python run_msn_server.py`
2. No PC do Amigo: `python run_msn.py` (e no campo "⚙️ Definições de Ligação / Servidor", colocar o IP do Servidor).

---

# 🎙️ Paltalk Multimedia Lounge (Desktop Client-Server)

## 🚀 Funcionalidades Principais

### 1. Servidor Central (`server/`)
- **Gestão de Salas e Categorias:** Criação de salas públicas ou protegidas por palavra-passe nas categorias temáticas (*Música & Karaoke, Tecnologia & Programação, Debate & Conversa Geral, Gaming, etc.*).
- **Fila de Microfone Inteligente (Push-To-Talk FIFO):** Mecanismo de pedir palavra (*Raise Hand*), atribuição ordenada com temporizador automático de orador e passagem de microfone.
- **Hierarquia de Moderação:**
  - 👑 **Crown (Admin):** Dono e criador da sala.
  - 🛡️ **Moderador:** Pode silenciar utilizadores (*Mute*), passar o microfone e expulsar (*Kick/Ban*).
  - 👤 **Membro:** Participante da sala.
- **Servidor de Média UDP (SFU Relay):** Retransmissão de frames de vídeo JPEG comprimidos e áudio para todos os clientes conectados na sala com latência ultrabaixa.

### 2. Cliente Desktop (`client/` - PyQt6)
- **Navegador do Lobby:** Lista de salas ativas com contagem de utilizadores, orador no ar, filtro de pesquisa em tempo real e criação de salas.
- **Sala Multimédia Completa:**
  - **Grelha Superior de Vídeo:** Múltiplas webcams simultâneas com moldura verde dinâmica de orador ativo e suporte a avatar virtual animado automático na ausência de webcam física.
  - **Lista de Membros Interativa:** Exibição de crachás (👑, 🛡️, 🎤, ✋, 📷, 🔇) e menu de contexto com o botão direito.
  - **Chat Central:** Histórico com timestamp, formatação visual e mensagens do sistema.
  - **Barra de Microfone Push-to-Talk:** Botão dinâmico com suporte à tecla de atalho `Espaço`, indicador de fila e botão de pedir/baixar mão.
- **Janela de Whisper (1-on-1):** Janela dedicada para conversas privadas diretas com outros utilizadores.

---

## 📦 Instalação das Dependências

Certifica-te de ter o Python 3.10+ instalado. Instala as bibliotecas necessárias:

```bash
pip install -r requirements.txt
```

As dependências incluem:
- `PyQt6` (Interface gráfica moderna)
- `websockets` (Protocolo assíncrono de sinalização e eventos)
- `opencv-python` (Captura e processamento de vídeo de webcam)
- `sounddevice` (Captura e reprodução de áudio)
- `numpy` & `pillow` (Manipulação e conversão de matrizes de imagem)

---

## 🏃 Como Executar e Testar

### 1. Iniciar o Servidor
Abre um terminal e executa:
```bash
python run_server.py
```
O servidor ficará à escuta nas portas:
- WebSocket: `ws://0.0.0.0:8765`
- Media UDP: `udp://0.0.0.0:8766`

---

### 2. Iniciar o Primeiro Cliente
Num novo terminal:
```bash
python run_client.py
```
1. Insere um nome de utilizador (ex: `Victor_Admin`).
2. Clica em **"Ligar e Entrar no Lobby"**.
3. Escolhe uma sala existente ou clica em **"➕ Criar Sala"**.

---

### 3. Iniciar um Segundo Cliente para Teste Simultâneo
Noutro terminal:
```bash
python run_client.py
```
1. Insere outro nome (ex: `Ana_Guest`).
2. Entra na mesma sala do primeiro cliente.
3. Testa:
   - Envio de mensagens no chat.
   - Pressionar a barra de espaços ou o botão **"🎤 Pressionar para Falar"** para assumir o microfone.
   - Clicar com o botão direito no nome do utilizador na lista de membros para abrir **"💬 Mensagem Privada (Whisper)"**.
   - Clicar em **"📷 Ligar Câmara"** para transmitir vídeo na grelha superior.

---

## 📂 Estrutura do Código

```
friend/
├── requirements.txt            # Ficheiro de dependências
├── run_server.py               # Ponto de entrada do Servidor
├── run_client.py               # Ponto de entrada do Cliente
├── README.md                   # Documentação
├── common/
│   ├── protocol.py             # Ações, Cargos e Pacotes JSON padronizados
│   └── utils.py                # Empacotamento binário de áudio e vídeo UDP
├── server/
│   ├── server_app.py           # Servidor WebSocket & Gestor de Conexões
│   ├── room_manager.py         # Lógica de salas, moderação e fila FIFO de oradores
│   └── media_relay.py          # SFU UDP Relay para áudio e vídeo
└── client/
    ├── client_app.py           # Orquestrador da aplicação cliente
    ├── network/
    │   ├── ws_client.py        # Cliente WebSocket assíncrono com sinais PyQt6
    │   └── media_client.py     # Cliente UDP de transmissão multimédia
    ├── media/
    │   ├── video_engine.py     # Captura OpenCV, câmara virtual e conversão PyQt6
    │   └── audio_engine.py     # Captura e reprodução de som com Sounddevice
    └── gui/
        ├── styles.py           # Folha de estilos Dark Theme moderna
        ├── login_dialog.py     # Janela de entrada
        ├── lobby_window.py     # Diretório de salas e categorias
        ├── room_window.py      # Janela principal da sala com grelha de vídeo e chat
        ├── private_chat.py     # Janela independente de Whisper
        └── widgets/
            ├── video_tile.py   # Tile individual de webcam/avatar com moldura ativa
            └── user_list.py    # Lista de membros com badges e menu de moderação
```