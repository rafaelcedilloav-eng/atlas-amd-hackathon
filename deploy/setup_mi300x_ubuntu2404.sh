C
C
C
C
C
Ce.
C
C

set -e  # Detenerse en cualquier error

echo "=========================================="
echo "  AMD MI300X SETUP - Ubuntu 24.04.4"
echo "  PyTorch + ROCm + Jupyter + QLoRA"
echo "=========================================="

# ============================================================
# PASO 0: PRE-REQUISITOS DEL SISTEMA
# ============================================================
# Ejecuta como root o con sudo. Verifica que tienes acceso GPU.

echo ""
echo "=== PASO 0: Verificar GPU y sistema ==="
echo "Verificando GPUs AMD..."

# Verificar que amd-smi existe (ROCm 6.4+)
if command -v amd-smi &> /dev/null; then
    amd-smi list
elif command -v rocm-smi &> /dev/null; then
    rocm-smi
else
    echo "⚠️  No se detecto amd-smi ni rocm-smi. ROCm podria no estar instalado."
    echo "Continuando con instalacion desde cero..."
fi

# Verificar arquitectura GPU (MI300X = gfx942)
echo ""
echo "Verificando arquitectura GPU..."
if command -v rocminfo &> /dev/null; then
    rocminfo | grep -E "Name:\s+gfx" | head -5
else
    echo "rocminfo no encontrado. Se instalara con ROCm."
fi

# ============================================================
# PASO 1: ACTUALIZAR SISTEMA E INSTALAR DEPENDENCIAS BASICAS
# ============================================================

echo ""
echo "=== PASO 1: Actualizar sistema e instalar dependencias ==="

sudo apt update && sudo apt upgrade -y

# Dependencias esenciales para ROCm, Docker, Python, compilacion
sudo apt install -y \
    wget \
    curl \
    git \
    vim \
    nano \
    htop \
    tmux \
    screen \
    build-essential \
    cmake \
    ninja-build \
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    python3-full \
    libjpeg-dev \
    libpng-dev \
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    llvm \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libxmlsec1-dev \
    liblzma-dev \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    pkg-config \
    libnuma-dev \
    libopenmpi-dev \
    openmpi-bin \
    openmpi-common

# ============================================================
# PASO 2: INSTALAR DOCKER (si no esta instalado)
# ============================================================
# Docker es el metodo RECOMENDADO por AMD para ROCm

echo ""
echo "=== PASO 2: Instalar Docker ==="

if ! command -v docker &> /dev/null; then
    echo "Docker no encontrado. Instalando..."
    
    # Eliminar versiones antiguas si existen
    for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do
        sudo apt remove -y $pkg 2>/dev/null || true
    done
    
    # Agregar repositorio oficial de Docker
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc
    
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "${VERSION_CODENAME}") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Agregar usuario actual al grupo docker
    sudo usermod -aG docker $USER
    echo "✅ Docker instalado. CIERRA Y VUELVE A ABRIR TU TERMINAL para que los grupos se apliquen."
    echo "   Luego ejecuta: newgrp docker"
    echo "   Y verifica con: docker run hello-world"
    exit 0
else
    echo "✅ Docker ya esta instalado: $(docker --version)"
    
    # Verificar que el usuario esta en grupo docker
    if ! groups $USER | grep -q '\bdocker\b'; then
        sudo usermod -aG docker $USER
        echo "⚠️  Agregado al grupo docker. CIERRA Y REABRE TERMINAL, luego: newgrp docker"
    fi
fi

# ============================================================
# PASO 3: PULL DE LA IMAGEN DOCKER OFICIAL AMD ROCm + PyTorch
# ============================================================
# Esta es la opcion RECOMENDADA por AMD. Todo pre-instalado y testeado.

echo ""
echo "=== PASO 3: Descargar imagen Docker AMD ROCm + PyTorch ==="
echo "Imagen: rocm/pytorch:rocm7.2_ubuntu24.04_py3.12_pytorch_release_2.9.1"
echo ""
echo "⏳ Esto descarga ~20-30GB. Toma un cafe..."

