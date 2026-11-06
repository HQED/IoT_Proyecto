# Semana 13. Monitor de Aula Conectado

## 1. Descripción del proyecto

En esta actividad se implementó un sistema IoT para monitorear la luminosidad de un aula mediante un sensor LDR conectado a una placa ESP32.

El sistema transmite las lecturas del sensor a Adafruit IO mediante el protocolo MQTT. Posteriormente, IFTTT supervisa el feed de luminosidad y genera una notificación en el celular cuando detecta un valor inferior a 1000 ADC.

## 2. Objetivo

Implementar un sistema de monitoreo de luminosidad que permita visualizar los datos históricos y generar alertas automáticas mediante una plataforma de integración en la nube.

## 3. Componentes utilizados

- ESP32.
- Sensor LDR.
- Sensor DHT11.
- Arduino IDE.
- Plataforma Adafruit IO.
- Servicio IFTTT.
- Aplicación móvil IFTTT.
- Conexión Wi-Fi.

## 4. Arquitectura del sistema

El funcionamiento sigue este flujo:

Sensor LDR → ESP32 → MQTT → Adafruit IO → IFTTT → Notificación móvil.

El ESP32 obtiene las lecturas del sensor y las publica en Adafruit IO cada 15 segundos. IFTTT supervisa el feed y ejecuta la acción configurada cuando se cumple la condición establecida.

## 5. Configuración del sistema

- Sensor LDR: GPIO33.
- Sensor DHT11: GPIO4.
- Feed de Adafruit IO: luminosidad.
- Frecuencia de publicación: 15 segundos.
- Condición de alerta: valor inferior a 1000 ADC.
- Acción: enviar una notificación mediante la aplicación IFTTT.

## 6. Resultados de las pruebas

Se comprobó el funcionamiento del sensor LDR mediante pruebas de iluminación y oscuridad. Las lecturas cambiaron según la cantidad de luz recibida.

También se verificó la recepción de datos en Adafruit IO y su representación mediante un gráfico histórico.

Finalmente, se configuró un Applet en IFTTT para generar notificaciones cuando el valor del feed luminosidad fuera inferior a 1000 ADC. Las notificaciones llegaron correctamente al dispositivo Android.

## 7. Evidencias

Las capturas de las pruebas se encuentran en la carpeta `evidencias`:

- Dashboard de Adafruit IO.
- Gráfico histórico de luminosidad.
- Configuración del Applet IFTTT.
- Notificaciones recibidas en el celular.

## 8. Conclusión

La actividad permitió integrar un sensor físico con una plataforma IoT en la nube y un servicio de automatización. Se comprobó la transmisión de datos, su visualización histórica y la generación de notificaciones móviles según una condición definida.

## 9. Tecnologías utilizadas

ESP32, Arduino IDE, MQTT, Adafruit IO e IFTTT.
