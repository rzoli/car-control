//******************************************************************************
// WiFiUartTransparentBridge
// Version 1.1.0
// Note
// This sketch is based on "WiFiTelnetToSerial - Example Transparent UART to Telnet Server for esp8266"
//******************************************************************************

#include <ESP8266WiFi.h>
#include "config.h"


WiFiServer localServer(networkport);
WiFiClient localClient;


void setup() {
  delay(1000);
  Serial.begin(baudrate);
  WiFi.setOutputPower(4);
  WiFi.begin(ssid, password);
  Serial.print("\nConnecting to "); Serial.println(ssid);

  uint8_t i = 0;
  while (WiFi.status() != WL_CONNECTED && i++ < 20) delay(500);
  if(i == 21){
    Serial.print("Could not connect to"); Serial.println(ssid);
    while(1) delay(500);
  }
  
  //start UART and the server
  localServer.begin();
  localServer.setNoDelay(true);

  Serial.print("Ready! Use 'Uart-WiFi Bridge ");
  Serial.print(WiFi.localIP());
  Serial.println(" to connect");

}

void loop() {
  //check if there are any new clients
  if (localServer.hasClient()){
    if (!localClient.connected()){
      if(localClient) localClient.stop();
      localClient = localServer.available();
    }
  }
      
  //check a client for data
  if (localClient && localClient.connected()){
    if(localClient.available()){
      size_t len = localClient.available();
      uint8_t sbuf[len];
      localClient.readBytes(sbuf, len);
      Serial.write(sbuf, len);      
    }
  }

  //check UART for data
  if(Serial.available()){
    size_t len = Serial.available();
    uint8_t sbuf[len];
    Serial.readBytes(sbuf, len);
    if (localClient && localClient.connected()){
      localClient.write(sbuf, len);
    }
  }
  Serial.println(localClient.connected());
  delay(1000);
  
}