# Usar la imagen mas reciente compatible con MI300X (gfx942)
# Basado en documentacion AMD oficial
docker pull rocm/pytorch:rocm7.2_ubuntu24.04_py3.12_pytorch_release_2.9.1

echo "✅ Imagen Docker descargada."

# ============================================================
# PASO 4: LANZAR CONTENEDOR DOCKER CON ACCESO GPU
# ============================================================

echo ""
echo "=== PASO 4: Lanzar contenedor Docker con acceso GPU ==="
echo ""
echo "Creando directorios de trabajo..."

# Crear directorios en host para persistencia
mkdir -p ~/mi300x-work/{notebooks,data,models,checkpoints,logs,scripts}
mkdir -p ~/mi300x-work/.jupyter
mkdir -p ~/mi300x-work/.cache/huggingface
mkdir -p ~/mi300x-work/.config/huggingface

# Script de lanzamiento del contenedor
cat > ~/mi300x-work/launch_container.sh << 'EOF'
#!/bin/bash
# Script para lanzar el contenedor MI300X

IMAGE="rocm/pytorch:rocm7.2_ubuntu24.04_py3.12_pytorch_release_2.9.1"
NAME="mi300x-training"
WORK_DIR="$HOME/mi300x-work"

# Detener contenedor existente si hay
if docker ps -a --format '{{.Names}}' | grep -q "^${NAME}$"; then
    echo "Deteniendo contenedor existente..."
    docker stop $NAME 2>/dev/null || true
    docker rm $NAME 2>/dev/null || true
fi

echo "Lanzando contenedor MI300X..."
echo "  - Jupyter en puerto 8888"
echo "  - Acceso a todas las GPUs"
echo "  - Memoria compartida 128GB"
echo "  - Directorios montados: notebooks, data, models, checkpoints"

docker run -d \
    --name $NAME \
    --cap-add=SYS_PTRACE \
    --security-opt seccomp=unconfined \
    --device=/dev/kfd \
    --device=/dev/dri \
    --group-add video \
    --group-add render \
    --ipc=host \
    --network=host \
    --shm-size=128G \
    --privileged \
    -v ${WORK_DIR}/notebooks:/workspace/notebooks \
    -v ${WORK_DIR}/data:/workspace/data \
    -v ${WORK_DIR}/models:/workspace/models \
    -v ${WORK_DIR}/checkpoints:/workspace/checkpoints \
    -v ${WORK_DIR}/logs:/workspace/logs \
    -v ${WORK_DIR}/scripts:/workspace/scripts \
    -v ${WORK_DIR}/.jupyter:/root/.jupyter \
    -v ${WORK_DIR}/.cache/huggingface:/root/.cache/huggingface \
    -v ${WORK_DIR}/.config/huggingface:/root/.config/huggingface \
    -e HF_HOME=/root/.cache/huggingface \
    -e HUGGINGFACE_HUB_CACHE=/root/.cache/huggingface \
    -e PYTORCH_HIP_ALLOC_CONF=expandable_segments:True \
    -e HIP_VISIBLE_DEVICES=0,1,2,3 \
    -e TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1 \
    $NAME \
    tail -f /dev/null

echo "✅ Contenedor lanzado: $NAME"
echo ""
echo "Para entrar al contenedor:"
echo "  docker exec -it $NAME bash"
echo ""
echo "Para ver logs:"
echo "  docker logs -f $NAME"
EOF

chmod +x ~/mi300x-work/launch_container.sh

echo "Ejecutando launch_container.sh..."
bash ~/mi300x-work/launch_container.sh

echo ""
echo "✅ Contenedor lanzado. Verificando estado..."
docker ps --filter name=mi300x-training --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# ============================================================
# PASO 5: VERIFICAR PyTorch Y GPUs DENTRO DEL CONTENEDOR
# ============================================================

