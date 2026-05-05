# MANUAL DE OPERACIONES KIMI-K2 - MI300X DEPLOYMENT v3.11
**Protocolo AACDU v3.1**
**Clasificación: CRÍTICO - HARDWARE ACCELERATOR LIFECYCLE**

## 1. PRE-REQUISITOS
- Sistema operativo: Ubuntu 22.04 Jammy (kernel >= 5.16)
- Acceso root o sudo
- Conectividad de red al repo.radeon.com

## 2. VALIDACIÓN HARDWARE
- `lspci -nn | grep -i "accelerator\|display"` (Debe mostrar 8 dispositivos "AMD Accelerators")
- `ls /dev/dri/ | grep render | wc -l` (Debe ser 8)

## 3. INSTALACIÓN DE DRIVERS Y ROCM
- Purgar versiones previas: `apt purge -y rocm-* hip-* *opencl* amdgpu-* mesa-opencl-icd`
- Instalar drivers: `amdgpu-install --usecase=rocm --no-32 --no-dkms -y`
- Instalar stack ROCm 6.1.1: `apt install -y rocm-dev rocm-libs hip-dev miopen-hip rccl rocm-smi-lib`
- Configurar variables de entorno en `/etc/profile.d/rocm.sh`:
  ```bash
  export ROCM_PATH=/opt/rocm
  export PATH=$ROCM_PATH/bin:$PATH
  export LD_LIBRARY_PATH=$ROCM_PATH/lib:$LD_LIBRARY_PATH
  export HSA_ENABLE_SDMA=0
  ```

## 4. DOCKER Y ROCM CONTAINER RUNTIME
- Instalar Docker Engine y configurar runtime en `/etc/docker/daemon.json` para soportar dispositivos AMD.
- Alias recomendado para ejecutar contenedores con acceso a GPU:
  ```bash
  alias docker-mi300x="/usr/local/bin/roc-docker"
  ```
  *(Ver script de `roc-docker` en los logs del sistema)*

## 5. VALIDACIÓN DE RENDIMIENTO
- `rocm-smi --showtopo` (Validar topología Infinity Fabric)
- PyTorch test: `python -c "import torch; print(torch.cuda.is_available())"`
- vLLM test: `python -m vllm.entrypoints.openai.api_server --model ./model --gpu-memory-utilization 0.95`

---
*Referencia: Ver manual completo en el histórico de ejecución del agente Kimi-K2.*
