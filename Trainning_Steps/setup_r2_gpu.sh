#!/bin/bash
# ============================================================
# ATLAS R2 - GPU SETUP & DEPENDENCY INSTALLATION
# For AMD MI300X + ROCm 6.2 + Ubuntu 22.04
# ============================================================

set -e

echo "╔════════════════════════════════════════════════════════╗"
echo "║  ATLAS R2 - GPU SETUP FOR QWEN3-30B FINETUNE          ║"
echo "║  Target: Qwen3-30B FullFinetune (not LoRA)            ║"
echo "║  GPU: AMD MI300X + ROCm 6.2.0                         ║"
echo "║  Framework: PyTorch 2.3.0 + DeepSpeed                ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# ============================================================
# STEP 1: VERIFY GPU & ROCm
# ============================================================
echo "[1/6] Verifying GPU & ROCm installation..."
echo ""

if ! command -v rocm-smi &> /dev/null; then
    echo "❌ ROCm not found. Installing ROCm 6.2..."
    wget -q -O - https://repo.radeon.com/rocm/rocm.gpg.key | apt-key add -
    apt-get update
    apt-get install -y rocm-dkms=6.2.0.60200-1~22.04 rocm-libs=6.2.0.60200-1~22.04
else
    echo "✅ ROCm found:"
    rocm-smi --version | head -3
fi

echo ""
rocm-smi
echo ""

# ============================================================
# STEP 2: SYSTEM DEPENDENCIES
# ============================================================
echo "[2/6] Installing system dependencies..."
apt-get update
apt-get install -y \
    build-essential \
    cmake \
    git \
    curl \
    wget \
    python3.11-dev \
    python3-pip \
    libopenblas-dev \
    liblapack-dev \
    libblas-dev

echo "✅ System dependencies installed"
echo ""

# ============================================================
# STEP 3: PYTHON ENVIRONMENT
# ============================================================
echo "[3/6] Setting up Python environment..."

# Upgrade pip
pip install --upgrade pip setuptools wheel --break-system-packages

# Create virtual environment (optional but recommended)
if [ ! -d "/root/atlas_r2_env" ]; then
    python3.11 -m venv /root/atlas_r2_env
    echo "✅ Virtual environment created: /root/atlas_r2_env"
else
    echo "✅ Virtual environment already exists"
fi

# Activate venv
source /root/atlas_r2_env/bin/activate

echo ""

# ============================================================
# STEP 4: PYTORCH + ROCM
# ============================================================
echo "[4/6] Installing PyTorch 2.3.0 + ROCm 6.2..."

# Install PyTorch with ROCm backend
pip install torch==2.3.0 torchvision==0.18.0 torchaudio==2.3.0 \
    --index-url https://download.pytorch.org/whl/rocm6.2 \
    --break-system-packages

# Verify PyTorch & GPU
python3 << EOF
import torch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU count: {torch.cuda.device_count()}")
if torch.cuda.is_available():
    print(f"Current GPU: {torch.cuda.get_device_name(0)}")
    print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
EOF

echo "✅ PyTorch installed with ROCm 6.2"
echo ""

# ============================================================
# STEP 5: FINETUNING DEPENDENCIES
# ============================================================
echo "[5/6] Installing finetuning stack (DeepSpeed, Flash-Attention, etc)..."

# Install from requirements
cat > /tmp/requirements_r2.txt << 'REQUIREMENTS'
transformers==4.40.2
huggingface-hub==0.22.2
tokenizers==0.15.1
datasets==2.18.0
accelerate==0.27.2
deepspeed==0.14.2
bitsandbytes==0.43.0
peft==0.10.0
flash-attn==2.5.8
xformers==0.0.26
pandas==2.2.1
numpy==1.26.4
scipy==1.13.0
scikit-learn==1.4.2
tqdm==4.66.2
wandb==0.16.6
tensorboard==2.16.2
loguru==0.7.2
fastapi==0.109.2
uvicorn==0.27.0
pydantic==2.6.4
click==8.1.7
rich==13.7.0
python-dotenv==1.0.1
REQUIREMENTS

pip install -r /tmp/requirements_r2.txt --break-system-packages

# Build DeepSpeed with ROCm
pip install deepspeed --pre --break-system-packages

echo "✅ Finetuning stack installed"
echo ""

# ============================================================
# STEP 6: VERIFY INSTALLATION
# ============================================================
echo "[6/6] Verifying installation..."
echo ""

python3 << 'VERIFY_SCRIPT'
import torch
import transformers
import deepspeed
from torch.cuda import is_available, device_count

print("╔════════════════════════════════════════════════════════╗")
print("║               INSTALLATION VERIFICATION                ║")
print("╚════════════════════════════════════════════════════════╝")
print("")
print(f"✅ PyTorch: {torch.__version__}")
print(f"✅ Transformers: {transformers.__version__}")
print(f"✅ DeepSpeed: {deepspeed.__version__}")
print(f"✅ CUDA Available: {is_available()}")
print(f"✅ GPU Count: {device_count()}")

if is_available():
    print(f"✅ GPU Name: {torch.cuda.get_device_name(0)}")
    props = torch.cuda.get_device_properties(0)
    print(f"✅ GPU Memory: {props.total_memory / 1e9:.1f} GB")
    print(f"✅ GPU Compute Capability: {props.major}.{props.minor}")
    
    # Test basic tensor operation
    x = torch.randn(1000, 1000).cuda()
    y = torch.matmul(x, x)
    print(f"✅ Tensor operations: Working")
    print(f"✅ Test tensor shape: {y.shape}")

print("")
print("╔════════════════════════════════════════════════════════╗")
print("║        ✅ ALL SYSTEMS GO FOR R2 FINETUNE              ║")
print("╚════════════════════════════════════════════════════════╝")
VERIFY_SCRIPT

echo ""

# ============================================================
# FINAL NOTES
# ============================================================
echo "╔════════════════════════════════════════════════════════╗"
echo "║                   NEXT STEPS                            ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "1. Activate venv:"
echo "   source /root/atlas_r2_env/bin/activate"
echo ""
echo "2. Download Qwen3-30B model:"
echo "   huggingface-cli download Rafaelcedav/atlas-core-30b-q8"
echo ""
echo "3. Prepare dataset:"
echo "   Place atlas_training_dataset.jsonl in /data/"
echo ""
echo "4. Run finetuning script:"
echo "   python3 finetune_qwen3_30b.py"
echo ""
echo "5. Monitor training:"
echo "   tensorboard --logdir ./runs"
echo ""
echo "GPU SPECS:"
rocm-smi --showid --showproductname --showtemp --showmeminfo=vram
echo ""
echo "✅ Setup complete. Ready for R2!"