echo ""
echo "=== PASO 5: Verificar PyTorch y GPUs dentro del contenedor ==="

docker exec mi300x-training bash -c "
    echo '--- Verificando PyTorch ---'
    python3 -c 'import torch; print(f"PyTorch version: {torch.__version__}")'
    
    echo ''
    echo '--- Verificando GPUs disponibles ---'
    python3 -c 'import torch; print(f"CUDA/ROCm available: {torch.cuda.is_available()}"); print(f"GPU count: {torch.cuda.device_count()}"); [print(f"GPU {i}: {torch.cuda.get_device_name(i)}") for i in range(torch.cuda.device_count())]'
    
    echo ''
    echo '--- Verificando ROCm ---'
    python3 -c 'import torch; print(f"ROCm build: {torch.version.hip}")'
    
    echo ''
    echo '--- Verificando arquitectura ---'
    rocminfo | grep -E 'Name:\\s+gfx' | head -5
"

# ============================================================
# PASO 6: INSTALAR JUPYTER LAB Y EXTENSIONES
# ============================================================

echo ""
echo "=== PASO 6: Instalar Jupyter Lab y configurar ==="

docker exec mi300x-training bash -c "
    pip install --upgrade pip
    pip install \
        jupyterlab \
        jupyterlab-git \
        jupyterlab-widgets \
        ipywidgets \
        notebook \
        nbclassic \
        jupyter-server-proxy \
        jupyterlab-code-formatter \
        black \
        isort
    
    # Generar config de Jupyter
    jupyter lab --generate-config
"

# Configurar Jupyter para acceso remoto seguro
cat > ~/mi300x-work/.jupyter/jupyter_lab_config.py << 'EOF'
c.ServerApp.ip = '0.0.0.0'
c.ServerApp.port = 8888
c.ServerApp.open_browser = False
c.ServerApp.allow_root = True
c.ServerApp.token = ''  # Sin token para desarrollo local. EN PRODUCCION USA CONTRASENA
c.ServerApp.password = ''
c.ServerApp.allow_origin = '*'
c.ServerApp.disable_check_xsrf = True
c.ServerApp.root_dir = '/workspace'
c.ServerApp.notebook_dir = '/workspace/notebooks'
c.ServerApp.max_buffer_size = 2147483647
c.MappingKernelManager.cull_idle_timeout = 43200  # 12 horas
c.NotebookApp.shutdown_no_activity_timeout = 43200
EOF

# ============================================================
# PASO 7: INSTALAR LIBRERIAS PARA QLoRA / ENTRENAMIENTO LLMs
# ============================================================

echo ""
echo "=== PASO 7: Instalar librerias de entrenamiento (QLoRA) ==="

docker exec mi300x-training bash -c "
    echo 'Instalando transformers, datasets, accelerate...'
    pip install \
        transformers \
        datasets \
        accelerate \
        peft \
        trl \
        bitsandbytes \
        scipy \
        sentencepiece \
        protobuf \
        huggingface-hub \
        tokenizers \
        safetensors \
        einops \
        xformers \
        wandb \
        tensorboard \
        mlflow \
        deepspeed \
        flash-attn \
        packaging \
        ninja
    
    echo ''
    echo '--- Verificando instalaciones ---'
    python3 -c 'import transformers; print(f"transformers: {transformers.__version__}")'
    python3 -c 'import peft; print(f"peft: {peft.__version__}")'
    python3 -c 'import trl; print(f"trl: {trl.__version__}")'
    python3 -c 'import bitsandbytes; print(f"bitsandbytes: OK")'
    python3 -c 'import accelerate; print(f"accelerate: {accelerate.__version__}")'
"

# ============================================================
# PASO 8: INSTALAR BITSANDBYTES ESPECIFICO PARA ROCm (CRITICO)
# ============================================================
# bitsandbytes oficial NO funciona con ROCm. Necesitas el fork de AMD.

