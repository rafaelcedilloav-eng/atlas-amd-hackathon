# CHECKLIST FINAL DE AUDITORÍA Y ENTREGA - ATLAS v3.0
**Protocolo: AACDU v3.1**
**Auditor:** Kimi-K2

## 1. INVENTARIO DE HARDWARE Y DRIVERS (AMD MI300X)
- [ ] OS: Ubuntu 22.04.4 LTS (Kernel 6.5+ optimizado).
- [ ] Drivers: amdgpu-dkms + ROCm 6.2.0 instalados.
- [ ] Variables de Entorno: `HSA_OVERRIDE_GFX_VERSION=11.0.0` (Target: gfx942).
- [ ] Permisos: Usuario 'atlas' añadido a grupos `render, video, kmem`.

## 2. INFRAESTRUCTURA Y DOCKER
- [ ] Docker Engine 24.0.7+ con runtime configurado para ROCm.
- [ ] Docker Compose v2.24.0+.
- [ ] `docker-compose.hackathon.yml` configurado con aislamiento de GCDs.
- [ ] `entrypoint.sh` configurado con espera de dependencias.

## 3. LIBRERÍAS Y ENTORNO PYTHON
- [ ] PyTorch 2.3.0 + ROCm 6.2.
- [ ] VLLM-ROCm 0.4.2 optimizado para MI300X.
- [ ] Dependencias críticas: `bleach`, `supabase`, `opentelemetry`.
- [ ] Validación: `python -c "import torch; print(torch.cuda.is_available())"` -> `True`.

## 4. ESTADO DE LA ARQUITECTURA ATLAS v3.0
- [ ] **Core Hexagonal:** Completado (Dominio, Puertos, Servicios).
- [ ] **Adaptadores Blindados:** Implementados (`Supabase`, `VLLM`, `SSEBus`) con sanitización PII y Circuit Breaker.
- [ ] **Observabilidad:** OpenTelemetry instrumentado y listo para trazas.
- [ ] **Seguridad:** Sanitización automática de logs, validación MIME, Rate Limiting.

## 5. ACCIONES POST-MIGRACIÓN (PENDIENTES)
- [ ] Guardar baseline de `rocm-smi` en `/var/log/atlas/`.
- [ ] Ejecutar `ATLAS_v3.0_DEPLOYMENT_REPORT.md` (Checklist final).
- [ ] Activar monitoreo en Grafana/Prometheus (Golden Signals).

---
*Este documento constituye la garantía técnica de que el sistema ATLAS v3.0 cumple con los estándares AACDU v3.1. Se autoriza el despliegue tras completar este checklist.*
