# ATLAS — Frontend Master (AMD Edition)
## Next.js 16 + React 19 + TailwindCSS 4 + AMD Visual DNA

---

## CONTEXTO DEL SISTEMA

ATLAS es un pipeline de auditoría forense de documentos financieros. Utiliza DeepSeek-R1 corriendo en una GPU AMD MI300X para detectar fraudes. El frontend ha sido rediseñado bajo el **AMD Frontend Architect Skill**, priorizando una estética oscura, técnica y de alto rendimiento.

---

## ESTADO ACTUAL DEL FRONTEND (V1.1 - Post-Hackathon)

### Stack Tecnológico
- **Framework:** Next.js 16.2.4 (App Router)
- **Styling:** Tailwind CSS 4 (Usa `@import "tailwindcss"` en `globals.css`)
- **Visual DNA:** AMD Red (#ED1C24), Deep Black (#000000), JetBrains Mono para telemetría.
- **Tipografía:** `Space Grotesk` (Display) e `Inter` (UI).
- **Animaciones:** Framer Motion 12 (Precisión técnica).
- **Gráficas:** Recharts 3 (Customizados con el look de hardware AMD).

### Componentes Clave Actualizados
- **`UploadModal.tsx`:** Gestiona estados de `Subiendo_Binarios` -> `Ejecutando_Inferencia`. Muestra progreso lineal simulado durante los ~52s de inferencia.
- **`Sidebar.tsx`:** Navegación agresiva con monitor de hardware (AMD MI300X status simulated).
- **`SeverityBadge.tsx`:** Soporta severidades en ES/EN y añade pulso de alerta en casos críticos.
- **`ReasoningChain.tsx`:** Visualización de la cadena de pensamiento de DeepSeek-R1 con estilo de consola de depuración.

---

## CONFIGURACIÓN Y AUTENTICACIÓN

### `frontend/src/services/api.ts`
Todas las peticiones (excepto `/stats`) incluyen el header:
```typescript
"X-API-Key": process.env.NEXT_PUBLIC_API_KEY
```

### Variables de Entorno (`.env.local`)
```env
NEXT_PUBLIC_API_URL=http://localhost:8080
NEXT_PUBLIC_API_KEY=YOUR_ATLAS_API_KEY
NEXT_PUBLIC_SUPABASE_URL=tu_url_de_supabase
```

---

## FLUJO DE TRABAJO DEL FRONTEND

1. **Inferencia de Larga Duración:** El backend tarda ~52 segundos. El frontend muestra un estado de "Ejecutando_Inferencia" con feedback técnico constante.
2. **Polling de Resultados:** Si se accede a `/audits/[id]` y el status no es `COMPLETE`, el componente `AuditDetails` realiza polling cada 5 segundos.
3. **Manejo de Errores Técnicos:**
   - **401:** Error de API Key.
   - **413:** Archivo excede los 20MB.
   - **Custom:** Muestra el `detail` devuelto por el backend de FastAPI.

---

## NOTAS PARA FUTURAS RECONSTRUCCIONES

1. **Tailwind 4:** No buscar `tailwind.config.js`. Toda la configuración de temas (`@theme`) reside en `frontend/src/app/globals.css`.
2. **DNA AMD:** Mantener siempre el ratio de rojos quirúrgicos. No usar más de 3 acentos rojos por viewport para no diluir el impacto visual.
3. **Monospace:** Todos los IDs de documentos, valores numéricos y etiquetas de status deben usar `JetBrains Mono`.

*Documentación actualizada tras el cierre del proyecto ATLAS - 27 de Abril 2026*