echo ""
echo "=== PASO 8: Instalar bitsandbytes ROCm (CRITICO para QLoRA) ==="

docker exec mi300x-training bash -c "
    cd /tmp
    rm -rf bitsandbytes
    git clone --recurse-submodules https://github.com/ROCm/bitsandbytes.git
    cd bitsandbytes
    git checkout rocm_enabled_multi_backend
    
    pip install -r requirements-dev.txt
    
    # Compilar especificamente para MI300X (gfx942)
    cmake -DBNB_ROCM_ARCH='gfx942' -DCOMPUTE_BACKEND=hip -S .
    python setup.py install
    
    echo '--- Verificando bitsandbytes ROCm ---'
    python3 -c 'import bitsandbytes; print(f"bitsandbytes ROCm: OK")'
    python3 -c 'import bitsandbytes.cextension; bitsandbytes.cextension.load_cuda_lib(); print("CUDA/HIP lib cargada correctamente")'
"

# ============================================================
# PASO 9: CONFIGURAR HUGGING FACE
# ============================================================

echo ""
echo "=== PASO 9: Configurar Hugging Face ==="
echo "Necesitas un token de Hugging Face para descargar modelos como Llama."
echo "Obten uno en: https://huggingface.co/settings/tokens"
echo ""

# Crear script de login
cat > ~/mi300x-work/scripts/hf_login.sh << 'EOF'
#!/bin/bash
# Ejecutar esto DENTRO del contenedor para hacer login en HF
read -sp "Introduce tu HuggingFace token: " HF_TOKEN
echo
huggingface-cli login --token $HF_TOKEN --add-to-git-credential
echo "✅ Login completado."
EOF

chmod +x ~/mi300x-work/scripts/hf_login.sh

echo "Para hacer login en HF, ejecuta DENTRO del contenedor:"
echo "  bash /workspace/scripts/hf_login.sh"
echo ""

# ============================================================
# PASO 10: CREAR SCRIPT DE LANZAMIENTO DE JUPYTER
# ============================================================

echo ""
echo "=== PASO 10: Crear script de lanzamiento Jupyter ==="

cat > ~/mi300x-work/scripts/start_jupyter.sh << 'EOF'
#!/bin/bash
# Script para iniciar Jupyter Lab en el contenedor

echo "Iniciando Jupyter Lab..."
echo "Accede en tu navegador a: http://$(hostname -I | awk '{print $1}'):8888"
echo ""

# Variables de entorno optimas para MI300X
export PYTORCH_HIP_ALLOC_CONF=expandable_segments:True
export TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1
export HIP_VISIBLE_DEVICES=0,1,2,3

# Iniciar Jupyter Lab
jupyter lab \
    --config=/root/.jupyter/jupyter_lab_config.py \
    --allow-root \
    --no-browser \
    --ip=0.0.0.0 \
    --port=8888 \
    --NotebookApp.token='' \
    --NotebookApp.password=''
EOF

chmod +x ~/mi300x-work/scripts/start_jupyter.sh

echo "✅ Script creado: ~/mi300x-work/scripts/start_jupyter.sh"

# ============================================================
# PASO 11: SCRIPT DE TEST GPU (VERIFICACION FINAL)
# ============================================================

echo ""
echo "=== PASO 11: Crear script de test GPU ==="

cat > ~/mi300x-work/scripts/test_gpu.py << 'EOF'
#!/usr/bin/env python3
"""
Test completo de GPUs AMD MI300X
Ejecutar: python /workspace/scripts/test_gpu.py
"""
import torch
import sys

print("="*60)
print("TEST DE GPUs AMD MI300X")
print("="*60)

# 1. Verificar PyTorch y ROCm
print("\n[1] PyTorch version:", torch.__version__)
print("    ROCm/HIP version:", torch.version.hip)

