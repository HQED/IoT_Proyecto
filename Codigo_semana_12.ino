
#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>

// ==================================================
// 1. CONFIGURACION DE PINES
// ==================================================

#define DHTPIN 4
#define DHTTYPE DHT11

#define LDR_PIN 33
#define LED_ROJO 5
#define LED_VERDE 18
#define BUZZER 19
#define LED_BLANCO 21

DHT dht(DHTPIN, DHTTYPE);

// ==================================================
// 2. CREDENCIALES WIFI
// ==================================================

// Escribe el nombre y la clave de tu red Wi-Fi.
const char* ssid = "";
const char* password = "";

// ==================================================
// 3. CONFIGURACION DE ADAFRUIT IO
// ==================================================

// Usuario que aparece en tu cuenta de Adafruit IO.
const char* aio_username = "HARVIC";

// Reemplaza el texto por tu AIO Key.
// No compartir esta clave ni publicarse en GitHub.
const char* aio_key = "";

// Servidor MQTT de Adafruit IO.
const char* mqtt_server = "io.adafruit.com";
const int mqtt_port = 1883;

// ==================================================
// 4. FEEDS DE ADAFRUIT IO
// ==================================================

// Feeds para publicar las lecturas de los sensores.
const char* topic_temp = "HARVIC/feeds/temperatura";
const char* topic_hum = "HARVIC/feeds/humedad";
const char* topic_ldr = "HARVIC/feeds/luminosidad";

// Feeds para recibir comandos desde el dashboard.
const char* topic_led = "HARVIC/feeds/led-rojo";
const char* topic_buzzer = "HARVIC/feeds/buzzer";

// ==================================================
// 5. CLIENTES WIFI Y MQTT
// ==================================================

WiFiClient espClient;
PubSubClient client(espClient);

// ==================================================
// 6. VARIABLES Y UMBRALES
// ==================================================

unsigned long ultimoEnvio = 0;
unsigned long ultimoIntentoWiFi = 0;
unsigned long ultimoIntentoMQTT = 0;

// Publicar lecturas cada 20 segundos para reducir el uso del limite.
const unsigned long intervaloEnvio = 20000;

// Umbrales ambientales del proyecto.
const float TEMP_LIMITE = 28.0;
const float HUM_LIMITE = 40.0;
const int UMBRAL_OSCURIDAD = 1500;

// Control manual del LED rojo.
// false = automatico; true = manual.
bool modoManualLED = false;

// ==================================================
// 7. PUBLICAR DATOS EN ADAFRUIT IO
// ==================================================

void publicar(const char* topico, const char* mensaje) {
  if (client.connected()) {
    if (client.publish(topico, mensaje)) {
      Serial.print("Publicado en ");
      Serial.print(topico);
      Serial.print(": ");
      Serial.println(mensaje);
    } else {
      Serial.print("Error al publicar en: ");
      Serial.println(topico);
    }
  }
}

// ==================================================
// 8. RECIBIR COMANDOS DEL DASHBOARD
// ==================================================

void callback(char* topic, byte* payload, unsigned int length) {

  // Convertir el mensaje recibido a texto.
  String mensaje = "";

  for (unsigned int i = 0; i < length; i++) {
    mensaje += (char)payload[i];
  }

  mensaje.trim();
  mensaje.toUpperCase();

  String topicoRecibido = String(topic);

  Serial.print("Comando recibido [");
  Serial.print(topic);
  Serial.print("]: ");
  Serial.println(mensaje);

  // -----------------------------------------------
  // Control remoto del LED rojo
  // Acepta ON/1 y OFF/0 para interruptores.
  // AUTO devuelve el control a la temperatura.
  // -----------------------------------------------

  if (topicoRecibido == topic_led) {

    if (mensaje == "ON" || mensaje == "1" ||
        mensaje == "TRUE") {

      modoManualLED = true;

      digitalWrite(LED_ROJO, HIGH);
      digitalWrite(LED_VERDE, LOW);

      Serial.println("LED rojo encendido manualmente");
    }
    else if (mensaje == "OFF" || mensaje == "0" ||
             mensaje == "FALSE") {

      modoManualLED = true;

      digitalWrite(LED_ROJO, LOW);
      digitalWrite(LED_VERDE, LOW);

      Serial.println("LED rojo apagado manualmente");
    }
    else if (mensaje == "AUTO") {

      modoManualLED = false;

      Serial.println("Control automatico del LED activado");
    }
  }

  // -----------------------------------------------
  // Control remoto del buzzer
  // -----------------------------------------------

  if (topicoRecibido == topic_buzzer) {

    if (mensaje == "ON" || mensaje == "1" ||
        mensaje == "TRUE") {

      digitalWrite(BUZZER, HIGH);

      Serial.println("Buzzer encendido por comando remoto");
    }
    else if (mensaje == "OFF" || mensaje == "0" ||
             mensaje == "FALSE") {

      digitalWrite(BUZZER, LOW);

      Serial.println("Buzzer apagado por comando remoto");
    }
  }
}

// ==================================================
// 9. CONEXION CON ADAFRUIT IO
// ==================================================

