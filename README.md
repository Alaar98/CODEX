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
- `outputs/trace_nominal_size_vs_altitude.png`: mapa tamaño–altitud con conteos.
- `outputs/trace_nominal_inclination_vs_altitude.png`: inclinación–altitud con conteos.
- `outputs/trace_nominal_inclination_histogram.png`: histograma de inclinación.
- `outputs/trace_nominal_altitude_histogram.png`: histograma de altitud por tamaño.
- `outputs/trace_nominal_semi_major_axis_*.png`: semieje mayor.
- `outputs/trace_nominal_eccentricity_*.png`: excentricidad.
- `outputs/trace_nominal_raan_*.png`: RAAN.
- `outputs/trace_nominal_argument_of_perigee_*.png`: argumento del perigeo.
- `outputs/trace_nominal_mean_anomaly_*.png`: anomalía media.
- `data/generated/figure_manifest.json`: variables disponibles y conteos de los mapas.

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

## Poblaciones para sensibilidad orbital

La población existente `data/generated/trace_population_50000.csv` sigue siendo
**la nominal**, sin modificar. En `data/generated/sensitivity/` hay nueve
alternativas independientes de 50.000 objetos (CSV comprimidos con gzip):

| Variable modificada | Tres alternativas |
|---|---|
| Excentricidad | Circular, menor e, mayor e |
| RAAN | 12, 8 y 4 planos equiespaciados, sin dispersión |
| Argumento del perigeo | 12, 8 y 4 posiciones equiespaciadas, sin dispersión |

Son nueve alternativas **más** la nominal, no combinaciones de variables. Se
mantienen IDs, tamaños, a, i, M, epoch y marco. Se recalculan los ápsides y
estados; no se vuelve a muestrear i al cambiar e. En el caso circular, el
argumento de latitud u es uniforme y omega se conserva solo como convención
numérica, marcado como físicamente indefinido.

Las separaciones son 30°, 45° y 90°, desde 0° y sin duplicar 360°. Se reparten
los objetos por igual entre ángulos, salvo el redondeo inevitable: en 12 grupos
hay ocho de 4.167 y cuatro de 4.166 objetos; en 8 hay 6.250 por grupo y en 4,
12.500. La asignación a IDs es aleatoria reproducible y no añade jitter.

```bash
.venv/bin/python scripts/generate_sensitivity_populations.py
```

El manifiesto registra modelos, semillas, hashes y controles. Cada alternativa
tiene un JSON de auditoría; las gráficas comparativas y mapas de conteo están
en `outputs/sensitivity/`, sin sustituir los gráficos nominales. Las funciones
`load_population(Path(...))` de `space_debris_detection.sensitivity` leen tanto
CSV normales como CSV.gz. Véanse todos los parámetros y supuestos en las notas.
Las cifras de detección y calidad aún requieren el simulador de misión/óptica.

En `outputs/` solo se guardan PNG. Los nombres indican la población:
`trace_nominal_...`, `trace_raan_12_planes_...`, `trace_argp_8_positions_...`,
`trace_eccentricity_circular_...`, etc. Las comparaciones usan nombres como
`trace_comparison_nominal_raan_12_8_4_planes.png`.

## Estilo científico de las figuras

Todas las figuras nuevas usan el módulo compartido `plotting.py`: texto serif,
matemáticas Computer Modern, ejes con unidades y bins explícitos y PNG a
300 dpi. Los mapas usan la paleta `inferno_r`, escala logarítmica de
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

## Validación óptica y radiométrica inicial

```bash
.venv/bin/python scripts/generate_optical_validation.py
```

Lee directamente `docs/references/TRACE_Detector_Optical_Baseline (1).xlsx`,
valida unidades y genera 14 PNG en `outputs/optical/`, con tablas CSV, intervalos
JSON y manifiesto en `data/generated/optical/`. Los nombres incluyen
`instrument_reference`: estas gráficas son del instrumento, no resultados
de detecciones de una población concreta. No se alteran las diez poblaciones.

Incluye SNR–magnitud AB, SNR–distancia y distancia–tamaño, variando apertura,
FOV, velocidad transversal, albedo y fase. La referencia de estudio es el
punto medio de apertura/FOV del Excel, fase 60°, albedo nominal, velocidad
transversal de 5 km/s y observador circular a 450 km (hipótesis de prueba, no
arquitectura de misión adoptada). Se incluye el giro LVLH en el movimiento
aparente para una LOS al zenit y movimiento relativo en sentido along-track.

Los intervalos exigen SNR >= umbral y dominio de fuente
no resuelta y ausencia de saturación de carga. El Excel incluye ahora **15 ke⁻
por píxel en la ganancia más alta** y **>140 ke⁻ en la más baja**. El modo High
Gain utiliza el primer valor. La carga pico se integra por píxel para una PSF
gaussiana con traza; los CSV identifican saturación y el motivo del límite inferior.
**No incluyen saturación del ADC, sombra de la plataforma, eclipses,
accesibilidad orbital ni detecciones de misión**. Los alcances ópticos pueden
exceder las distancias físicamente disponibles entre objetos LEO: deben cruzarse
después con la geometría real. Los triángulos señalan alcance superior al
barrido de 20.000 km; no son máximos de detección calculados.