# 2. Verificar GPUs
print("\n[2] Verificando GPUs...")
if not torch.cuda.is_available():
    print("❌ ERROR: No se detectaron GPUs!")
    sys.exit(1)

gpu_count = torch.cuda.device_count()
print(f"    GPUs detectadas: {gpu_count}")

for i in range(gpu_count):
    name = torch.cuda.get_device_name(i)
    mem = torch.cuda.get_device_properties(i).total_memory / 1024**3
    print(f"    GPU {i}: {name} | Memoria: {mem:.1f} GB")

# 3. Test de memoria
print("\n[3] Test de asignacion de memoria...")
try:
    for i in range(gpu_count):
        torch.cuda.set_device(i)
        # Asignar 10GB para test
        test_tensor = torch.zeros(10 * 1024**3 // 4, device=f'cuda:{i}')
        print(f"    GPU {i}: ✅ Asignados 10GB correctamente")
        del test_tensor
        torch.cuda.empty_cache()
except Exception as e:
    print(f"    ❌ Error en asignacion de memoria: {e}")

# 4. Test de operacion matmul (FP16)
print("\n[4] Test de operacion matmul FP16...")
try:
    device = torch.device('cuda:0')
    a = torch.randn(4096, 4096, device=device, dtype=torch.float16)
    b = torch.randn(4096, 4096, device=device, dtype=torch.float16)
    c = torch.matmul(a, b)
    print(f"    ✅ Matmul 4096x4096 FP16 exitoso. Resultado shape: {c.shape}")
except Exception as e:
    print(f"    ❌ Error en matmul: {e}")

# 5. Test de bf16 (soportado en MI300X)
print("\n[5] Test de bfloat16...")
try:
    x = torch.randn(1024, 1024, device='cuda:0', dtype=torch.bfloat16)
    y = torch.matmul(x, x.t())
    print(f"    ✅ bfloat16 soportado y funcionando")
except Exception as e:
    print(f"    ❌ Error bf16: {e}")

# 6. Verificar bitsandbytes
print("\n[6] Verificando bitsandbytes...")
try:
    import bitsandbytes as bnb
    print("    ✅ bitsandbytes importado correctamente")
except Exception as e:
    print(f"    ❌ Error importando bitsandbytes: {e}")

# 7. Verificar transformers
print("\n[7] Verificando transformers...")
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from trl import SFTTrainer
    print("    ✅ transformers, peft, trl importados correctamente")
except Exception as e:
    print(f"    ❌ Error: {e}")

print("\n" + "="*60)
print("TEST COMPLETADO")
print("="*60)
EOF

chmod +x ~/mi300x-work/scripts/test_gpu.py

echo "✅ Script de test creado."

# ============================================================
# PASO 12: EJECUTAR TEST INICIAL
# ============================================================

echo ""
echo "=== PASO 12: Ejecutar test inicial ==="
docker exec mi300x-training python3 /workspace/scripts/test_gpu.py

# ============================================================
# PASO 13: INICIAR JUPYTER LAB
# ============================================================

echo ""
echo "=== PASO 13: Iniciar Jupyter Lab ==="
echo ""

# Iniciar Jupyter en background dentro del contenedor
docker exec -d mi300x-training bash /workspace/scripts/start_jupyter.sh

sleep 3

# Verificar que Jupyter esta corriendo
echo "Verificando Jupyter..."
docker exec mi300x-training bash -c "jupyter lab list 2>/dev/null || ps aux | grep jupyter"

IP_HOST=$(hostname -I | awk '{print $1}')
echo ""
echo "=========================================="
echo "  ✅ JUPYTER LAB INICIADO"
echo "=========================================="
echo "  Accede en tu navegador:"
echo "  http://${IP_HOST}:8888"
echo ""
echo "  O desde tu maquina local con SSH tunnel:"
echo "  ssh -L 8888:localhost:8888 usuario@${IP_HOST}"
echo "=========================================="

# ============================================================
# PASO 14: TEMPLATE DE ENTRENAMIENTO QLoRA
# ============================================================

echo ""
echo "=== PASO 14: Crear template de entrenamiento QLoRA ==="

cat > ~/mi300x-work/notebooks/01_qlora_training_template.py << 'EOF'
#!/usr/bin/env python3
"""
TEMPLATE: Entrenamiento QLoRA en AMD MI300X
Configurado para 4 GPUs MI300X (192GB cada una = 768GB total)

Este script es un template. Adaptalo a tu dataset y modelo.
"""

import os
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    BitsAndBytesConfig,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training, TaskType
from trl import SFTTrainer
import wandb

# ============================================================
# CONFIGURACION
# ============================================================

# GPUs a usar (4x MI300X)
os.environ["CUDA_VISIBLE_DEVICES"] = "0,1,2,3"
os.environ["PYTORCH_HIP_ALLOC_CONF"] = "expandable_segments:True"
os.environ["TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL"] = "1"

# Modelo base (cambiar al que necesites)
MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"  # o "mistralai/Mistral-7B-Instruct-v0.3"

# Dataset (cambiar al tuyo)
DATASET_NAME = "tatsu-lab/alpaca"  # Reemplaza con tu dataset

# Configuracion QLoRA (4-bit)
BNB_CONFIG = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,      # Nested quantization
    bnb_4bit_quant_type="nf4",           # Normalized float 4
    bnb_4bit_compute_dtype=torch.bfloat16 # MI300X tiene excelente soporte bf16
)

