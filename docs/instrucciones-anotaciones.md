# Guía de Anotaciones para Textos TTS

## Sistema de Anotaciones

Este sistema TTS soporta anotaciones de modos de voz usando tags XML-like para cambiar el modo de voz por segmento de texto.

## Sintaxis

```
<modo>texto aquí</modo>
```

## Modos Disponibles

| Modo | Descripción | Características |
|------|-------------|-----------------|
| `normal` | Voz base, sin efectos especiales | Tono natural y equilibrado |
| `whisper` | Susurro | Agudo, aireado, íntimo |
| `emphatic` | Énfasis | Fuerte, claro, importante |
| `radio` | Efecto radial | Como teléfono o interfono |
| `processed` | Procesado | Efecto laboratorio/robot |

## Reglas de Formato

### ✅ CORRECTO

```
Hello <whisper>secret</whisper> world
<emphatic>Importante</emphatic> y <radio>transmisión</radio>
Inicio <whisper>susurro</whisper> fin
```

### ❌ INCORRECTO

```
<!-- Tags sin cerrar -->
<whisper>texto

<!-- Tags anidados (no soportado) -->
<whisper><radio>texto</radio></whisper>

<!-- Espacios raros en tags -->
< whisper >texto</ whisper >
```

## Ejemplos de Uso

### Ejemplo 1: Narración Dramática

```
Era una noche oscura <whisper>y silenciosa</whisper> cuando de repente <emphatic>¡escuchamos un grito!</emphatic> Todo volvió a la calma <radio>según los reportes</radio>.
```

### Ejemplo 2: Instrucciones

```
<emphatic>Atención:</emphatic> Presione el botón rojo <whisper>suavemente</whisper> y espere <radio>confirmación por radio</radio>.
```

### Ejemplo 3: Diálogo

```
<whisper>¿Estás ahí?</whisper> preguntó ella. <emphatic>¡Sí, estoy aquí!</emphatic> respondió él <radio>desde la base</radio>.
```

### Ejemplo 4: Misterio

```
Caminaba por el pasillo <whisper>oscuro y silencioso</whisper> cuando <emphatic>¡una puerta se cerró de golpe!</emphatic> <whisper>¿Quién está ahí?</whisper> pregunté <radio>a la seguridad</radio>.
```

### Ejemplo 5: Ciencia Ficción

```
<radio>Iniciando secuencia de aterrizaje</radio>. <emphatic>¡Atención, impacto inminente!</emphatic> <whisper>Rezos no ayudarán ahora</whisper>. Sistemas <processed>críticamente dañados</processed>.
```

### Ejemplo 6: Audiolibro

```
<whisper>Querida Jane,</whisper> comenzó la carta. <emphatic>Debo confesarte algo importante:</emphatic> te he amado en silencio todos estos años. <radio>Fin de la transmisión</radio>.
```

### Ejemplo 7: Podcast

```
<emphatic>Bienvenidos a Misterios Sin Resolver!</emphatic> Hoy investigaremos <whisper>el enigma de las luces</whisper> que aparecieron <radio>según testigos</radio> sobre el lago.
```

### Ejemplo 8: Videojuego NPC

```
<whisper>Acércate, no quiero que nos escuchen</whisper>. <emphatic>El rey está en peligro!</emphatic> <radio>La guardia nos vigila</radio>. Debes llegar al castillo <whisper>antes del amanecer</whisper>.
```

### Ejemplo 9: Noticiero

```
<emphatic>Última hora:</emphatic> El presidente ha anunciado nuevas medidas. <radio>Según corresponsales</radio> en el lugar, la situación es <whisper>más grave de lo reportado</whisper>.
```

### Ejemplo 10: Terror

```
<whisper>No debimos venir aquí</whisper>. Algo se mueve <emphatic>en la oscuridad</emphatic>. <radio>¿Escuchaste eso?</radio> <whisper>Silencio, viene hacia nosotros</whisper>.
```

## Prompt para IA Generadora

Si quieres que una IA te ayude a generar textos con anotaciones, usa este prompt:

```
Vas a ayudarme a generar textos de prueba para un sistema TTS que soporta anotaciones de modos de voz.

## Sistema de Anotaciones
Sintaxis: <modo>texto aquí</modo>

## Modos Disponibles
- normal: Voz base
- whisper: Susurro (agudo, aireado)
- emphatic: Énfasis (fuerte, claro)
- radio: Efecto radial (teléfono)
- processed: Procesado (robot)

## Tu Tarea
Genera textos que:
1. Sean naturales y coherentes
2. Usen 2-3 modos diferentes por texto
3. Tengan 3-6 segmentos anotados
4. Los tags tengan sentido semántico

## Formato de Salida
- Título: Nombre descriptivo
- Texto: Con anotaciones completas
- Modos usados: Lista
- Descripción: Contexto
```

## Consejos para Mejores Resultados

1. **Coherencia semántica**: Los tags deben tener sentido con el contenido
   - ✅ ` <whisper>no nos deben escuchar</whisper>`
   - ❌ `<whisper>¡GRITO FUERTE!</whisper>`

2. **Longitud de segmentos**: Mantén segmentos de 3-15 palabras
   - ✅ `<whisper>se acercó lentamente</whisper>`
   - ❌ `<whisper>una oración extremadamente larga que pierde el efecto del susurro porque es demasiado extensa</whisper>`

3. **Puntuación dentro de tags**: La puntuación debe estar dentro del tag
   - ✅ `<emphatic>¡Cuidado!</emphatic>`
   - ❌ `<emphatic>¡Cuidado</emphatic>!`

4. **Espacios entre tags**: Deja espacios naturales entre segmentos
   - ✅ `Inicio <whisper>susurro</whisper> fin`
   - ❌ `Inicio<whisper>susurro</whisper>fin`

## Probar Textos

Usa el playground en `http://localhost:3000` para probar tus textos:

1. Copia el texto con anotaciones
2. Pega en el área de texto
3. Selecciona una voz
4. Click en "Generar Audio"
5. Escucha el resultado

## API Endpoint

```bash
curl -X POST http://localhost:3000/v1/text-to-speech/pMsXgVXv3BLzUgSXRplE \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello <whisper>world</whisper>"}' \
  -o audio.wav
```
