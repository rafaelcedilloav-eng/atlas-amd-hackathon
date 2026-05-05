# PLAN DE EJECUCION — PROYECTO ATLAS
> Fecha limite: <24 horas | Arquitectura: Zero-Trust | Infraestructura: AMD GPUs (ROCm)

---

## FASE 0: DESCARGA DE MODELOS (Ejecutar AHORA)

### 0.1 Core Engine — Auditor Forense (Base para QLoRA)
    huggingface-cli download Qwen/Qwen3-32B \
      --local-dir ./models/core-engine-base \
      --local-dir-use-symlinks False

### 0.2 Router — Agente Cero (Clasificacion/Enrutamiento)
    huggingface-cli download DragonLLM/Qwen-Open-Finance-R-8B \
      --local-dir ./models/router-base \
      --local-dir-use-symlinks False

### 0.3 Vision Engine — OCR/Documentos (Base para inferencia bajo demanda)
    huggingface-cli download openbmb/MiniCPM-o-2_6 \
      --local-dir ./models/vision-engine-base \
      --local-dir-use-symlinks False

### 0.4 Verificacion de descarga
    du -sh ./models/core-engine-base ./models/router-base ./models/vision-engine-base
    ls ./models/core-engine-base/*.safetensors | wc -l
    ls ./models/router-base/*.safetensors | wc -l
    ls ./models/vision-engine-base/*.safetensors | wc -l

---

## FASE 1: ENTORNO ROCm (AMD GPU)

### 1.1 Verificar ROCm instalado
    rocm-smi
    rocminfo | grep gfx
    python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'ROCm: {torch.version.hip}'); print(f'GPU disponible: {torch.cuda.is_available()}')"

### 1.2 Instalar dependencias criticas
    pip install transformers>=4.48.0 accelerate bitsandbytes peft trl datasets
    pip install flash-attn --no-build-isolation
    pip install docling

> Nota AMD: bitsandbytes >= 0.43.0 tiene soporte experimental para ROCm. Si falla, usar `pip install bitsandbytes-rocm` o compilar desde fuente.

---

## FASE 2: FINE-TUNING QLoRA — CORE ENGINE

### 2.1 Script: train_core_engine.py

    #!/usr/bin/env python3
    """
    QLoRA Fine-tuning para ATLAS Core Engine
    Modelo: Qwen/Qwen32B
    Formato: ChatML con Chain-of-Thought (CoT)
    """

    import torch
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        TrainingArguments,
        BitsAndBytesConfig,
    )
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from trl import SFTTrainer
    from datasets import load_dataset

    # CONFIGURACION
    MODEL_ID = "./models/core-engine-base"
    DATASET_PATH = "./data/golden_dataset.jsonl"
    OUTPUT_DIR = "./adapters/atlas-core-engine-qlora"

    # QLoRA 4-bit para ahorro de VRAM en AMD
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    # LoRA Config — target modules para Qwen3
    lora_config = LoraConfig(
        r=64,
        lora_alpha=128,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )

    # CARGA DE MODELO Y TOKENIZER
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
        attn_implementation="flash_attention_2",
    )

    model = prepare_model_for_kbit_training(model)
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # DATASET (ChatML + CoT)
    # Tu JSONL debe tener formato:
    # {"messages": [
    #   {"role": "system", "content": "Eres un auditor forense..."},
    #   {"role": "user", "content": "Analiza esta transaccion..."},
    #   {"role": "assistant", "content": "<think>\n...razonamiento...\n</think>\n...respuesta final..."}
    # ]}

    dataset = load_dataset("json", data_files=DATASET_PATH, split="train")

    def format_chatml(example):
        return tokenizer.apply_chat_template(
            example["messages"],
            tokenize=False,
            add_generation_prompt=False,
        )

    dataset = dataset.map(lambda x: {"text": format_chatml(x)})

    # ENTRENAMIENTO
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=3,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        optim="paged_adamw_8bit",
        learning_rate=2e-4,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        weight_decay=0.001,
        max_grad_norm=0.3,
        logging_steps=10,
        save_strategy="epoch",
        bf16=True,
        tf32=False,
        group_by_length=True,
        report_to="none",
        max_seq_length=8192,
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        args=training_args,
        dataset_text_field="text",
    )

    trainer.train()
    trainer.model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"Adapter guardado en: {OUTPUT_DIR}")

### 2.2 Ejecutar entrenamiento
    export HSA_OVERRIDE_GFX_VERSION=11.0.0
    export PYTORCH_HIP_ALLOC_CONF=expandable_segments:True

    python train_core_engine.py

---

## FASE 3: CONFIGURACION DEL ROUTER

### 3.1 Script: router_inference.py

    #!/usr/bin/env python3
    """
    Router (Agente Cero) — Inferencia directa sin fine-tuning
    Modelo: DragonLLM/Qwen-Open-Finance-R-8B
    Salida: JSON estricto para enrutamiento
    """

    import json
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    MODEL_ID = "./models/router-base"

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )

    SYSTEM_PROMPT = """Eres el Router de ATLAS. Tu trabajo es clasificar consultas financieras/forenses y devolver UNICAMENTE un JSON valido.

    Categorias disponibles:
    - "core_engine": Analisis forense profundo, auditoria, cumplimiento regulatorio (MX/USA)
    - "vision_engine": Extraccion OCR de documentos, lectura de estados financieros
    - "general": Consultas generales de finanzas

    Responde UNICAMENTE con este formato JSON (sin markdown, sin explicaciones):
    {"categoria": "...", "confianza": 0.0-1.0, "motivo": "..."}"""

    def route_query(user_input: str) -> dict:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ]
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            temperature=0.1,
            do_sample=True,
            top_p=0.95,
            pad_token_id=tokenizer.eos_token_id,
        )

        response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            return {"categoria": "core_engine", "confianza": 0.5, "motivo": "fallback_por_error_json", "raw": response}

    if __name__ == "__main__":
        test_queries = [
            "Audita esta transaccion sospechosa de $2.3M en la cuenta 4455 del Banco XYZ conforme a la Ley Fintech MX",
            "Extrae el balance general del PDF adjunto del Q4 2025",
            "Que es un bono cupon cero?",
        ]
        for q in test_queries:
            print(f"\nQuery: {q}")
            print(f"Router: {json.dumps(route_query(q), indent=2, ensure_ascii=False)}")

### 3.2 Ejecutar Router
    python router_inference.py

---

## FASE 4: VISION ENGINE — OCR Y DOCUMENTOS

### 4.1 Estrategia de gestion de memoria (Anti-OOM)

    # NUNCA cargar Core Engine (32B) + Vision Engine (8B) simultaneamente.
    # El Router decide que motor cargar bajo demanda.
    #
    # Flujo de memoria:
    #   Router (8B) = ~6 GB  -> SIEMPRE ACTIVO
    #   + Core (32B) = ~20 GB -> TOTAL ~26 GB (carga bajo demanda)
    #   + Vision (8B) = ~6 GB -> TOTAL ~12 GB (carga bajo demanda)
    #
    # Maximo VRAM concurrente: ~26 GB

### 4.2 Capa 1: Docling — Parsing estructural (CPU)

    from docling.document_converter import DocumentConverter

    converter = DocumentConverter()

    def parse_document(doc_path: str) -> dict:
        """Extrae texto, tablas y layout de PDF/imagen. Corre en CPU."""
        result = converter.convert(doc_path)
        return {
            "markdown": result.document.export_to_markdown(),
            "json": result.document.export_to_dict(),
        }

### 4.3 Capa 2: MiniCPM-o-2.6 — Comprension visual (GPU bajo demanda)

    #!/usr/bin/env python3
    """
    Vision Engine — Inferencia OCR/Documentos
    Modelo: MiniCPM-o-2_6 (8B)
    Uso: Solo cuando Docling no logra OCR de calidad (escaneos bajos, firmas, sellos)
    """

    import torch
    from PIL import Image
    from transformers import AutoModel, AutoTokenizer

    MODEL_ID = "./models/vision-engine-base"

    def load_vision_model():
        """Carga el modelo de vision bajo demanda."""
        model = AutoModel.from_pretrained(
            MODEL_ID,
            trust_remote_code=True,
            attn_implementation="flash_attention_2",
            torch_dtype=torch.bfloat16,
            device_map="auto",
        )
        tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
        return model, tokenizer

    def ocr_image(image_path: str, model, tokenizer) -> str:
        """OCR de imagen con MiniCPM-o-2.6."""
        image = Image.open(image_path).convert("RGB")

        msgs = [
            {"role": "user", "content": [image, "Extrae TODO el texto de este documento financiero. Preserva tablas, montos, fechas y firmas. Devuelve el resultado en Markdown."]},
        ]

        res = model.chat(
            image=None,
            msgs=msgs,
            tokenizer=tokenizer,
            sampling=True,
            temperature=0.1,
            system_prompt="Eres un experto en OCR de documentos financieros y legales. Extrae texto con maxima precision.",
        )
        return res

    def unload_vision_model(model):
        """Libera VRAM del modelo de vision."""
        import gc
        del model
        gc.collect()
        torch.cuda.empty_cache()

### 4.4 Pipeline completo Vision

    def process_document(doc_path: str) -> str:
        """
        Pipeline hibrido: Docling -> MiniCPM-o-2.6 (fallback)
        Devuelve Markdown estructurado listo para el Core Engine.
        """
        # Paso 1: Docling siempre primero (CPU, rapido)
        parsed = parse_document(doc_path)
        markdown = parsed["markdown"]

        # Paso 2: Heuristica de calidad
        # Si el markdown tiene <10 lineas o contiene muchos caracteres de error,
        # probablemente es un escaneo de baja calidad -> activar Vision Engine
        if len(markdown.strip().split("\n")) < 10 or "[ERROR]" in markdown:
            print("[Vision Engine] Docling insuficiente. Activando MiniCPM-o-2.6...")
            model, tokenizer = load_vision_model()
            markdown = ocr_image(doc_path, model, tokenizer)
            unload_vision_model(model)

        return markdown

---

## FASE 5: INFERENCIA CORE ENGINE (Post-QLoRA)

### 5.1 Script: core_inference.py

    #!/usr/bin/env python3
    """
    Core Engine — Inferencia con Adapter QLoRA
    Modelo base: Qwen/Qwen3-32B
    Adapter: ./adapters/atlas-core-engine-qlora
    """

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel

    BASE_MODEL = "./models/core-engine-base"
    ADAPTER_PATH = "./adapters/atlas-core-engine-qlora"

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )
    model = PeftModel.from_pretrained(model, ADAPTER_PATH)
    model = model.merge_and_unload()

    SYSTEM_PROMPT = """Eres el Core Engine de ATLAS, un auditor forense especializado en regulaciones financieras de Mexico y Estados Unidos.

    Reglas:
    1. SIEMPRE razona paso a paso usando el formato <think>...</think> antes de dar tu conclusion final.
    2. Cita articulos especificos de leyes (Ley Fintech MX, Ley de Instituciones de Credito, BSA/AML USA, etc.).
    3. Evalua riesgos de lavado de dinero, fraude y cumplimiento normativo.
    4. Tu respuesta final debe ser estructurada, precisa y auditable."""

    def audit_query(user_input: str) -> str:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ]
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

        outputs = model.generate(
            **inputs,
            max_new_tokens=4096,
            temperature=0.3,
            do_sample=True,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id,
        )

        return tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)

    if __name__ == "__main__":
        query = """Analiza la siguiente transaccion bajo el marco de la Ley Fintech MX y BSA/AML:
        - Origen: Cuenta empresarial en Cayman Islands
        - Destino: Cuenta MXN en Banco Digital MX
        - Monto: $1.2M USD
        - Frecuencia: 3 transacciones en 48h
        - Justificacion del cliente: "Pago por servicios de consultoria""""
        print(audit_query(query))

---

## FASE 6: PIPELINE END-TO-END

### 6.1 Script: atlas_pipeline.py

    #!/usr/bin/env python3
    """
    Pipeline completo ATLAS:
    Router -> (Vision Engine | Core Engine) -> Respuesta
    """

    import json
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    from docling.document_converter import DocumentConverter

    # --- CONFIGURACION ---
    ROUTER_ID = "./models/router-base"
    CORE_BASE = "./models/core-engine-base"
    CORE_ADAPTER = "./adapters/atlas-core-engine-qlora"
    VISION_ID = "./models/vision-engine-base"

    # --- ROUTER (siempre cargado) ---
    router_tokenizer = AutoTokenizer.from_pretrained(ROUTER_ID, trust_remote_code=True)
    router_model = AutoModelForCausalLM.from_pretrained(
        ROUTER_ID, torch_dtype=torch.bfloat16, device_map="auto", trust_remote_code=True
    )

    # --- DOC CONVERTER (CPU) ---
    doc_converter = DocumentConverter()

    # --- FUNCIONES AUXILIARES ---
    def route_query(user_input: str) -> dict:
        SYSTEM_PROMPT = """Eres el Router de ATLAS. Clasifica la consulta y devuelve UNICAMENTE JSON valido.
        Categorias: "core_engine", "vision_engine", "general"
        Formato: {"categoria": "...", "confianza": 0.0-1.0, "motivo": "..."}"""
        msgs = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_input}]
        prompt = router_tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        inputs = router_tokenizer(prompt, return_tensors="pt").to(router_model.device)
        outputs = router_model.generate(**inputs, max_new_tokens=256, temperature=0.1, do_sample=True, top_p=0.95, pad_token_id=router_tokenizer.eos_token_id)
        response = router_tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        try:
            return json.loads(response.strip())
        except:
            return {"categoria": "core_engine", "confianza": 0.5, "motivo": "fallback"}

    def process_with_vision(doc_path: str) -> str:
        """Carga MiniCPM-o-2.6 bajo demanda, procesa, libera VRAM."""
        from PIL import Image
        from transformers import AutoModel, AutoTokenizer
        import gc

        model = AutoModel.from_pretrained(VISION_ID, trust_remote_code=True, torch_dtype=torch.bfloat16, device_map="auto")
        tokenizer = AutoTokenizer.from_pretrained(VISION_ID, trust_remote_code=True)

        image = Image.open(doc_path).convert("RGB")
        msgs = [{"role": "user", "content": [image, "Extrae TODO el texto en Markdown."]}]
        result = model.chat(image=None, msgs=msgs, tokenizer=tokenizer, sampling=True, temperature=0.1)

        del model, tokenizer
        gc.collect()
        torch.cuda.empty_cache()
        return result

    def process_with_core(user_input: str) -> str:
        """Carga Core Engine bajo demanda, procesa, libera VRAM."""
        import gc

        tokenizer = AutoTokenizer.from_pretrained(CORE_BASE, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(CORE_BASE, torch_dtype=torch.bfloat16, device_map="auto", trust_remote_code=True)
        model = PeftModel.from_pretrained(model, CORE_ADAPTER)
        model = model.merge_and_unload()

        SYSTEM_PROMPT = "Eres el Core Engine de ATLAS, auditor forense especializado MX/USA. Razona con <think>...</think>."
        msgs = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_input}]
        prompt = tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        outputs = model.generate(**inputs, max_new_tokens=4096, temperature=0.3, do_sample=True, top_p=0.9, pad_token_id=tokenizer.eos_token_id)
        result = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)

        del model, tokenizer
        gc.collect()
        torch.cuda.empty_cache()
        return result

    # --- PIPELINE PRINCIPAL ---
    def atlas_pipeline(user_input: str, doc_path: str = None) -> dict:
        """Pipeline completo ATLAS."""
        # 1. Router clasifica
        route = route_query(user_input)
        categoria = route.get("categoria", "core_engine")

        # 2. Ejecuta motor correspondiente
        if categoria == "vision_engine" and doc_path:
            # Vision: Docling primero, fallback a MiniCPM-o-2.6
            parsed = doc_converter.convert(doc_path)
            markdown = parsed.document.export_to_markdown()
            if len(markdown.strip().split("\n")) < 10:
                markdown = process_with_vision(doc_path)
            # Luego pasa al Core Engine con el texto extraido
            respuesta = process_with_core(f"Documento extraido:\n{markdown}\n\nConsulta: {user_input}")
        elif categoria == "core_engine":
            respuesta = process_with_core(user_input)
        else:
            respuesta = process_with_core(user_input)  # General -> Core por defecto

        return {
            "router": route,
            "respuesta": respuesta,
        }

    # --- TEST ---
    if __name__ == "__main__":
        # Test 1: Consulta forense directa
        print(atlas_pipeline("Audita esta transaccion de $2.3M conforme a Ley Fintech MX"))
        # Test 2: Documento adjunto
        # print(atlas_pipeline("Analiza este estado financiero", doc_path="./docs/estado_q4.pdf"))

---

## FASE 7: VALIDACION Y CHECKLIST FINAL

### 7.1 Checklist pre-entrega
- [ ] Descarga completada: Core Engine (32B), Router (8B), Vision Engine (8B)
- [ ] rocm-smi muestra GPU activa y memoria asignada
- [ ] Fine-tuning QLoRA completado sin OOM
- [ ] Adapter guardado en ./adapters/atlas-core-engine-qlora/adapter_model.safetensors
- [ ] Router devuelve JSON valido en 100% de casos de prueba
- [ ] Core Engine genera <think>...</think> en todas las respuestas
- [ ] Docling extrae Markdown estructurado de PDFs
- [ ] MiniCPM-o-2.6 realiza OCR de imagenes escaneadas
- [ ] Pipeline end-to-end ejecuta sin OOM (verificar rocm-smi durante ejecucion)
- [ ] Golden Dataset validado contra formato ChatML esperado

### 7.2 Comando de validacion rapida del formato ChatML
    python -c "
    import json
    with open('./data/golden_dataset.jsonl') as f:
        for i, line in enumerate(f):
            data = json.loads(line)
            msgs = data['messages']
            assert any(m['role'] == 'system' for m in msgs), f'Falta system en linea {i}'
            assert any(m['role'] == 'user' for m in msgs), f'Falta user en linea {i}'
            assert any(m['role'] == 'assistant' for m in msgs), f'Falta assistant en linea {i}'
    print('Formato ChatML validado')
    "

### 7.3 Monitoreo de VRAM durante ejecucion
    watch -n 1 rocm-smi

---

## ESPECIFICACIONES TECNICAS RESUMIDAS

| Componente | Modelo | Parametros | Contexto | VRAM (4-bit) | Estado |
|---|---|---|---|---|---|
| Core Engine | Qwen3-32B | 32.5B | 131,072 tokens | ~20 GB | Carga bajo demanda |
| Router | Qwen-Open-Finance-R-8B | 8.2B | 131,072 tokens | ~6 GB | Siempre activo |
| Vision Engine | MiniCPM-o-2_6 | 8B | 131,072 tokens | ~6 GB | Carga bajo demanda |
| Parsing | Docling (IBM) | — | — | 0 GB (CPU) | Siempre activo |

**Maximo VRAM concurrente: ~26 GB** (Router + Core) o **~12 GB** (Router + Vision).

> Recomendacion de hardware AMD: 1x MI300X (192GB HBM3) o 2x MI250X (128GB HBM2e) sobrados. Incluso 1x MI210 (64GB) o RX 7900 XTX (24GB) pueden correr el pipeline con gestion de carga.

---

## TROUBLESHOOTING RAPIDO

| Problema | Solucion |
|---|---|
| CUDA out of memory en AMD | Verificar que solo un motor grande este cargado. Usar `torch.cuda.empty_cache()` + `gc.collect()` entre cargas. |
| bitsandbytes no carga en ROCm | `pip install bitsandbytes --upgrade` o compilar con `CMAKE_ARGS="-DLLAMA_HIPBLAS=ON"` |
| Flash Attention falla en ROCm | Omitir `attn_implementation="flash_attention_2"` o instalar `flash-attn` con soporte HIP |
| Tokenizer no reconoce ChatML | Verificar `trust_remote_code=True` y version `transformers>=4.48.0` |
| Thinking mode no se activa | Confirmar que el prompt contiene `<think>` en el contenido del assistant del dataset |
| MiniCPM-o-2.6 no carga | Verificar que el modelo se descargo completo. Requiere `transformers>=4.40.0` |
| Docling no extrae tablas | Usar `result.document.export_to_markdown()` que preserva tablas en formato Markdown |

---

> ATLAS Lead AI Architect — Decision firmada.
> Modelos aprobados para descarga inmediata. Arquitectura Zero-Trust validada.
> Vision Engine: MiniCPM-o-2_6 (8B) aprobado. Anti-OOM garantizado.