# Configuracion LoRA
LORA_CONFIG = LoraConfig(
    r=64,                    # Rank (mayor = mas parametros, mas memoria)
    lora_alpha=16,           # Scaling factor
    target_modules=[         # Modulos a adaptar (varia segun modelo)
        "q_proj",
        "k_proj", 
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    ],
    lora_dropout=0.05,
    bias="none",
    task_type=TaskType.CAUSAL_LM,
)

# Hiperparametros de entrenamiento
TRAINING_ARGS = TrainingArguments(
    output_dir="/workspace/checkpoints/qlora-run-1",
    num_train_epochs=3,
    per_device_train_batch_size=4,      # Ajustar segun modelo y memoria
    per_device_eval_batch_size=4,
    gradient_accumulation_steps=4,      # Efectivo: 4*4*4 = 64 batch size
    optim="paged_adamw_8bit",           # Optimizer 8-bit para ahorrar memoria
    learning_rate=2e-4,
    warmup_ratio=0.03,
    weight_decay=0.001,
    max_grad_norm=0.3,
    logging_steps=10,
    save_strategy="steps",
    save_steps=100,
    evaluation_strategy="steps",
    eval_steps=100,
    bf16=True,                          # MI300X soporta bf16 nativamente
    tf32=True,
    dataloader_num_workers=4,
    remove_unused_columns=False,
    report_to="wandb",                # o "tensorboard"
    run_name="mi300x-qlora-experiment-1",
    # DeepSpeed (opcional, para multi-GPU avanzado)
    # deepspeed="/workspace/scripts/ds_config.json",
)

# ============================================================
# PREPARACION
# ============================================================

def setup():
    print(f"GPUs disponibles: {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
    
    # Login a wandb (opcional)
    # wandb.login()
    # wandb.init(project="mi300x-qlora", name=TRAINING_ARGS.run_name)

def load_model_and_tokenizer():
    print(f"\nCargando modelo: {MODEL_NAME}")
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=BNB_CONFIG,
        device_map="auto",              # Auto distribuye capas entre GPUs
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
        attn_implementation="flash_attention_2",  # Requiere flash-attn
    )
    
    # Preparar para QLoRA
    model = prepare_model_for_kbit_training(model)
    model = get_peft_model(model, LORA_CONFIG)
    
    print(f"Parametros entrenables: {model.print_trainable_parameters()}")
    
    return model, tokenizer

