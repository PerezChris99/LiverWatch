# Device Integration Contract

External hardware is an integration boundary, not trusted clinical truth.

Every device measurement must carry device identity, subject identity, canonical measurement code, value/unit, timezone-aware measurement time, signal quality and protocol. New measurements enter LiverWatch as pending and become usable only after the platform's validation policy accepts them.

Adapters may support BLE, HTTPS or batch transport. Hardware vendors must not couple directly to risk-engine internals.

A device alert is a monitoring event and must never be presented as a diagnosis. Clinical claims require independent validation against appropriate reference measurements.
