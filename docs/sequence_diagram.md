# Diagrama de Secuencia

Este diagrama ilustra los dos flujos principales de la arquitectura de alta disponibilidad:
1. **Monitor en Segundo Plano (Ping/Echo):** El Dispatcher sondea constantemente a las réplicas.
2. **Redundancia Activa:** El Dispatcher recibe una petición del cliente, consulta a todas las réplicas VIVAS en paralelo y retorna la respuesta más rápida.

```mermaid
sequenceDiagram
    participant Cliente
    participant Dispatcher
    participant ReplicaA as Réplica A
    participant ReplicaB as Réplica B

    %% Monitor en Segundo Plano (Ping/Echo)
    loop Cada T segundos
        Dispatcher->>ReplicaA: GET /ping
        Dispatcher->>ReplicaB: GET /ping
        
        alt Éxito
            ReplicaA-->>Dispatcher: 200 OK {"replica_id": "A"}
            Note right of Dispatcher: Reinicia fallos, estado VIVA
        else Tiempo de espera (t)
            ReplicaB--xDispatcher: ¡Timeout!
            Note right of Dispatcher: Incrementa fallos, estado CAIDA si >= k
        end
    end
    
    %% Flujo de Redundancia Activa para Petición del Cliente
    Note over Cliente,ReplicaB: Flujo de Petición con Redundancia Activa
    
    Cliente->>Dispatcher: GET /saldo/<idTarjeta>
    activate Dispatcher
    
    Note right of Dispatcher: Verifica el estado global:<br/>A está VIVA, B está VIVA
    
    par Petición a todas las réplicas VIVAS concurrentemente
        Dispatcher->>ReplicaA: GET /saldo/<idTarjeta>
        Dispatcher->>ReplicaB: GET /saldo/<idTarjeta>
    end
    
    ReplicaA-->>Dispatcher: 200 OK (Respuesta más rápida)
    
    Note right of Dispatcher: El Dispatcher responde inmediatamente<br/>al Cliente con la primera respuesta
    Dispatcher-->>Cliente: 200 OK (De la Réplica A)
    deactivate Dispatcher
    
    ReplicaB-->>Dispatcher: 200 OK (Respuesta más lenta)
    Note right of Dispatcher: El Dispatcher ignora las respuestas más lentas
```
