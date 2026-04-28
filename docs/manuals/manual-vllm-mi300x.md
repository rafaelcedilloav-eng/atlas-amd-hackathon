# 🖥️ Manual de Configuración — vLLM + DeepSeek-R1 en AMD Instinct MI300X VF

> **Nivel:** Copia y pega en orden. No improvises.
> **Tiempo estimado:** 45–60 minutos (la mayoría es espera de carga del modelo)
> **GPU:** AMD Instinct MI300X VF — gfx942 — 192GB VRAM

---

## ⚠️ Antes de empezar — Lee esto

- Cada bloque de código se copia **completo** y se pega en la terminal
- Cuando un paso dice **"espera hasta ver X"**, no avances hasta verlo
- Si algo falla, hay una sección de **Troubleshooting** al final
- El modelo pesa ~65GB — la descarga/carga tarda. Es normal el silencio

---

## PASO 1 — Conectarse al servidor

Abre **PowerShell** en tu PC y ejecuta:

```
ssh root@165.245.141.216
```

Ingresa tu contraseña cuando la pida. Debes ver algo como:

```
root@0:~#
```

✅ Ya estás dentro del servidor.

---

## PASO 2 — Verificar que Docker está corriendo

```bash
docker ps
```

Si responde con una tabla (aunque esté vacía) → Docker está vivo. Si da error, ejecuta:

```bash
sudo systemctl start docker
sudo systemctl enable docker
```

---

## PASO 3 — Verificar que la GPU es visible

```bash
rocm-smi --showproductname
```

Debes ver:

```
GPU[0] : Card Series: AMD Instinct MI300X VF
```

Si no aparece la GPU, reinicia el servidor y vuelve al Paso 1.

---

## PASO 4 — Verificar que el directorio de modelos existe

```bash
ls /mnt/scratch/huggingface
```

Si da error `No such file or directory`, créalo:

```bash
mkdir -p /mnt/scratch/huggingface
```

---

## PASO 5 — Limpiar cualquier contenedor anterior

```bash
docker rm -f vllm-atlas 2>/dev/null || true
```

No importa si dice "Error: No such container" — eso es normal si es instalación nueva.

---

## PASO 6 — Liberar el puerto 8000 (por si está ocupado)

```bash
sudo fuser -k 8000/tcp 2>/dev/null || true
sudo systemctl restart docker
```

Espera 5 segundos después del restart antes de continuar.

---

## PASO 7 — Descargar la imagen de vLLM para ROCm

```bash
docker pull vllm/vllm-openai-rocm:v0.17.1
```

⏳ Esto puede tardar varios minutos dependiendo de tu conexión. Espera hasta ver:

```
Status: Downloaded newer image for vllm/vllm-openai-rocm:v0.17.1
```

Si la imagen ya estaba descargada dirá `Status: Image is up to date` — también está bien.

---

## PASO 8 — Lanzar el contenedor con vLLM

Copia y pega este bloque **completo** de una sola vez:

```bash
docker run -d --name vllm-atlas \
  --device=/dev/kfd \
  --device=/dev/dri \
  --group-add video \
  --group-add render \
  --ipc=host \
  --cap-add=SYS_PTRACE \
  --security-opt seccomp=unconfined \
  -v /mnt/scratch/huggingface:/root/.cache/huggingface \
  -p 8000:8000 \
  -e HF_HOME=/root/.cache/huggingface \
  -e ROCR_VISIBLE_DEVICES=0 \
  -e HIP_VISIBLE_DEVICES=0 \
  -e HSA_ENABLE_SDMA=0 \
  -e PYTORCH_ROCM_ARCH=gfx942 \
  vllm/vllm-openai-rocm:v0.17.1 \
  --model deepseek-ai/DeepSeek-R1-Distill-Qwen-32B \
  --tensor-parallel-size 1 \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.90
```

Si responde con un hash largo tipo:

```
53dadefb698bed85dfbd832e58ab77ac4a5e0b49901de3fa8f6834ae9dc79d33
```

✅ El contenedor arrancó correctamente.

---

## PASO 9 — Verificar que el contenedor está vivo

```bash
docker ps | grep vllm-atlas
```

Debes ver una línea con `Up X seconds` o `Up X minutes`. Si no aparece nada, ve a **Troubleshooting → Contenedor no aparece en docker ps**.

---

## PASO 10 — Monitorear la carga del modelo en VRAM

Abre una **segunda terminal de PowerShell** y conéctate igual:

```
ssh root@165.245.141.216
```

Luego ejecuta:

```bash
watch -n 3 'rocm-smi --showmeminfo vram'
```

Vas a ver la VRAM subir progresivamente:

```
VRAM Total Used Memory (B): 820817920      ← inicio (~800MB, normal)
VRAM Total Used Memory (B): 66600890368    ← cargando (~62GB)
VRAM Total Used Memory (B): 187044884480   ← casi listo (~174GB)
```

⏳ **Este proceso tarda entre 30 y 50 minutos.** Es completamente normal el silencio.

Cuando la VRAM se estabilice alrededor de **170–180GB** y deje de subir → el modelo terminó de cargar.

---

## PASO 11 — Verificar que el servidor está listo

En la primera terminal, revisa los logs:

```bash
docker logs --follow vllm-atlas
```

Espera hasta ver líneas como esta repetiéndose:

