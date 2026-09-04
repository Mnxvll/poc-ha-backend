# Explicación Detallada del Código (Sistema RECAUDO-T)

Este documento tiene como objetivo explicar de forma sencilla y paso a paso cómo funciona cada archivo del proyecto y cómo se comunican entre sí para lograr un sistema de **Alta Disponibilidad** tolerante a fallos.

---

## 1. El Problema que resolvemos

Imagina que tienes una aplicación bancaria para consultar saldo. Si tienes un solo servidor y este se apaga o se daña, todos tus clientes se quedan sin servicio. 

Para solucionar esto, en lugar de tener un solo servidor, creamos **múltiples servidores idénticos (Réplicas)**. Delante de ellos ponemos un "coordinador" llamado **Dispatcher**. El cliente nunca habla con las réplicas directamente; el cliente solo habla con el Dispatcher. El Dispatcher se encarga de saber cuáles réplicas están vivas y enviarles el trabajo.

---

## 2. El Archivo: `replica.py` (Los Servidores de Trabajo)

Piensa en una réplica como un cajero de banco. Su única función es responder rápidamente a lo que se le pregunte.

*   **¿Qué es?** Es una aplicación web muy sencilla construida con **Flask**.
*   **¿Cómo se configura?** Lee de las variables de entorno su puerto (ej. `5001`) y su nombre (`REPLICA_ID` = "A").
*   **Tiene 3 rutas (Endpoints) principales:**
    1.  `GET /ping`: Es el latido del corazón. Solo sirve para decir "¡Hey, estoy vivo y soy la Réplica A!". El Dispatcher usa esta ruta todo el tiempo para verificar la salud de la réplica.
    2.  `GET /saldo/<idTarjeta>`: Es la función de negocio real. Cuando se le pide, devuelve el saldo (`15000`) y firma la respuesta diciendo qué réplica la atendió.
    3.  `POST /chaos/crash`: Es un botón de autodestrucción. Llama a `os._exit(0)`, lo que apaga el proceso inmediatamente. Nos sirve para simular que el servidor se quemó o se quedó sin energía, para probar si nuestro sistema realmente tolera fallos.

---

## 3. El Archivo: `dispatcher.py` (El Cerebro Central)

El Dispatcher es el jefe. Su trabajo es doble: vigilar a los empleados (réplicas) y atender a los clientes. Para hacer las dos cosas al mismo tiempo sin quedarse congelado, usa **Hilos (Threads)**.

### Parte A: El Monitor (Ping / Echo)
En la función `bucle_monitor()`, el Dispatcher inicia un proceso en segundo plano (un hilo) que funciona como un bucle infinito:
1.  Cada `T` segundos, el Dispatcher le hace una petición a la ruta `/ping` de TODAS las réplicas.
2.  Si una réplica no responde en un tiempo máximo (`t`), el Dispatcher anota un **fallo**.
3.  Si la réplica acumula `k` fallos seguidos (ej. 2 fallos), el Dispatcher la declara oficialmente como **"CAIDA"** e imprime el mensaje en consola.
4.  Para que esto sea seguro, usamos `candado_estado` (`threading.Lock()`). Esto es como un semáforo que asegura que el hilo del monitor y el hilo que atiende a los clientes no intenten modificar el estado de las réplicas exactamente al mismo milisegundo (lo que causaría un error).

### Parte B: Redundancia Activa (Atender al cliente)
Cuando un cliente hace una petición real a `GET /saldo/123` en el Dispatcher:
1.  El Dispatcher revisa su libreta (el diccionario de estados) para ver cuáles réplicas están **"VIVAS"**.
2.  Levanta un **ThreadPoolExecutor** (un grupo de trabajadores concurrentes).
3.  El Dispatcher envía la misma consulta de saldo a **todas las réplicas vivas EXACTAMENTE AL MISMO TIEMPO**.
4.  Usando `concurrent.futures.as_completed`, el Dispatcher se queda esperando. **La primera réplica que responda** con la información, será la ganadora. 
5.  El Dispatcher toma esa primera respuesta y se la envía inmediatamente al cliente. Si las otras réplicas tardan más en responder, sus respuestas simplemente son ignoradas.

> **¿Por qué esto es genial?** Porque si tienes 3 réplicas y una se vuelve lenta (pero no ha muerto del todo), el cliente nunca notará la lentitud, ya que las otras dos réplicas responderán rápido y el Dispatcher siempre entrega la respuesta más veloz.

---

## 4. El Archivo: `runner.py` (El Orquestador)

Para que todo esto funcione, tendrías que abrir 4 terminales diferentes: tres para arrancar cada `replica.py` (en los puertos 5001, 5002 y 5003) y una para arrancar el `dispatcher.py` (puerto 5000). Hacer eso a mano es muy tedioso.

Para eso existe `runner.py`:
*   Es un pequeño script en Python que usa la librería `subprocess` para ejecutar otros comandos automáticamente.
*   Al correrlo, lanza mágicamente las tres réplicas por ti, espera un segundo a que enciendan, y luego lanza el Dispatcher.
*   Si presionas `Ctrl + C` en tu teclado, el bloque de `except KeyboardInterrupt:` atrapa esa señal y procede a "matar" (terminar) cuidadosamente todos los subprocesos de las réplicas y el dispatcher, dejando tu computadora limpia y sin procesos zombies corriendo en el fondo.

---

## En Resumen (Flujo Completo)

1. Corres `python runner.py`.
2. Las réplicas A, B y C se encienden y esperan peticiones.
3. El Dispatcher se enciende y empieza a hacerles `/ping` por debajo cada segundo. Todas reportan estar "VIVAS".
4. Un cliente pide su saldo. El Dispatcher le pregunta a A, B y C al mismo tiempo. La réplica B responde más rápido, así que el cliente recibe la respuesta de B.
5. De repente, alguien manda un `/chaos/crash` a la Réplica A.
6. En el siguiente ciclo de `/ping`, el Dispatcher nota que A no responde. A los dos fallos, la marca como "CAIDA".
7. Otro cliente pide su saldo. El Dispatcher revisa y ve que A está muerta, así que solo le hace la petición a B y C. El sistema sigue funcionando perfectamente sin que el cliente se haya enterado de que un servidor explotó.
