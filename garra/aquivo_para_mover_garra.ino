#include <Servo.h>

Servo base;
Servo braco;
Servo antebraco;
Servo garra;

void setup() {
  Serial.begin(9600);

  base.attach(2);
  braco.attach(3);
  antebraco.attach(4);
  garra.attach(5);

  base.write(90);
  delay(500);
  braco.write(120);
  delay(500);
  antebraco.write(60);
  delay(500);
  garra.write(120);
  delay(500);

  pegarObjeto();
  colocarNaEsteira();
  voltarParaPosicaoInicial();

  Serial.println("\nComando recebido! Iniciando a sequência de movimentos...");
}

void loop() {
  // if (Serial.available() > 0) {
  //   while (Serial.available() > 0) {
  //     Serial.read();
  //   }

  //   Serial.println("\nComando recebido! Iniciando a sequência de movimentos...");

  //   pegarObjeto();
  //   colocarNaEsteira();
  //   voltarParaPosicaoInicial();

  //   Serial.println("\nSequência concluída.");
  //   Serial.println("Aguardando novo comando...");
  //   Serial.println("----------------------------------------------------");
  // }
}

/**
 * @brief Move o braço para pegar um objeto.
 */
void pegarObjeto() {
  Serial.println("1. Pegando objeto...");
  moverMotor(base, 90, 180);
  moverMotor(braco, 120, 30);
  // moverMotor(antebraco, 60, 15);
  moverMotor(garra, 120, 140);
  moverMotor(braco, 30, 120);
}

/**
 * @brief Move o braço para colocar o objeto em uma esteira.
 */
void colocarNaEsteira() {
  Serial.println("2. Colocando na esteira...");
  // moverMotor(antebraco, 15, 35);
  // moverMotor(antebraco, 35, 60);
  // moverMotor(braco, 80, 120);
  moverMotor(antebraco, 60, 130);
  moverMotor(base, 180, 0);
  moverMotor(braco, 120, 80);
  moverMotor(garra, 140, 120);
}

/**
 * @brief Retorna o braço para a posição inicial de repouso.
 */
void voltarParaPosicaoInicial() {
  Serial.println("3. Voltando para a posição inicial...");
  moverMotor(base, 0, 90);
  // moverMotor(braco, 120, 50);
  // moverMotor(antebraco, 60, 15);

  // Garante que o braço termine na mesma posição que começou
  moverMotor(braco, 80, 120);
  moverMotor(antebraco, 130, 60);
}

/**
 * @brief Move um servo de uma posição inicial para uma final de forma gradual.
 * @param servo O objeto Servo a ser movido.
 * @param posicaoInicial O ângulo inicial.
 * @param posicaoFinal O ângulo final.
 */
void moverMotor(Servo servo, int posicaoInicial, int posicaoFinal) {
  int passo = 40;

  if (posicaoInicial < posicaoFinal) {
    for (int posicao = posicaoInicial; posicao <= posicaoFinal; posicao++) {
      servo.write(posicao);
      delay(passo);
    }
  } else {
    for (int posicao = posicaoInicial; posicao >= posicaoFinal; posicao--) {
      servo.write(posicao);
      delay(passo);
    }
  }
}