# TRACE

**Tracking and Reacquisition Architecture for Cooperative Estimation of
Uncorrelated Space Objects**

Proyecto en Python, sin IA, para estudiar la viabilidad de un concepto de
misión de detección de basura espacial. Combina análisis de misión,
optimización, óptica y radiometría.

## Inicio rápido

Requiere Python 3.11 o posterior. Desde la raíz del repositorio:

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
.venv/bin/python -m pip install -e .
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python examples/first_order_budget.py
```

La población y sus gráficos utilizan NumPy y Matplotlib. La instalación utiliza
setuptools como herramienta de empaquetado. No requiere servicios ni claves.

## Población sintética ESA 2026

```bash
.venv/bin/python scripts/generate_population.py
```

Genera exactamente 50.000 objetos, de diámetro >=1 cm y altitud 200–2.000 km,
con semilla fija. Los resultados son:

- `data/generated/trace_population_50000.csv`: identificadores, tamaños, altitudes,
  semiejes, excentricidades, epoch convencional y pesos estadísticos.
- `data/generated/trace_population_metadata.json`: parámetros y trazabilidad.
- `outputs/trace_size_vs_altitude.png` y `.pdf`: todos los objetos de la muestra.

Fuentes originales: `docs/references/`. Curvas extraídas: `data/reference/`.
Consultar **[Notas del Proyecto](Notas%20del%20Proyecto.md)** para las hipótesis.
Las órbitas circulares equivalentes aún no incluyen orientación ni fase: esta
entrega no permite calcular encuentros o cobertura y no es un catálogo MASTER.

## Organización

- `src/space_debris_detection/mission.py`: futuro análisis geométrico y de misión.
- `src/space_debris_detection/optimization.py`: futuros barridos y optimización.
- `src/space_debris_detection/optics.py`: apertura y límite de difracción.
- `src/space_debris_detection/radiometry.py`: señal y relación señal/ruido.
- `examples/first_order_budget.py`: presupuesto sintético ejecutable.
- `tests/`: comprobaciones de los modelos iniciales.
- `docs/mission_concept.md`: preguntas e hipótesis por concretar.

## Alcance actual

Los modelos implementados son aproximaciones de primer orden en unidades SI.
El ejemplo toma una irradiancia arbitraria: todavía no modela la reflexión del
objeto, su distancia, las órbitas, la iluminación, la cobertura ni la probabilidad
de detección. Su SNR no demuestra viabilidad de una misión real.

El modelo radiométrico supone una longitud de onda representativa y extracción
de toda la señal; incluye ruido de Poisson de señal y fondo, y ruido de lectura.
Quedan pendientes la integración espectral, la corriente oscura, las pérdidas
por movimiento, la PSF, saturación y un criterio de detección con falsas alarmas.
