#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <ArduinoJson.h>

// ==================== CONFIGURACIÓN WiFi ====================
#define WIFI_SSID     "Totalplay-B8A3"        // Cambiar
#define WIFI_PASSWORD "B8A3A636xMXEJCyH"      // Cambiar

// ==================== CONFIGURACIÓN MQTT ====================
#define MQTT_SERVER   "192.168.100.240"        // IP de la Raspberry Pi
#define MQTT_PORT     1883                     // 1883 Raspberry Pi / 1884 Docker
#define NODE_ID       "nodo1"                  // CAMBIAR: "nodo1", "nodo2" o "nodo3"

#define DHT_PIN    4     // P4 = DATA del DHT11
#define DHT_TYPE   DHT11
#define LDR_PIN    34    // P34 = Salida digital del LDR
#define RELAY_PIN  26    // P26 = Señal de control del relevador

// ==================== ESTRUCTURA DE TOPICS ====================
const String TOPIC_DATOS   = "iot/ambiente/" + String(NODE_ID);
const String TOPIC_CONTROL = "iot/control/"  + String(NODE_ID);

// ==================== OBJETOS GLOBALES ====================
WiFiClient   clienteWiFi;
PubSubClient clienteMQTT(clienteWiFi);
DHT          dht(DHT_PIN, DHT_TYPE);

unsigned long ultimaPublicacion = 0;
const unsigned long INTERVALO_PUBLICACION = 5000;  // Publicar cada 5 segundos
bool estadoRelevador = false;

// ==================== FUNCIÓN: Conectar WiFi ====================
void conectarWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;

  Serial.println("\n[WiFi] Conectando a: " + String(WIFI_SSID));
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int intentos = 0;
  while (WiFi.status() != WL_CONNECTED && intentos < 30) {
    delay(500);
    Serial.print(".");
    intentos++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WiFi] ✓ Conectado exitosamente");
    Serial.println("[WiFi]   IP local: " + WiFi.localIP().toString());
    Serial.println("[WiFi]   RSSI:     " + String(WiFi.RSSI()) + " dBm");
  } else {
    Serial.println("\n[WiFi] ✗ Error: No se pudo conectar");
    Serial.println("[WiFi]   Reiniciando en 5 segundos...");
    delay(5000);
    ESP.restart();
  }
}

// ==================== FUNCIÓN: Callback MQTT ====================
void callbackMQTT(char* topic, byte* payload, unsigned int length) {
  // Convertir payload a String
  String mensaje = "";
  for (unsigned int i = 0; i < length; i++) mensaje += (char)payload[i];
  mensaje.trim();

  Serial.println("\n[MQTT] ← Mensaje recibido");
  Serial.println("  Topic:   " + String(topic));
  Serial.println("  Payload: " + mensaje);

  // Procesar comandos
  if (String(topic) == TOPIC_CONTROL) {
    if (mensaje == "1") {
      estadoRelevador = true;
      digitalWrite(RELAY_PIN, HIGH);
      Serial.println("  Acción: Relevador ENCENDIDO ✓");
    } else if (mensaje == "0") {
      estadoRelevador = false;
      digitalWrite(RELAY_PIN, LOW);
      Serial.println("  Acción: Relevador APAGADO ✓");
    } else {
      Serial.println("  Acción: Comando no reconocido - se esperaba 0 o 1");
    }
  }
}

// ==================== FUNCIÓN: Conectar MQTT ====================
void conectarMQTT() {
  while (!clienteMQTT.connected()) {
    Serial.println("\n[MQTT] Conectando al broker...");
    Serial.println("  Servidor: " + String(MQTT_SERVER));
    Serial.println("  Puerto:   " + String(MQTT_PORT));
    Serial.println("  Nodo ID:  " + String(NODE_ID));

    if (clienteMQTT.connect(NODE_ID)) {
      Serial.println("[MQTT] ✓ Conectado al broker");

      // Suscribirse al topic de control del relevador
      clienteMQTT.subscribe(TOPIC_CONTROL.c_str());
      Serial.println("[MQTT] ✓ Suscrito a: " + TOPIC_CONTROL);

    } else {
      Serial.print("[MQTT] ✗ Error de conexión. Estado: ");
      Serial.println(clienteMQTT.state());
      Serial.println("[MQTT]   Reintentando en 5 segundos...");
      delay(5000);
    }
  }
}