El modelo usa esfera lambertiana con albedo geométrico, fondo AB, espectro solar
de cuerpo negro normalizado y extracción de PSF gaussiana más traza. Las
hipótesis completas y la revisión dimensional de la ecuación (9) del paper
están en las notas. Se comprueban ecuaciones radiométricas del paper con una
extracción especificada; no se afirma reproducir íntegramente su figura 2.

## Excel de resultados y vistas resumidas

```bash
.venv/bin/python scripts/export_optical_results.py
```

Produce `data/generated/optical/TRACE_Resultados_Estudio_Optico.xlsx` con 854
casos únicos, todos a 450 km.
Una fila representa tamaño y configuración, consolidando referencias repetidas
entre barridos. Las dos últimas columnas de Casos son alcance mínimo y máximo
en km. Incluye Guía, Resumen_10cm, Casos e Intervalos.
Los máximos censurados y los huecos entre intervalos están identificados.

En `outputs/optical/summary/` se muestran ventanas de detección mediante barras
horizontales para 1, 10 y 100 cm, separando cada parámetro en un panel.
El sexto panel muestra la referencia a 450 km. Las poblaciones originales
permanecen intactas. Todavía no se comparan misiones completas.

## Comparación simultánea por tamaño e histograma nominal

```bash
.venv/bin/python scripts/plot_size_comparisons.py
```

Después de exportar el Excel, añade a ese archivo las hojas TamanosComparados
e IntervalosTamanos. Calcula exactamente 1, 5, 10 y 100 cm en los mismos casos
y crea dos versiones de la figura con cuatro barras por condición: azul,
verde, amarillo y morado. La escala lineal conserva la presentación original;
la logarítmica permite distinguir todos los tamaños sin aplastar los alcances
pequeños. Ambas incorporan malla fina y quedan en outputs/optical/summary.
Los casos se guardan en data/generated/optical/size_comparison_cases.csv.

El histograma `outputs/trace_nominal_object_size_histogram.png` cuenta todos
los objetos nominales: vista completa con bins logarítmicos y un detalle lineal
1–10 cm. Los conteos de cada bin están en data/generated/nominal_size_histogram.csv.

Se aceptan tránsitos parciales con SNR ≥ 5, siempre que no saturen y cumplan
el dominio no resuelto y la exclusión solar. La señal usa el tiempo visible
`min(exposición, cruce central)`; fondo y dark usan toda la exposición.
Se supone el máximo solapamiento temporal posible: no es una simulación de
instantes aleatorios de entrada al campo. La línea de tránsito completo es
solo informativa. El barrido actual va de 1 m a 20.000 km.

```bash
.venv/bin/python scripts/plot_unresolved_population.py
```

Genera `outputs/optical/summary/trace_nominal_unresolved_source_limit_observer_450km.png`
y un CSV con las distancias de los 50.000 objetos. Observador de referencia:
Estado inicial TEME=(6821,0,0) km en 2026-11-05T00:00:00Z. Incluye objetos ocultos por la
Tierra o fuera del campo. Verde identifica visibles y detectables (SNR ≥ 5,
no saturados y no resueltos); lila identifica visibles no detectables y gris el resto. Se supone órbita
ecuatorial circular prógrada, cámara al zenit, Sol aproximado y sombra
terrestre cilíndrica. El tiempo de señal se calcula para la exposición
centrada en la época seleccionada, admitiendo tránsitos parciales. Se propagan
observador y debris con un modelo de dos cuerpos durante una órbita del
observador y se selecciona el máximo de visibles en una malla de 15 s
(empate: el primero; no se selecciona por SNR). El barrido queda en
`data/generated/optical/snapshot_epoch_scan_450km.csv`. La instantánea elegida
es 2026-11-05T01:23:15Z: 13 visibles no detectables (lila), 0 detectables
(verde), 49.987 restantes (gris). Es una instantánea seleccionada para
visualización, no un conteo acumulado ni una tasa media de misión.
Las posiciones propagadas se expresan en los ejes TEME fijos de la época
nominal; se omiten J2, arrastre y precesión durante este barrido corto.
El umbral nominal es FWHM×δ = 0,000113165494 rad = 23,3421 arcsec.
La línea roja es d[cm]=11,3165494 r[km]; la zona inferior sombreada es no resuelta.

## Alcance de los modelos iniciales anteriores

Los modelos iniciales `radiometry.py` y `examples/first_order_budget.py` son
aproximaciones ilustrativas de primer orden en unidades SI.
El ejemplo toma una irradiancia arbitraria: todavía no modela la reflexión del
objeto, su distancia, las órbitas, la iluminación, la cobertura ni la probabilidad
de detección. Su SNR no demuestra viabilidad de una misión real.

El modelo radiométrico supone una longitud de onda representativa y extracción
de toda la señal; incluye ruido de Poisson de señal y fondo, y ruido de lectura.
Quedan pendientes la integración espectral, la corriente oscura, las pérdidas
por movimiento, la PSF, saturación y un criterio de detección con falsas alarmas.
