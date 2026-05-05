# GPU AMD MI300X — Guia de Arranque desde Cero

Sigue este doc al pie de la letra. Todo lo que necesitas para continuar mañana.

---

## 1. Crear el GPU en DigitalOcean

1. Ve a DigitalOcean → Create Droplet
2. Selecciona **GPU Droplet** → AMD MI300X (205 GB VRAM)
3. OS: **Ubuntu 24.04 LTS**
4. SSH Key: agrega `atlas_r2_key.pub` (esta en `.ssh/atlas_r2_key.pub`)
5. Anota la IP nueva (reemplaza 134.199.201.13 en todos los comandos)

---

## 2. Conectarse

```bash
ssh -i .ssh/atlas_r2_key root@<IP_NUEVA>
```

---

## 3. Verificar GPU

```bash
rocm-smi
# Debe mostrar: AMD Instinct MI300X, ~205 GB VRAM

rocminfo | grep -A2 'gfx942'
# Debe mostrar: AMD Instinct MI300X VF
```

---

## 4. Instalar dependencias del sistema

```bash
apt-get update -y
apt-get install -y python3.12 python3.12-venv python3-pip git tmux wget
```

---

## 5. Crear entorno virtual

```bash
python3 -m venv /root/atlas_r2_env
source /root/atlas_r2_env/bin/activate
```

---

## 6. Instalar PyTorch con ROCm

```bash
pip install torch==2.5.1+rocm6.2 torchvision==0.20.1+rocm6.2 torchaudio==2.5.1+rocm6.2 \
    --index-url https://download.pytorch.org/whl/rocm6.2

# Verificar:
python3 -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
# Debe imprimir: True / AMD Instinct MI300X VF
```

---

## 7. Instalar librerias de training

```bash
pip install \
    transformers==5.7.0 \
    datasets==2.18.0 \
    accelerate==1.13.0 \
    huggingface_hub==1.13.0 \
    tensorboard==2.20.0 \
    deepspeed==0.18.9
```

> **NO instalar bitsandbytes** — no tiene soporte ROCm, causa errores.
> **NO usar Unsloth** — usa kernels CUDA, incompatible con ROCm.

---

## 8. Subir archivos al GPU

Desde tu maquina local (Windows), en PowerShell:

```powershell
# Carpeta de trabajo
ssh -i .ssh/atlas_r2_key root@<IP_NUEVA> "mkdir -p /root/atlas_r2 /data /outputs"

# Scripts de training
scp -i .ssh/atlas_r2_key `
    Trainning_Steps/finetune_qwen3_14b.py `
    Trainning_Steps/finetune_deepseek_r1_8b.py `
    scripts/upload_to_hf.py `
    scripts/upload_deepseek_hf.py `
    root@<IP_NUEVA>:/root/atlas_r2/

# Dataset
scp -i .ssh/atlas_r2_key `
    Trainning_Steps/atlas_training_dataset_final.jsonl `
    root@<IP_NUEVA>:/data/atlas_training_dataset.jsonl
```

---

## 9. Configuracion HuggingFace

```bash
source /root/atlas_r2_env/bin/activate

# Setear token (no guardarlo en archivos)
export HF_TOKEN=***REMOVED***
```

---

## 10. Modelos ya entrenados en HuggingFace

Si necesitas descargar los modelos ya entrenados:

```bash
# Qwen3-14B ATLAS R2
huggingface-cli download Rafaelcedav/atlas-r2-qwen3-14b --local-dir /outputs/r2_qwen3_14b_finetuned

# DeepSeek-R1-8B Finanzas
huggingface-cli download Rafaelcedav/atlas-finanzas-deepseek-r1-8b --local-dir /outputs/atlas_deepseek_r1_8b
```

---

## 11. Lanzar training (proximos modelos)

### Patron general — SIEMPRE usar estos flags en ROCm:

```python
# En el script de training, OBLIGATORIO:
attn_implementation="eager"   # sdpa tiene bug NaN en ROCm + bf16
optim="adamw_torch"           # paged_adamw_8bit no funciona en ROCm
dataloader_pin_memory=False   # evita SIGKILL por pin de RAM
bf16=True                     # NO usar fp16 en MI300X
gradient_checkpointing=True   # necesario para modelos grandes
```

### Lanzar en background:

```bash
source /root/atlas_r2_env/bin/activate
cd /root/atlas_r2
nohup python3 finetune_NOMBRE.py > /root/training_NOMBRE.log 2>&1 &
echo "PID: $!"

# Ver progreso:
tail -f /root/training_NOMBRE.log
```

---

## 12. Proximos modelos a entrenar (en orden)

| Modelo | Script | VRAM est. | ETA |
|--------|--------|-----------|-----|
| Legal MX+USA (Mistral-7B) | por crear | ~97 GB | ~40 min |
| Coding (Qwen2.5-Coder-7B) | por crear | ~97 GB | ~40 min |
| Orquestacion (Llama-3.2-3B) | por crear | ~42 GB | ~20 min |
| Consejero (Qwen3-8B) | por crear | ~111 GB | ~40 min |
| Trading (DeepSeek-R1-8B) | por crear | ~111 GB | ~40 min |

> Mistral-7B + Qwen2.5-Coder-7B pueden correr SIMULTANEAMENTE (~194 GB total).
> Llama-3.2-3B puede correr EN PARALELO con cualquiera de los de arriba.

---

## 13. Generar dataset legal sin API (Opcion local)

El plan para mañana — usar el modelo ya entrenado para generar datos desde los docs legales:

```bash
# Los documentos fuente estan en:
# D:\Proyectos\atlas-amd-hackathon\docs\dataset_raw\MX\
# D:\Proyectos\atlas-amd-hackathon\docs\dataset_raw\USA\

# Script por crear: scripts/generate_legal_dataset_local.py
# Usa el modelo local (DeepSeek o Qwen) en el GPU para generar QA pairs
# Sin API, sin costo, con los .txt legales como seed
```

---

## 14. Monitoreo

```bash
# VRAM en tiempo real:
watch -n 2 rocm-smi --showmeminfo vram

# Loss en tiempo real:
tail -f /root/training_NOMBRE.log | grep "loss"

# Checkpoints guardados:
ls -lt /outputs/NOMBRE_modelo/
```

---

## Variables de referencia

| Variable | Valor |
|----------|-------|
| GPU IP anterior | 134.199.201.13 (destruida) |
| SSH Key | .ssh/atlas_r2_key |
| HF Username | Rafaelcedav |
| Dataset local | Trainning_Steps/atlas_training_dataset_final.jsonl |
| Dataset GPU | /data/atlas_training_dataset.jsonl |
| Modelo 14B HF | Rafaelcedav/atlas-r2-qwen3-14b |
| Modelo 8B HF | Rafaelcedav/atlas-finanzas-deepseek-r1-8b |
