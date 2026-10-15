# OpenTwixtor

Alternativa open source al efecto **Twixtor**: slow motion y time remapping
generando frames intermedios con **flujo óptico** (Farneback, OpenCV).

> No está afiliado a RE:Vision Effects. Es una implementación independiente.

## Instalación

```bash
git clone https://github.com/TU_USUARIO/twixtor-open.git
cd twixtor-open
pip install -r requirements.txt
```

## Uso

Interfaz gráfica:

```bash
python twixtor.py
```

Línea de comandos:

```bash
python twixtor.py entrada.mp4 salida.mp4 --speed 0.25   # 4x más lento
python twixtor.py entrada.mp4 salida.mp4 --speed 2      # 2x más rápido
```

## Cómo funciona

1. Calcula el flujo óptico hacia adelante y hacia atrás entre dos frames.
2. Deforma (warp) ambos frames hacia el instante intermedio.
3. Mezcla los dos resultados para crear el frame nuevo.

## Limitaciones

- No conserva el audio (se puede agregar con `ffmpeg`).
- Artefactos en oclusiones y movimiento muy rápido.
- Velocidad constante; las rampas de velocidad son una mejora pendiente.

## Licencia

MIT