```
Engine 000: Avg prompt throughput: 0.0 tokens/s, Running: 0 reqs, Waiting: 0 reqs, GPU KV cache usage: 0.0%
```

Eso significa que el servidor está en **idle esperando requests**. ✅

Presiona `Ctrl+C` para salir de los logs.

---

## PASO 12 — Prueba final — confirmar que responde

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
    "messages": [{"role": "user", "content": "Hola, funciona?"}],
    "max_tokens": 50
  }'
```

Si ves una respuesta JSON con texto en el campo `content` → **el servidor está 100% operativo**. 🎉

---

## PASO 13 — Guardar el script de arranque (hazlo una sola vez)

```bash
cat > /root/start-vllm.sh << 'EOF'
#!/bin/bash
docker rm -f vllm-atlas 2>/dev/null || true
sudo fuser -k 8000/tcp 2>/dev/null || true

docker run -d --name vllm-atlas \
  --device=/dev/kfd \
  --device=/dev/dri \
  --group-add video \
  --group-add render \
  --ipc=host \
  --cap-add=SYS_PTRACE \
  --security-opt seccomp=unconfined \
  -v /mnt/scratch/huggingface:/root/.cache/huggingface \
  -p 8000:8000 \
  -e HF_HOME=/root/.cache/huggingface \
  -e ROCR_VISIBLE_DEVICES=0 \
  -e HIP_VISIBLE_DEVICES=0 \
  -e HSA_ENABLE_SDMA=0 \
  -e PYTORCH_ROCM_ARCH=gfx942 \
  vllm/vllm-openai-rocm:v0.17.1 \
  --model deepseek-ai/DeepSeek-R1-Distill-Qwen-32B \
  --tensor-parallel-size 1 \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.90

echo ""
echo "✅ Contenedor lanzado. Esperando carga del modelo (~40 min)..."
echo "Monitorea VRAM con: watch -n 3 'rocm-smi --showmeminfo vram'"
EOF

chmod +x /root/start-vllm.sh
echo "Script guardado en /root/start-vllm.sh"
```

**La próxima vez que reinstales**, solo ejecuta:

```bash
bash /root/start-vllm.sh
```

Y ve directo al Paso 10.

---

## 🔧 Troubleshooting — Problemas comunes

---

### ❌ Error: `Bind for :::8000 failed: port is already allocated`

```bash
sudo fuser -k 8000/tcp
sudo systemctl restart docker
# Espera 5 segundos, luego repite el Paso 8
```

---

### ❌ Error: `Failed to infer device type`

Causa: variables de entorno incorrectas o permisos de dispositivo.
Solución: asegúrate de copiar el comando del **Paso 8 completo** sin modificar nada, especialmente que **NO tenga** `HSA_OVERRIDE_GFX_VERSION`.

```bash
docker rm -f vllm-atlas
# Repite el Paso 8 copiando el bloque completo
```

---

### ❌ El contenedor no aparece en `docker ps`

```bash
# Ver si murió y por qué
docker logs vllm-atlas --tail 30
```

Si ves `RuntimeError: Failed to infer device type` → repite desde el Paso 6.
Si ves `OOM` o `out of memory` → el modelo no cabe en VRAM, contacta soporte.

---

### ❌ La VRAM se queda en ~800MB y no sube

El EngineCore worker no está accediendo a la GPU. Solución:

```bash
docker rm -f vllm-atlas
sudo systemctl restart docker
# Espera 10 segundos
bash /root/start-vllm.sh
```

---

### ❌ El curl no responde / connection refused

El servidor aún no terminó de cargar. Vuelve al **Paso 10** y espera que la VRAM llegue a ~174GB antes de probar el curl.

---

### ❌ Warning: `AMD GPU device(s) is/are in a low-power state`

**Este warning es normal e inofensivo** en la MI300X VF. El hypervisor controla el power state — no afecta el funcionamiento del modelo. Ignóralo.

---

## 📋 Referencia rápida — Comandos del día a día

| Acción | Comando |
|--------|---------|
| Arrancar el servidor | `bash /root/start-vllm.sh` |
| Ver si está corriendo | `docker ps \| grep vllm-atlas` |
| Ver logs en vivo | `docker logs --follow vllm-atlas` |
| Ver VRAM en uso | `rocm-smi --showmeminfo vram` |
| Detener el servidor | `docker rm -f vllm-atlas` |
| Probar que responde | `curl http://localhost:8000/v1/chat/completions -H "Content-Type: application/json" -d '{"model":"deepseek-ai/DeepSeek-R1-Distill-Qwen-32B","messages":[{"role":"user","content":"test"}],"max_tokens":10}'` |

---

## 📌 Datos clave de esta configuración

| Parámetro | Valor |
|-----------|-------|
| GPU | AMD Instinct MI300X VF |
| Arquitectura GFX | gfx942 |
| VRAM total | ~192 GB |
| VRAM usada por el modelo | ~174 GB |
| Modelo | DeepSeek-R1-Distill-Qwen-32B |
| Puerto API | 8000 |
| Imagen Docker | vllm/vllm-openai-rocm:v0.17.1 |
| Max model len | 8192 tokens |
| GPU memory utilization | 90% |

---

*Manual generado el 26 de Abril 2026 — basado en sesión de configuración real.*