void conectarMQTT() {

  if (WiFi.status() != WL_CONNECTED ||
      client.connected()) {
    return;
  }

  // Evitar intentos de conexion demasiado seguidos.
  if (millis() - ultimoIntentoMQTT < 5000) {
    return;
  }

  ultimoIntentoMQTT = millis();

  Serial.println("Conectando a Adafruit IO...");

  // Identificador unico para el ESP32.
  String mac = WiFi.macAddress();
  mac.replace(":", "");

  String clientId = "ESP32_Aula_" + mac;

  // Autenticacion con usuario y AIO Key.
  if (client.connect(
        clientId.c_str(),
        aio_username,
        aio_key)) {

    Serial.println("[OK] Conectado a Adafruit IO");

    // Suscribirse a los feeds de control.
    bool subLED = client.subscribe(topic_led);
    bool subBuzzer = client.subscribe(topic_buzzer);

    if (subLED && subBuzzer) {
      Serial.println("[OK] Suscripciones de control activas");
    } else {
      Serial.println("Aviso: no se pudo suscribir a todos los feeds");
    }

  } else {

    Serial.print("Error MQTT: ");
    Serial.println(client.state());

    Serial.println("Verifica usuario, AIO Key y conexion.");
  }
}

// ==================================================
// 10. CONFIGURACION INICIAL
// ==================================================

void setup() {

  Serial.begin(115200);

  // Configurar los actuadores como salidas.
  pinMode(LED_ROJO, OUTPUT);
  pinMode(LED_VERDE, OUTPUT);
  pinMode(BUZZER, OUTPUT);
  pinMode(LED_BLANCO, OUTPUT);

  // Apagar los actuadores al iniciar.
  digitalWrite(LED_ROJO, LOW);
  digitalWrite(LED_VERDE, LOW);
  digitalWrite(BUZZER, LOW);
  digitalWrite(LED_BLANCO, LOW);

  // Iniciar el sensor DHT11.
  dht.begin();

  // Lectura analogica de 12 bits: 0 a 4095.
  analogReadResolution(12);

  // Configurar Wi-Fi.
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(ssid, password);

  // Configurar el servidor MQTT.
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);

  // Tiempo maximo de espera para operaciones MQTT.
  client.setSocketTimeout(5);

  Serial.println();
  Serial.println("==================================");
  Serial.println(" SISTEMA IOT - AULA INTELIGENTE");
  Serial.println("      ADAFRUIT IO");
  Serial.println("==================================");
  Serial.println("Conectando a Wi-Fi...");
}

// ==================================================
// 11. CICLO PRINCIPAL
// ==================================================

void loop() {

  // -----------------------------------------------
  // A. Comprobar conexion Wi-Fi
  // -----------------------------------------------

  if (WiFi.status() != WL_CONNECTED) {

    if (millis() - ultimoIntentoWiFi >= 10000) {

      ultimoIntentoWiFi = millis();

      Serial.println("Wi-Fi desconectado. Reconectando...");
      WiFi.reconnect();
    }

    return;
  }

  // Mostrar la direccion IP una sola vez.
  static bool wifiInformado = false;

  if (!wifiInformado) {

    Serial.println("[OK] Wi-Fi conectado");
    Serial.print("Direccion IP: ");
    Serial.println(WiFi.localIP());

    wifiInformado = true;
  }

  // -----------------------------------------------
  // B. Mantener la conexion MQTT
  // -----------------------------------------------

  conectarMQTT();

  if (client.connected()) {
    client.loop();
  }

  // -----------------------------------------------
  // C. Leer sensores cada cinco segundos
  // -----------------------------------------------

  if (millis() - ultimoEnvio >= intervaloEnvio) {

    ultimoEnvio = millis();

    float temperatura = dht.readTemperature();
    float humedad = dht.readHumidity();

    int luminosidad = analogRead(LDR_PIN);

    Serial.println();
    Serial.println("======= LECTURAS DEL AULA =======");

    // ---------------------------------------------
    // D. Validar el DHT11
    // ---------------------------------------------

    if (isnan(temperatura) || isnan(humedad)) {

      Serial.println("Error: lectura invalida del DHT11");

    } else {

      // Mostrar las lecturas en el monitor serial.
      Serial.print("Temperatura: ");
      Serial.print(temperatura);
      Serial.println(" C");

      Serial.print("Humedad: ");
      Serial.print(humedad);
      Serial.println(" %");

      // Publicar las lecturas en Adafruit IO.
      String t = String(temperatura, 1);
      String h = String(humedad, 1);

      publicar(topic_temp, t.c_str());
      publicar(topic_hum, h.c_str());

      // -------------------------------------------
      // E. AUTOMATIZACION POR TEMPERATURA
      // -------------------------------------------

      if (temperatura > TEMP_LIMITE) {

        if (!modoManualLED) {

          digitalWrite(LED_ROJO, HIGH);
          digitalWrite(LED_VERDE, LOW);
        }

        Serial.println("Temperatura ALTA");

      } else {

        if (!modoManualLED) {

          digitalWrite(LED_ROJO, LOW);
          digitalWrite(LED_VERDE, HIGH);
        }

        Serial.println("Temperatura NORMAL");
      }

      // -------------------------------------------
      // F. AUTOMATIZACION POR HUMEDAD
      // -------------------------------------------

      if (humedad < HUM_LIMITE) {

        digitalWrite(BUZZER, HIGH);

        Serial.println("Humedad BAJA: buzzer encendido");

      } else {

        digitalWrite(BUZZER, LOW);

        Serial.println("Humedad NORMAL: buzzer apagado");
      }
    }

    // ---------------------------------------------
    // G. AUTOMATIZACION POR LUMINOSIDAD
    // ---------------------------------------------

    Serial.print("Luminosidad ADC: ");
    Serial.println(luminosidad);

    if (luminosidad < UMBRAL_OSCURIDAD) {

      digitalWrite(LED_BLANCO, HIGH);

      Serial.println("Oscuridad detectada");

    } else {

      digitalWrite(LED_BLANCO, LOW);

      Serial.println("Luz suficiente");
    }

    // Publicar la lectura del LDR.
    String l = String(luminosidad);
    publicar(topic_ldr, l.c_str());

    Serial.println("Lecturas procesadas");
    Serial.println("=================================");
  }
}
