#include <Wire.h>
#include <LiquidCrystal_I2C.h>


// Define os pinos do Arduino conectados às entradas do driver ULN2003 para o motor de passo
const int IN1 = 8; // IN1 na placa ULN2003
const int IN2 = 9; // IN2
const int IN3 = 10; // IN3
const int IN4 = 11; // IN4

// Sequência de sinais para o motor de passo no modo "half-step" (8 passos por ciclo)
// Cada linha representa um passo com o estado ligado (1) ou desligado (0) dos 4 pinos
const int steps[8][4] = {
  {1, 0, 0, 0},
  {1, 1, 0, 0},
  {0, 1, 0, 0},
  {0, 1, 1, 0},
  {0, 0, 1, 0},
  {0, 0, 1, 1},
  {0, 0, 0, 1},
  {1, 0, 0, 1}
};

// Delay entre os passos
const int velocidade = 3;

// Pino do botão que liga/desliga o sistema
const int botaoPin = 2;

// Variável para guardar o estado anterior do botão 
bool estadoAnteriorBotao = LOW;

// Variável que indica se o sistema está ativo ou não
bool sistemaAtivo = true;

// Define o objeto LCD com o endereço I2C 0x27 e display 16x2 caracteres
LiquidCrystal_I2C lcd(0x27, 16, 2);

void setup() {
  Serial.begin(9600); // Inicializa comunicação serial 

  // Configura os pinos do motor como saída
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  pinMode(botaoPin, INPUT_PULLUP); // Configura o botão com resistor pull-up interno

  // Inicializa o LCD e mostra a mensagem inicial
  lcd.init();
  lcd.backlight();
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Sistema Ativo");
}

// Função para girar o motor em aproximadamente 90 graus
void AbrePorta(){
  for (int i = 0; i < 128; i++) { 
    for (int step = 0; step < 8; step++) {
      digitalWrite(IN1, steps[step][0]);
      digitalWrite(IN2, steps[step][1]);
      digitalWrite(IN3, steps[step][2]);
      digitalWrite(IN4, steps[step][3]);
      delay(velocidade);
    }
  }
  desligarBobinas();
}

// gira o motor em aproximadamente 270 graus para fechar a porta
void fechaPorta(){
  for (int i = 0; i < 384; i++) {
    for (int step = 0; step < 8; step++) {
      digitalWrite(IN1, steps[step][0]);
      digitalWrite(IN2, steps[step][1]);
      digitalWrite(IN3, steps[step][2]);
      digitalWrite(IN4, steps[step][3]);
      delay(velocidade);
    }
  }
  desligarBobinas();
}

// Função para desligar todas as bobinas do motor (deixar pinos em LOW)
void desligarBobinas() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
}


void loop() {
  // Lê o estado atual do botão (inverte pois está com pull-up)
  bool estadoBotao = !digitalRead(botaoPin);

  // Detecta mudança de estado do botão (ligado e desligado)
  if (estadoBotao && !estadoAnteriorBotao) {
    sistemaAtivo = !sistemaAtivo;
    lcd.clear();

    // Mostra mensagem quando o sistema estiver ativo
    if (sistemaAtivo) {
      lcd.setCursor(0, 0);
      lcd.print("Sistema Ativo");
      while (Serial.available()) Serial.read(); // Limpa buffer serial

    } else { // Mensagem quando desativado e garante que motor fique desligado ao desligar o sistema
      lcd.setCursor(0, 0);
      lcd.print("Sistema Desligado");
      digitalWrite(IN1, LOW);
      digitalWrite(IN2, LOW);
      digitalWrite(IN3, LOW);
      digitalWrite(IN4, LOW);
      while (Serial.available()) Serial.read();
    }
    delay(300); // Pequena pausa para evitar múltiplas detecções do botão
  }

  // Atualiza estado anterior do botão
  estadoAnteriorBotao = estadoBotao; 

  // Se o sistema está ativo e recebeu comando pela serial
  if (sistemaAtivo && Serial.available() > 0) {

    // Lê o comando recebido
    char comando = Serial.read();

    if (comando == 'A') {  // Comando para abrir a porta
      AbrePorta();
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Acesso Liberado");
    } 
    else if (comando == 'F') { // Comando para acesso negado (não gira motor)
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Acesso Negado");
    }
    else if (comando == 'C') {  // Comando para fechar a porta
      fechaPorta();
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Porta Fechada");
    }
  }
}
