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

La población y sus gráficos utilizan NumPy, Matplotlib y SGP4. La instalación utiliza
setuptools como herramienta de empaquetado. No requiere servicios ni claves.

## Población sintética ESA 2026

```bash
.venv/bin/python scripts/generate_population.py
```

Genera exactamente 50.000 objetos, de diámetro >=1 cm y altitud 200–2.000 km,
con semilla fija. Los resultados son:

- `data/generated/trace_population_50000.csv`: identificadores, tamaños, altitudes,
  seis elementos orbitales, posición/velocidad, epoch y marco, donantes,
  indicadores de extrapolación y pesos estadísticos.
- `data/generated/trace_population_metadata.json`: parámetros y trazabilidad.
- `data/generated/validation.json`: auditoría de consistencia del resultado.
- `outputs/trace_size_vs_altitude.png` y `.pdf`: mapa tamaño–altitud con conteos.
- `outputs/trace_inclination_vs_altitude.*`: inclinación–altitud con conteos.
- `outputs/trace_inclination_histogram.*`: histograma de inclinación.
- `outputs/trace_altitude_histogram.*`: histograma de altitud por clase de tamaño.
- `outputs/trace_semi_major_axis_*.{png,pdf}`: semieje mayor.
- `outputs/trace_eccentricity_*.{png,pdf}`: excentricidad.
- `outputs/trace_raan_*.{png,pdf}`: RAAN.
- `outputs/trace_argument_of_perigee_*.{png,pdf}`: argumento del perigeo.
- `outputs/trace_mean_anomaly_*.{png,pdf}`: anomalía media.
- `outputs/figure_manifest.json`: variables disponibles y conteos de los mapas.

Fuentes originales: `docs/references/`. Curvas extraídas: `data/reference/`.
Consultar **[Notas del Proyecto](Notas%20del%20Proyecto.md)** para las hipótesis.
La inclinación procede de la figura 3.3a del informe, condicionada en bandas de
40 km de perigeo. Los donantes de e/RAAN/omega se propagan con SGP4 a
**2026-11-05 00:00:00 UTC, marco TEME**. La anomalía media es sintética, uniforme.
Se guardan los seis elementos y estados cartesianos coherentes a esa época.
Es una población híbrida de estudio, no un catálogo MASTER.

## Referencias CelesTrak y reproducción completa

Los cinco CSV originales del usuario están en `data/raw/celestrak/`, con hashes
en `provenance.json`. Se utilizan los grupos FENGYUN 1C, IRIDIUM 33 y COSMOS
2251, cruzados con SATCAT; el GP de activos se archiva, pero no se usa como
donante. La reproducción funciona sin acceso a CelesTrak.

Para volver a filtrar, sincronizar, muestrear, dibujar y auditar:

```bash
bash scripts/reproduce_population.sh
```

Se filtran DEB/RB no operativos ni reentrados, geocéntricos, con GP dentro de
7 días de la época común y órbitas residentes en 200–2.000 km. Quedan **2.567
donantes**. Se propagan sus GP y se convierten los estados TEME a elementos
instantáneos antes de remuestrear conjuntamente `(e, RAAN, omega)`.

**Limitación importante:** son tres familias de fragmentación, no una muestra
representativa de toda la basura LEO. El 20,996 % de la población requiere
donantes fuera de +/-100 km de altitud; siete altitudes se ajustan menos de
1 km para respetar los ápsides. Estas decisiones y la transferencia desde
objetos catalogados a tamaños de 1–10 cm están detalladas en las notas.

El generador usa por defecto el catálogo de referencia incluido. La opción
`--inclination-only` solicita explícitamente una salida parcial. No se asigna
masa: faltan hipótesis de forma, densidad y relación área/masa.

## Estilo científico de las figuras

Todas las figuras nuevas usan el módulo compartido `plotting.py`: texto serif,
matemáticas Computer Modern, ejes con unidades y bins explícitos, PDF vectorial
y PNG a 300 dpi. Los mapas usan la paleta `inferno_r`, escala logarítmica de
conteos y celdas vacías blancas. El estilo matemático se renderiza con MathText:
no requiere una instalación LaTeX externa.

La reextracción opcional de figuras ESA necesita PyMuPDF (probado con 1.26.6):
`python scripts/extract_esa_inclination.py`. Generar la población desde los CSV
incluidos no necesita esa dependencia.

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