// ==================== FUNCIÓN: Leer Temperatura ====================
float leerTemperatura() {
  float t = dht.readTemperature();
  if (isnan(t)) {
    Serial.println("[DHT11] ✗ Error al leer temperatura");
    return -999;
  }
  return round(t * 10) / 10.0; 
}

// ==================== FUNCIÓN: Leer Humedad ====================
float leerHumedad() {
  float h = dht.readHumidity();
  if (isnan(h)) {
    Serial.println("[DHT11] ✗ Error al leer humedad");
    return -999;
  }
  return round(h * 10) / 10.0; 
}

// ==================== FUNCIÓN: Leer Luz ====================
float leerLuz() {
  int val = digitalRead(LDR_PIN);
  return val == 0 ? 100 : 0;
}

// ==================== FUNCIÓN: Publicar Datos ====================
void publicarDatos() {
  float temperatura = leerTemperatura();
  float humedad     = leerHumedad();
  float luz         = leerLuz();

  // Revisa los datos del DH11, si son inválidos no los publica
  if (temperatura == -999 || humedad == -999) {
    Serial.println("Datos inválidos, los datos no se publicaron");
    return;
  }

  // Construir JSON con los datos del nodo
  StaticJsonDocument<200> doc;
  doc["nodo"]        = NODE_ID;
  doc["temperatura"] = temperatura;
  doc["humedad"]     = humedad;
  doc["luz"]         = luz;
  doc["relay"]       = estadoRelevador ? 1 : 0;

  String payload;
  serializeJson(doc, payload);

  // Publicar en el topic del nodo
  bool exito = clienteMQTT.publish(TOPIC_DATOS.c_str(), payload.c_str());

  if (exito) {
    Serial.println("\n[MQTT] → Datos publicados");
    Serial.println("  Topic:   " + TOPIC_DATOS);
    Serial.println("  Payload: " + payload);
  } else {
    Serial.println("\n[MQTT] ✗ Error al publicar datos");
  }
}

// ==================== SETUP ====================
void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("\n\n");
  Serial.println("========================================");
  Serial.println("  ESP32 - Cliente MQTT");
  Serial.println("  Nodo ID: " + String(NODE_ID));
  Serial.println("  Broker:  " + String(MQTT_SERVER));
  Serial.println("========================================");

  //Acá se configura cada pin
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);   // Relevador apagado al iniciar
  pinMode(LDR_PIN, INPUT);

  //Esta parte inicia el dht11
  dht.begin();
  delay(2000);  // Por si acaso

  // Conectar a WiFi
  conectarWiFi();

  // Configurar y conectar MQTT
  clienteMQTT.setServer(MQTT_SERVER, MQTT_PORT);
  clienteMQTT.setCallback(callbackMQTT);
  conectarMQTT();

  Serial.println("\n[Sistema] Listo. Publicando cada " + String(INTERVALO_PUBLICACION / 1000) + " segundos\n");
}

// ==================== LOOP ====================
void loop() {
  // Verificar y reconectar WiFi si es necesario
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WiFi] ✗ Desconectado. Reconectando...");
    conectarWiFi();
  }

  // Verificar y reconectar MQTT si es necesario
  if (!clienteMQTT.connected()) {
    Serial.println("[MQTT] ✗ Desconectado. Reconectando...");
    conectarMQTT();
  }

  // Mantener conexión MQTT y procesar mensajes entrantes
  clienteMQTT.loop();

  // Publicar datos periódicamente
  unsigned long ahora = millis();
  if (ahora - ultimaPublicacion >= INTERVALO_PUBLICACION) {
    ultimaPublicacion = ahora;
    publicarDatos();
  }
}