def format_dataset(examples):
    """Formatear dataset para entrenamiento. Adaptar segun tu dataset."""
    # Ejemplo para formato Alpaca
    if "instruction" in examples and "input" in examples and "output" in examples:
        texts = []
        for instruction, input_text, output in zip(examples["instruction"], examples["input"], examples["output"]):
            if input_text:
                text = f"### Instruction:\n{instruction}\n\n### Input:\n{input_text}\n\n### Response:\n{output}"
            else:
                text = f"### Instruction:\n{instruction}\n\n### Response:\n{output}"
            texts.append(text)
        return {"text": texts}
    return examples

def main():
    setup()
    
    # Cargar dataset
    print(f"\nCargando dataset: {DATASET_NAME}")
    dataset = load_dataset(DATASET_NAME, split="train[:1000]")  # Limitar para test
    dataset = dataset.map(format_dataset, batched=True)
    
    # Dividir en train/val
    dataset = dataset.train_test_split(test_size=0.1)
    
    # Cargar modelo
    model, tokenizer = load_model_and_tokenizer()
    
    # Configurar collator
    collator = DataCollatorForLanguageModeling(tokenizer, mlm=False)
    
    # Entrenador
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset["train"],
        eval_dataset=dataset["test"],
        args=TRAINING_ARGS,
        data_collator=collator,
        max_seq_length=2048,  # Ajustar segun modelo y memoria
    )
    
    # Entrenar
    print("\n🚀 Iniciando entrenamiento...")
    trainer.train()
    
    # Guardar modelo
    print("\n💾 Guardando modelo...")
    trainer.save_model("/workspace/models/qlora-final")
    tokenizer.save_pretrained("/workspace/models/qlora-final")
    
    print("\n✅ Entrenamiento completado!")

if __name__ == "__main__":
    main()
EOF

chmod +x ~/mi300x-work/notebooks/01_qlora_training_template.py

echo "✅ Template QLoRA creado en: ~/mi300x-work/notebooks/01_qlora_training_template.py"

# ============================================================
# PASO 15: CONFIG DE DEEPSPEED (OPCIONAL - MULTI-GPU)
# ============================================================

cat > ~/mi300x-work/scripts/ds_config.json << 'EOF'
{
    "bf16": {
        "enabled": true
    },
    "zero_optimization": {
        "stage": 2,
        "offload_optimizer": {
            "device": "cpu",
            "pin_memory": true
        },
        "allgather_partitions": true,
        "allgather_bucket_size": 2e8,
        "overlap_comm": true,
        "reduce_scatter": true,
        "reduce_bucket_size": 2e8,
        "contiguous_gradients": true
    },
    "train_batch_size": "auto",
    "train_micro_batch_size_per_gpu": "auto",
    "gradient_accumulation_steps": "auto",
    "optimizer": {
        "type": "AdamW",
        "params": {
            "lr": "auto",
            "betas": "auto",
            "eps": "auto",
            "weight_decay": "auto"
        }
    },
    "scheduler": {
        "type": "WarmupLR",
        "params": {
            "warmup_min_lr": "auto",
            "warmup_max_lr": "auto",
            "warmup_num_steps": "auto"
        }
    }
}
EOF

echo "✅ Config DeepSpeed creada."

# ============================================================
# RESUMEN FINAL Y TIPS
# ============================================================

echo ""
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           ✅ SETUP COMPLETADO - AMD MI300X                   ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║                                                              ║"
echo "║  📁 Directorio de trabajo: ~/mi300x-work/                    ║"
echo "║                                                              ║"
echo "║  🐳 Contenedor Docker: mi300x-training                      ║"
echo "║     Entrar: docker exec -it mi300x-training bash            ║"
echo "║                                                              ║"
IP_HOST=$(hostname -I | awk '{print $1}')
echo "║  📓 Jupyter Lab: http://${IP_HOST}:8888                      ║"
echo "║                                                              ║"
echo "║  🔧 Scripts utiles:                                         ║"
echo "║     ~/mi300x-work/scripts/start_jupyter.sh                   ║"
echo "║     ~/mi300x-work/scripts/test_gpu.py                       ║"
echo "║     ~/mi300x-work/scripts/hf_login.sh                       ║"
echo "║                                                              ║"
echo "║  🧠 Template QLoRA:                                          ║"
echo "║     ~/mi300x-work/notebooks/01_qlora_training_template.py  ║"
echo "║                                                              ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  PROXIMOS PASOS:                                             ║"
echo "║  1. Entra al contenedor: docker exec -it mi300x-training bash"
echo "║  2. Login HF: bash /workspace/scripts/hf_login.sh           ║"
echo "║  3. Test GPUs: python /workspace/scripts/test_gpu.py        ║"
echo "║  4. Adapta el template QLoRA a tu dataset                  ║"
echo "║  5. Entrena! 🚀                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================
# TIPS Y TRUCOS PARA ENTRENAR 4 IAs ASAP EN MI300X
# ============================================================

echo ""
echo "=== 💡 TIPS Y TRUCOS PARA ENTRENAR 4 IAs ASAP ==="
echo ""
echo "1. PARALELO CON DEEPSPEED:"
echo "   - Usa torchrun para lanzar 4 entrenamientos paralelos"
echo "   - Ej: torchrun --nproc_per_node=1 train1.py &"
echo "         torchrun --nproc_per_node=1 train2.py &"
echo "         (una GPU por entrenamiento)"
echo ""
echo "2. MULTI-GPU POR ENTRENAMIENTO:"
echo "   - Para modelos grandes (70B+), usa FSDP o DeepSpeed ZeRO-3"
echo "   - Con 4 GPUs de 192GB puedes entrenar modelos hasta ~140B"
echo ""
echo "3. BATCH SIZE Y MEMORIA:"
echo "   - MI300X tiene 192GB HBM3 por GPU - aprovechalo"
echo "   - Con QLoRA 4-bit: batch_size=4, max_seq_length=4096"
echo "   - Con gradient_accumulation=4: batch efectivo = 16"
echo ""
echo "4. FLASH ATTENTION 2:"
echo "   - SIEMPRE usa attn_implementation=flash_attention_2"
echo "   - Ahorra ~30-40% memoria y es mas rapido"
echo ""
echo "5. MONITOREO:"
echo "   - amd-smi monitor -d 0,1,2,3 (temperatura, uso, memoria)"
echo "   - rocm-smi --showmeminfo (memoria detallada)"
echo "   - watch -n 1 amd-smi list (monitoreo en tiempo real)"
echo ""
echo "6. PERSISTENCIA:"
echo "   - Los modelos y checkpoints se guardan en ~/mi300x-work/"
echo "   - Los contenedores son efimeros, los datos NO"
echo ""
echo "7. REINICIAR CONTENEDOR:"
echo "   - docker restart mi300x-training"
echo "   - docker exec -it mi300x-training bash"
echo ""
echo "8. BACKUP CHECKPOINTS:"
echo "   - rsync -av ~/mi300x-work/checkpoints/ /backup/path/"
echo ""
echo "9. MODELOS RECOMENDADOS PARA QLoRA:"
echo "   - Llama-3.1-8B/70B (Meta)"
echo "   - Mistral-7B/Nemo-12B (Mistral AI)"
echo "   - Qwen2.5-7B/72B (Alibaba)"
echo "   - DeepSeek-R1-Distill (DeepSeek)"
echo ""
echo "10. DATASETS POPULARES:"
echo "   - tatsu-lab/alpaca (instrucciones)"
echo "   - mlabonne/orpo-dpo-mix-40k (preferencias)"
echo "   - trl-lib/ultrafeedback_binarized (RLHF)"
echo "   - Open-Orca/OpenOrca (chat)"
echo ""
echo "🚀 BUENA SUERTE CON TUS 4 IAs!"
