# TRACE Mission Validation Simulator
## Especificación técnica para desarrollo en Python

**Proyecto:** TRACE — *Tracking and Reacquisition Architecture for Cooperative Estimation of Uncorrelated Space Objects*

**Propósito:** definir el baseline físico, matemático y de software para desarrollar las herramientas de Mission Analysis necesarias para validar la viabilidad de TRACE.

---

# 1. Objetivo general

Desarrollar un entorno de simulación modular en Python que permita estudiar de forma acoplada:

1. Las oportunidades geométricas de observación de una población de objetos orbitales.
2. La detectabilidad óptica de esos objetos para distintas configuraciones del instrumento.
3. El diseño de constelación que maximiza el número de observaciones útiles.
4. La probabilidad de readquisición del mismo objeto por dos o tres satélites.
5. La probabilidad de observación simultánea desde varios satélites.
6. La mejora de la determinación orbital y de la covarianza obtenida mediante observaciones multi-satélite.

Las preguntas principales que el simulador debe permitir responder son:

- ¿Qué tamaños de debris pueden observarse con un payload óptico de complejidad razonable?
- ¿A qué distancias pueden detectarse?
- ¿Cómo afectan el FOV, apertura y focal a la detectabilidad?
- ¿Cómo afecta la velocidad angular del objeto al streaking y al SNR?
- ¿Qué arquitectura orbital maximiza el número de objetos detectados?
- ¿Qué variables de la constelación tienen mayor impacto sobre el rendimiento?
- ¿Con qué frecuencia puede otro satélite volver a observar un objeto detectado?
- ¿Con qué frecuencia puede producirse una observación simultánea?
- ¿Cuánto mejora la incertidumbre orbital al pasar de una observación a dos o tres observaciones desde posiciones diferentes?
- ¿Cuál es el mejor compromiso entre número de detecciones, readquisición, calidad de la geometría y número de satélites?

El **motor de simulación deberá estar completamente desacoplado del visualizador**.

---

# 2. Fuentes de referencia del proyecto

El desarrollo utilizará dos documentos principales de entrada.

## 2.1 Especificación de misión

Archivo:

`TRACE_Mission_Validation_Specification.md`

Este documento define:

- arquitectura de software;
- metodología;
- modelos físicos;
- ecuaciones;
- secuencia de validación;
- KPIs;
- outputs;
- tests;
- lógica de simulación;
- requisitos de visualización.

---

## 2.2 Baseline del detector y sistema óptico

Archivo:

`TRACE_Detector_Optical_Baseline.xlsx`

Este workbook será la **source of truth para los valores numéricos asociados al detector, sistema óptico y assumptions de detectabilidad**.

Codex deberá consultar este fichero directamente cuando implemente la Optical Validation.

El workbook contiene las hojas:

- `Detector_Baseline`
- `Optica_Deteccion`
- `Notas`

Los valores numéricos contenidos en estas hojas no deberán duplicarse ni hardcodearse manualmente dentro del software.

---

# 3. Jerarquía de configuración

La jerarquía de parámetros será:

1. `TRACE_Detector_Optical_Baseline.xlsx`
2. `TRACE_Mission_Validation_Specification.md`
3. Configuración YAML/JSON de cada simulación.

Interpretación:

- **Excel** = valores baseline.
- **Markdown** = física, ecuaciones, metodología y requisitos.
- **YAML/JSON** = configuración concreta de un run y posibles overrides.

Si existe alguna discrepancia entre un valor numérico escrito accidentalmente en otro documento y el workbook Excel:

- utilizar el valor del Excel;
- reportar la discrepancia;
- no resolverla silenciosamente.

---

# 4. Carga de parámetros detector/óptica

Crear un módulo específico para cargar el baseline óptico.

Por ejemplo:

```text
trace/config/load_optical_baseline.py
```

El loader deberá:

- localizar `TRACE_Detector_Optical_Baseline.xlsx`;
- leer `Detector_Baseline`;
- leer `Optica_Deteccion`;
- validar parámetros obligatorios;
- validar unidades;
- detectar celdas vacías;
- detectar parámetros duplicados;
- convertir unidades a SI internamente cuando corresponda;
- producir mensajes de error claros.

No deberá utilizar valores default silenciosos si falta una variable requerida.

---

# 5. Modelos tipados de configuración

Los valores del workbook deberán cargarse en estructuras tipadas equivalentes a:

```text
DetectorConfig
OpticalSystemConfig
DetectionConfig
```

Se pueden utilizar:

- Pydantic;
- dataclasses;
- u otra solución tipada equivalente.

Estas configuraciones deberán ser utilizadas por el resto del simulador.

---

# 6. Runtime configuration

Aunque el Excel sea la fuente baseline, no es necesario leer el workbook continuamente durante una simulación.

Flujo recomendado:

```text
TRACE_Detector_Optical_Baseline.xlsx
        ↓
parameter loader
        ↓
validated configuration object
        ↓
optional YAML runtime configuration
        ↓
simulation engine
```

Se podrán generar configuraciones como:

```text
default_sensor.yaml
default_optics.yaml
```

pero deberán derivarse inicialmente del workbook.

Estos YAML podrán modificarse para:

- sensitivity analyses;
- trade studies;
- alternative detector cases;
- experiment configurations.

---

# 7. Trazabilidad de parámetros

Cada run deberá guardar:

```text
detector_source_file
detector_source_sheet
optics_source_file
optics_source_sheet
parameter_set_version
runtime_overrides
```

Por ejemplo:

```text
detector_source_file = TRACE_Detector_Optical_Baseline.xlsx
detector_source_sheet = Detector_Baseline
optics_source_sheet = Optica_Deteccion
```

Esto debe permitir reproducir exactamente cada resultado.

---

# 8. Secuencia general de validación

El desarrollo seguirá:

```text
Propagator validation
        ↓
Geometry Core
        ↓
Optical Validation
        ↓
Constellation Performance
        ↓
Reacquisition
        ↓
Orbit Determination
```

Conceptualmente:

**Geometría preliminar → Detectabilidad óptica → Optimización de constelación → Readquisición → Orbit Determination**

La optimización óptica no debe realizarse únicamente sobre ranges arbitrarios.

Primero deben generarse condiciones geométricas representativas mediante propagación orbital.

Del mismo modo, la constelación no debe optimizarse únicamente utilizando un tamaño mínimo de debris supuesto.

Las oportunidades geométricas deberán filtrarse posteriormente mediante el modelo real de detectabilidad.

---

# 9. Fase geométrica preliminar

El primer objetivo será generar oportunidades geométricas de observación para una o varias constelaciones preliminares.

Para cada cruce del FOV calcular:

- distancia sensor–debris;
- velocidad relativa;
- velocidad angular aparente;
- tiempo de permanencia en el FOV;
- ángulo de fase Sol–objeto–observador;
- estado de iluminación;
- ocultación terrestre;
- ángulo de exclusión solar;
- ángulo de exclusión terrestre;
- ángulo de exclusión lunar.

Estos resultados definirán el dominio real de operación del instrumento.

---

# 10. Población de objetos MASTER

Se utilizará una población derivada de ESA MASTER.

La base de datos proporcionada tendrá como mínimo:

- identificador;
- masa;
- diámetro equivalente;
- posición X;
- posición Y;
- posición Z;
- velocidad VX;
- velocidad VY;
- velocidad VZ.

El software deberá exigir o permitir configurar explícitamente:

- epoch;
- sistema de referencia;
- unidades.

Estos campos **no deberán asumirse silenciosamente**.

---

# 11. Funciones del population loader

El simulador deberá poder trabajar con:

- población completa;
- subconjuntos;
- muestras aleatorias;
- muestras estratificadas;
- selección por tamaño;
- selección por altitud;
- selección por inclinación.

Los estados cartesianos deberán poder convertirse a elementos orbitales osculadores.

---

# 12. Arquitectura híbrida de propagación orbital

Se utilizarán dos backends de propagación:

```text
FastJ2Propagator
OrekitPropagator
```

Ambos implementarán una interfaz común.

---

# 13. FastJ2Propagator

Será el motor principal para Mission Analysis y simulaciones masivas.

Debe implementar:

- dinámica Kepleriana;
- perturbación secular J2;
- operaciones vectorizadas;
- propagación eficiente de grandes poblaciones.

Se utilizará principalmente para:

- propagación de MASTER;
- Monte Carlo;
- design-space exploration;
- simulaciones de grandes poblaciones;
- búsqueda masiva de eventos geométricos.

La implementación deberá priorizar NumPy.

Numba podrá introducirse posteriormente si resulta necesario.

---

# 14. OrekitPropagator

Orekit se utilizará como **backend astrodinámico de referencia y mayor fidelidad**.

Se utilizará principalmente para:

- validar FastJ2Propagator;
- propagación precisa de satélites host;
- gestión de tiempos;
- escalas temporales;
- frames;
- transformaciones;
- Sol;
- Luna;
- eclipses;
- geometría de referencia;
- casos seleccionados de alta fidelidad;
- futura Orbit Determination.

No se utilizará inicialmente para propagar toda la población MASTER durante grandes Monte Carlo salvo que benchmarks posteriores indiquen que su rendimiento es suficiente.

---

# 15. Interfaz común de propagación

Conceptualmente:

```python
propagator.propagate(states, times)
```

Backends:

```text
fast_j2
orekit
```

El resto del software no deberá depender de la implementación concreta.

Crear:

```text
PropagatorBackend
```

y una factory equivalente a:

```text
PropagatorFactory
```

---

# 16. Cross-validation FastJ2 vs Orekit

Antes de utilizar FastJ2 para grandes poblaciones, realizar una validación cuantitativa.

Seleccionar órbitas representativas:

- diferentes altitudes;
- diferentes inclinaciones;
- diferentes RAAN;
- órbitas circulares;
- órbitas ligeramente excéntricas.

Propagar durante:

- una órbita;
- 6 horas;
- 24 horas.

---

# 17. Métricas de validación del propagador

Comparar:

- position error;
- velocity error;
- RAAN error;
- argument of perigee error;
- anomaly error;
- semimajor axis;
- eccentricity.

Cuando sea posible:

- error en entrada al FOV;
- error en salida del FOV;
- error en range;
- error en angular rate.

El error del FastJ2 deberá quedar cuantificado antes de ejecutar grandes Monte Carlo.

---

# 18. Frames, tiempo y efemérides

Utilizar preferentemente Orekit como referencia para:

- GCRF;
- EME2000;
- ITRF;
- transformaciones inercial ↔ terrestre;
- escalas temporales;
- posición del Sol;
- posición de la Luna;
- Earth orientation cuando sea necesario.

Crear wrappers TRACE propios.

El resto del software no debe llamar directamente a Orekit salvo mediante estos adapters.

---

# 19. Frame LVLH

La orientación del sensor se definirá respecto al frame local LVLH.

La referencia nominal será:

```text
zenith
```

Variables de orientación:

```text
along_track_offset_deg
cross_track_offset_deg
```

Todos los sensores de una configuración tendrán la misma orientación.

No existirán slews durante la simulación nominal.

Validar el LVLH frente a Orekit.

---

# 20. Modelo del detector

Los parámetros numéricos del detector deberán leerse exclusivamente de:

```text
TRACE_Detector_Optical_Baseline.xlsx
```

hoja:

```text
Detector_Baseline
```

Esta hoja contendrá entre otros:

- resolución;
- pixel pitch;
- dimensiones activas;
- quantum efficiency;
- banda espectral;
- integration time;
- read noise;
- dark current;
- modo conceptual;
- SNR threshold.

El código no deberá duplicar manualmente dichos valores.

---

# 21. Sistema óptico

Los parámetros y rangos numéricos del sistema óptico deberán leerse de:

```text
TRACE_Detector_Optical_Baseline.xlsx
```

hoja:

```text
Optica_Deteccion
```

Esta hoja incluye entre otros:

- FOV design range;
- aperture diameter design range;
- optical throughput;
- PSF model;
- PSF FWHM;
- optical background;
- photometric model;
- albedo scenarios;
- detector dimension usada para derivar focal;
- exclusion angle baselines.

---

# 22. Variables derivadas del sistema óptico

Determinadas variables no serán independientes.

En particular:

```text
focal_length
f_number
plate_scale
```

deberán calcularse automáticamente.

---

# 23. Relación FOV–focal

La focal se calculará mediante:

```text
f = W / [2 × tan(FOV/2)]
```

donde:

```text
W
```

será la dimensión del detector indicada en `TRACE_Detector_Optical_Baseline.xlsx` para este cálculo.

No permitir:

```text
FOV
focal length
detector size
```

como tres grados de libertad independientes.

---

# 24. F-number

Calcular:

```text
f_number = focal_length / aperture_diameter
```

La apertura será una variable de diseño dentro del rango establecido en el workbook.

---

# 25. Plate scale

Calcular a partir de:

- pixel pitch;
- focal length.

Por ejemplo:

```text
plate_scale ≈ pixel_pitch / focal_length
```

en rad/pixel para small-angle approximation.

También proporcionar:

```text
arcsec/pixel
```

como output de ingeniería.

---

# 26. Throughput, QE y banda espectral

Los valores numéricos deberán obtenerse del workbook.

El modelo deberá soportar:

- throughput espectral constante inicialmente;
- QE constante inicialmente;
- banda espectral top-hat inicialmente.

La arquitectura deberá permitir introducir posteriormente curvas espectrales reales.

---

# 27. PSF

El tipo y parámetros baseline de PSF deberán leerse del workbook.

El modelo baseline deberá soportar una PSF gaussiana.

El PSF FWHM deberá permanecer configurable para sensitivity analysis.

---

# 28. Modelo fotométrico del debris

El modelo baseline será el definido en el workbook y en esta especificación.

Inicialmente:

- objeto equivalente;
- reflexión Lambertiana;
- phase function Lambertiana.

La magnitud/flujo deberá depender como mínimo de:

- debris diameter;
- range;
- phase angle;
- albedo.

---

# 29. Albedo

Los escenarios numéricos de albedo deberán obtenerse de:

```text
TRACE_Detector_Optical_Baseline.xlsx
```

No hardcodear escenarios en el código.

El software deberá soportar al menos:

```text
pessimistic
nominal
optimistic
```

cuando aparezcan definidos en el workbook.

---

# 30. Modelo solar

Para el modelo físico se podrá utilizar:

- espectro AM0;
- o blackbody solar correctamente normalizado.

El cálculo se realizará únicamente sobre la banda definida por el workbook.

El modelo solar deberá encapsularse para permitir sustitución futura.

---

# 31. Background óptico

El background baseline deberá obtenerse del workbook.

No descomponer inicialmente entre:

- zodiacal light;
- earthshine;
- lunar background;
- stray light.

El parámetro deberá poder modificarse mediante runtime override.

---

# 32. Modelo de streak

La variable principal para el detector será la **velocidad angular aparente**.

Calcular:

```text
angular_displacement = angular_rate × integration_time
```

Convertir posteriormente mediante el plate scale a:

```text
streak_length_pixels
```

---

# 33. Características del streak

Para cada evento calcular:

- relative velocity;
- angular rate;
- angular displacement;
- streak length;
- PSF width;
- effective pixel footprint;
- total signal;
- integrated streak SNR.

No asumir que toda la señal está contenida en un único pixel.

---

# 34. Modelo SNR

La ecuación deberá incluir al menos:

- object electrons;
- optical background;
- dark current;
- read noise;
- effective number of pixels.

Conceptualmente:

```text
SNR =
N_obj /
sqrt(
    N_obj
    + N_background
    + N_dark
    + N_read_variance
)
```

donde los términos dependientes de píxeles deben utilizar el footprint efectivo del streak.

---

# 35. Threshold SNR

El threshold numérico de detección no deberá estar hardcodeado.

Debe cargarse desde:

```text
TRACE_Detector_Optical_Baseline.xlsx
```

La lógica será:

```text
SNR >= configured_SNR_threshold
```

---

# 36. Condiciones completas de detección

Un debris será considerado detectado únicamente cuando cumpla simultáneamente:

1. Está dentro del FOV.
2. Está iluminado por el Sol.
3. La LOS satélite–debris no está ocultada por la Tierra.
4. Cumple el threshold SNR definido en el workbook.
5. Cumple solar exclusion.
6. Cumple Earth exclusion.
7. Cumple Lunar exclusion.

Los valores numéricos de los exclusion angles deberán obtenerse del workbook.

---

# 37. Ángulos de exclusión

Para el baseline inicial calcular la separación entre la LOS satélite–debris y:

- dirección aparente al Sol;
- dirección al centro terrestre;
- dirección aparente a la Luna.

Las thresholds deberán obtenerse de:

```text
Optica_Deteccion
```

Mantener estos modelos encapsulados.

---

# 38. Earth exclusion

La primera implementación podrá utilizar separación respecto al centro de la Tierra si así aparece definido en el baseline.

No obstante, la arquitectura deberá permitir en el futuro utilizar:

```text
earth_limb_exclusion
```

sin modificar el resto del detector pipeline.

Geometric Earth occultation seguirá siendo un criterio independiente.

---

# 39. Iluminación y eclipse

Implementar:

- solar illumination del debris;
- Earth eclipse;
- Earth occultation de la LOS.

La versión masiva puede utilizar inicialmente una Tierra esférica.

Los modelos vectorizados deberán validarse frente a Orekit.

---

# 40. Estado de detección

Cada evento deberá almacenar:

```python
is_detectable: bool
primary_failure_reason: str
failure_flags: list[str]
```

Posibles flags:

```text
outside_fov
eclipse
earth_occultation
sun_exclusion
earth_exclusion
moon_exclusion
snr
```

---

# 41. Convención visual global

En las gráficas de eventos:

```text
VERDE = detectable
GRIS CLARO = no detectable
```

Esta convención deberá mantenerse en:

- scatter plots;
- visualizador 3D;
- análisis de eventos.

---

# 42. Diagnostic mode

Añadir un modo diagnóstico opcional donde los puntos puedan colorearse por:

- SNR rejection;
- eclipse;
- Earth occultation;
- Sun exclusion;
- Earth exclusion;
- Moon exclusion;
- outside FOV.

---

# 43. Optical Validation

El objetivo será determinar qué objetos pueden detectarse utilizando:

- detector baseline;
- FOV variable;
- aperture variable.

El modelo deberá caracterizar simultáneamente:

- brightness;
- range;
- phase;
- angular velocity;
- streak;
- FOV;
- focal;
- aperture.

---

# 44. Inicio obligatorio de Optical Validation

Antes de ejecutar la Phase 2, Codex deberá:

1. Leer `TRACE_Detector_Optical_Baseline.xlsx`.
2. Mostrar los parámetros encontrados.
3. Validar las unidades.
4. Validar los rangos.
5. Construir `DetectorConfig`.
6. Construir `OpticalSystemConfig`.
7. Construir `DetectionConfig`.
8. Ejecutar consistency tests.
9. Sólo entonces ejecutar el modelo óptico.

Si el workbook no está disponible:

**no inventar parámetros.**

---

# 45. Variables de Optical Validation

## Instrumento

- FOV;
- aperture;
- focal length derivada;
- f-number derivado;
- integration time.

## Debris

- diameter;
- albedo;
- range;
- phase angle.

## Geometría

- relative velocity;
- angular rate;
- dwell time.

---

# 46. Outputs por evento

Calcular:

- apparent magnitude;
- photon count;
- electron count;
- SNR;
- streak length;
- focal length;
- f-number;
- plate scale;
- is_detectable;
- rejection reason.

---

# 47. Outputs agregados

Calcular:

- limiting magnitude;
- minimum detectable diameter;
- maximum detection range;
- fraction of geometric opportunities detectable;
- fraction detectable by size class;
- fraction rejected by each criterion.

---

# 48. Range vs apparent magnitude

Debe mantenerse como una gráfica principal.

Scatter de encuentros físicos.

Color:

```text
verde = detectable
gris = non-detectable
```

---

# 49. Range vs debris diameter

Scatter de encuentros.

Permite identificar la frontera tamaño–distancia.

Color:

```text
verde = detectable
gris = non-detectable
```

---

# 50. Range vs SNR

Mostrar:

- puntos de eventos;
- threshold de SNR.

Color por detectabilidad.

---

# 51. Angular rate vs apparent magnitude

Esta será una de las gráficas principales de TRACE.

Razón:

la magnitud representa dificultad fotométrica mientras que angular rate representa la penalización dinámica asociada al streaking.

Color:

```text
verde = detectable
gris = non-detectable
```

---

# 52. Angular rate vs SNR

Permite estudiar directamente la degradación del rendimiento debida al movimiento.

Color por detectabilidad.

---

# 53. Angular rate vs streak length

Mostrar relación entre:

- angular velocity;
- integration time;
- plate scale;
- streak length.

Separar por FOV cuando resulte útil.

---

# 54. FOV vs streak length

Mostrar curvas para diferentes angular rates.

Esta gráfica deberá explicar el trade:

```text
larger FOV
→ shorter focal length
→ larger angular pixel scale
→ shorter streak in pixels
```

---

# 55. FOV vs limiting magnitude

Generar una curva por apertura o configuración relevante.

Los FOV a estudiar deberán obtenerse del rango definido en el workbook.

---

# 56. FOV vs minimum detectable diameter

Generar para:

- diferentes ranges;
- o escenarios geométricos representativos.

---

# 57. Aperture vs limiting magnitude

Generar una curva por FOV.

---

# 58. Aperture vs minimum detectable diameter

Generar una curva por FOV o range.

---

# 59. Optical diagnostic plots

Generar también:

```text
FOV vs focal length
FOV vs f-number
FOV vs plate scale
```

Estas gráficas servirán para validar consistencia física.

---

# 60. Heatmaps

Generar:

```text
FOV × aperture → limiting magnitude
FOV × aperture → minimum detectable diameter
range × debris diameter → detectability
angular rate × apparent magnitude → detectability
```

Añadir cuando sea posible:

```text
FOV × aperture
→ fraction of MASTER opportunities detectable
```

Esta será una figura clave para conectar óptica y Mission Analysis.

---

# 61. Diseño de constelación

Una vez validado el modelo óptico, estudiar configuraciones orbitales.

Variables:

- total satellites;
- orbital planes;
- satellites per plane;
- altitude;
- inclination;
- RAAN;
- RAAN separation;
- in-plane phasing;
- inter-plane phasing;
- FOV;
- along-track boresight offset;
- cross-track boresight offset.

---

# 62. Configuraciones Walker-like

Se podrán generar arquitecturas regulares tipo Walker-like.

No limitar el software exclusivamente a esta familia.

---

# 63. Objetivo de Constellation Performance

Calcular:

- detection events/day;
- unique objects detected/day.

No contar cruces geométricos como detecciones.

Sólo los eventos que cumplan el pipeline completo de detección serán considerados detecciones válidas.

---

# 64. Métodos de exploración del espacio de diseño

Implementar:

1. Grid Search.
2. Latin Hypercube Sampling.
3. Sobol Sampling.

Utilizar seeds reproducibles.

No comenzar con un brute-force masivo.

---

# 65. KPIs de constelación

Para cada configuración calcular:

- total detection events/day;
- unique debris/day;
- fraction of population/day;
- detections by diameter bin;
- detections by altitude bin;
- detections by inclination bin;
- median range;
- median angular rate;
- median dwell time;
- rejection by SNR;
- rejection by eclipse;
- rejection by Earth occultation;
- rejection by Sun exclusion;
- rejection by Earth exclusion;
- rejection by Moon exclusion.

---

# 66. Análisis de sensibilidad

Evaluar influencia de:

- satellite count;
- plane count;
- altitude;
- inclination;
- RAAN separation;
- FOV;
- along-track angle;
- cross-track angle;
- aperture cuando corresponda.

El objetivo será identificar qué variables dominan el rendimiento.

---

# 67. Event table

Cada evento deberá almacenar:

```text
simulation_id
object_id
satellite_id
plane_id

event_start
event_end
event_duration
dwell_time

minimum_range
relative_velocity
angular_rate
phase_angle

apparent_magnitude
SNR
streak_length

debris_diameter
debris_mass
albedo_scenario

satellite_position
satellite_velocity

debris_position
debris_velocity

boresight_direction
FOV

aperture
focal_length
f_number
plate_scale

sun_exclusion_angle
earth_exclusion_angle
moon_exclusion_angle

illumination_valid
earth_occulted

is_detectable
primary_failure_reason
failure_flags

propagator_backend
model_version
parameter_set_version
```

---

# 68. Tipos de evento

Distinguir:

```text
geometric_crossing
geometrically_valid_opportunity
detectable_event
unique_detected_object
```

---

# 69. Readquisición

Para cada objeto detectado buscar:

- segundo observador;
- tercer observador;
- observación simultánea.

La ventana temporal baseline deberá ser configurable.

Inicialmente utilizar una ventana del orden de un día para los análisis TRACE.

---

# 70. KPIs de readquisición

Calcular:

- probability of second observation;
- probability of third observation;
- A→B latency;
- A→B→C latency;
- median latency;
- P90 latency;
- candidate observers;
- observer baseline;
- LOS angle;
- range at each observation.

Guardar distribuciones completas.

---

# 71. Observación simultánea

Definir como:

```text
overlap real de ventanas detectables
```

de dos o más satélites sobre el mismo objeto.

---

# 72. Métricas de observación simultánea

Calcular:

- overlap duration;
- observer separation;
- LOS intersection angle;
- parallax geometry;
- range from observer A;
- range from observer B;
- SNR A;
- SNR B;
- phase angle.

KPIs:

- probability simultaneous observation;
- simultaneous events/day.

---

# 73. Orbit Determination

Baseline:

```text
angles-only Batch Least Squares
```

No implementar EKF/UKF inicialmente.

La arquitectura deberá mantenerse desacoplada del backend dinámico.

---

# 74. Orekit y Orbit Determination

Evaluar Orekit como backend preferente para OD en fases posteriores, especialmente para:

- propagación;
- state transition matrices;
- Jacobians;
- estimation;
- high-fidelity dynamics.

No es obligatorio utilizar Orekit para el primer prototipo BLS si una implementación propia resulta más transparente para Mission Analysis.

---

# 75. Tracklets

Una observación no será una única dirección instantánea.

Cada ventana deberá poder producir múltiples medidas.

Cada medida incluirá:

- timestamp;
- observer position;
- observer velocity;
- RA/Dec o equivalente;
- measurement covariance.

Cadencia configurable.

---

# 76. Precisión astrométrica

Definir:

```text
measurement_sigma_arcsec
```

como parámetro configurable.

No fijar todavía un requisito definitivo.

Podrá derivarse posteriormente de:

- plate scale;
- PSF;
- SNR;
- centroiding;
- calibration;
- star tracker performance.

---

# 77. Casos OD

Comparar:

### A

```text
SAT-A
```

### B

```text
SAT-A → SAT-B
```

### C

```text
SAT-A → SAT-B → SAT-C
```

### D

```text
SAT-A + SAT-B simultaneous
```

Opcionalmente:

### E

```text
simultaneous A+B → later C
```

---

# 78. Métricas OD

Calcular:

- position covariance;
- velocity covariance;
- radial uncertainty;
- along-track uncertainty;
- cross-track uncertainty;
- 3D position uncertainty;
- covariance determinant;
- covariance volume proxy;
- covariance reduction factor;
- truth position error;
- truth velocity error;
- condition number.

---

# 79. Epoch común

Todas las comparaciones de soluciones OD deberán realizarse en un epoch común.

Opcionalmente propagar la incertidumbre a:

```text
+1 h
+6 h
+24 h
```

---

# 80. Observabilidad single-observer

Un short angles-only tracklet tiene baja observabilidad de:

- range;
- range rate.

El software no deberá ocultar:

- singularities;
- poor conditioning;
- prior dependence.

Si se utiliza weak prior deberá identificarse explícitamente.

---

# 81. Acoplamiento constelación–readquisición

La arquitectura que maximiza detections/day no tiene por qué maximizar:

- readquisition probability;
- multiobserver geometry;
- orbit quality.

Por tanto las fases de:

```text
Constellation Performance
Reacquisition
Orbit Determination
```

deberán iterar.

---

# 82. Optimización multiobjetivo

No utilizar inicialmente una función de mérito rígida.

Generar:

- comparative tables;
- sensitivity plots;
- Pareto fronts.

Objetivos potenciales:

- maximize unique debris/day;
- maximize detection events/day;
- maximize second-observation probability;
- maximize third-observation probability;
- maximize simultaneous probability;
- maximize covariance reduction;
- minimize satellite count.

---

# 83. Visualizador 3D

Crear visualizador independiente del motor.

Primera implementación:

```text
Plotly + Dash
```

Posibles migraciones futuras:

- PyVista;
- Three.js;
- deck.gl;
- WebGL alternatives.

---

# 84. Tierra

Mostrar:

- esfera terrestre;
- ejes opcionales;
- frame opcional.

No es necesario inicialmente utilizar texturas de alta resolución.

---

# 85. Debris

Representar como puntos.

Convención:

```text
gris claro = no detectable
verde = detectable
```

Marker size:

proporcional al diámetro mediante escala gráfica.

No utilizar escala física real.

---

# 86. Satélites

Representar mediante:

- pequeños cubos;
- color identificativo;
- orbit trajectories.

Permitir color por:

- satellite;
- orbital plane.

---

# 87. FOV

Representar:

- cono;
- frustum;
- volumen equivalente.

Debe respetar:

- FOV;
- LVLH;
- along-track offset;
- cross-track offset.

Debe evolucionar correctamente durante la órbita.

---

# 88. Animación

Incluir:

- time slider;
- play;
- pause;
- playback speed;
- satellite selection;
- debris selection;
- size filters;
- detection filters.

Cuando un debris pase a ser detectable:

```text
grey → green
```

Cuando deje de cumplir criterios:

```text
green → grey
```

---

# 89. Información interactiva

Para un debris seleccionado mostrar:

- object ID;
- mass;
- diameter;
- altitude;
- range;
- relative velocity;
- angular rate;
- apparent magnitude;
- SNR;
- detection status;
- observing satellite.

---

# 90. Rendimiento del visualizador

No será obligatorio representar toda la población MASTER simultáneamente.

Permitir:

- sampling;
- filtering;
- level-of-detail;
- display only objects near FOV;
- display only detected objects;
- configurable maximum markers.

La simulación física puede utilizar una población mucho mayor que el renderer.

---

# 91. Tecnologías recomendadas

Preferentemente:

- NumPy;
- SciPy;
- Pandas o Polars;
- PyArrow;
- Parquet;
- Orekit;
- Astropy cuando resulte útil;
- SciPy QMC;
- Matplotlib;
- Plotly;
- Dash;
- Pydantic;
- Numba si resulta necesario.

---

# 92. Estructura de configuración

```text
config/
    default_sensor.yaml
    default_optics.yaml
    default_constellation.yaml
    default_simulation.yaml
    orekit.yaml
```

Importante:

`default_sensor.yaml` y `default_optics.yaml` no constituyen la source of truth original.

Deben derivarse del Excel baseline y podrán posteriormente recibir overrides.

---

# 93. Metadata de cada run

Guardar:

- simulation ID;
- date/time;
- full config;
- random seed;
- propagator backend;
- software version;
- model version;
- parameter-set version;
- number of objects;
- satellite count;
- duration;
- timestep;
- runtime overrides.

---

# 94. Formato de resultados

Preferir Parquet.

Archivos:

```text
objects.parquet
satellites.parquet
states.parquet
propagator_validation.parquet
geometric_crossings.parquet
detections.parquet
reacquisitions.parquet
simultaneous_events.parquet
od_results.parquet
constellation_results.parquet
```

---

# 95. Arquitectura propuesta

```text
trace_sim/
│
├── config/
│   ├── load_optical_baseline.py
│   ├── default_sensor.yaml
│   ├── default_optics.yaml
│   ├── default_constellation.yaml
│   ├── default_simulation.yaml
│   └── orekit.yaml
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── orekit-data/
│
├── trace/
│   ├── constants.py
│   ├── units.py
│
│   ├── configuration/
│   │   ├── models.py
│   │   ├── excel_loader.py
│   │   └── validation.py
│
│   ├── population/
│   │   ├── loader.py
│   │   ├── sampling.py
│   │   └── orbital_elements.py
│
│   ├── dynamics/
│   │   ├── base.py
│   │   ├── fast_j2.py
│   │   ├── orekit_backend.py
│   │   ├── propagator_factory.py
│   │   └── validation.py
│
│   ├── time/
│   │   └── time_system.py
│
│   ├── ephemerides/
│   │   ├── sun.py
│   │   └── moon.py
│
│   ├── frames/
│   │   ├── lvlh.py
│   │   └── transformations.py
│
│   ├── optics/
│   │   ├── detector.py
│   │   ├── optical_system.py
│   │   ├── photometry.py
│   │   ├── lambert.py
│   │   ├── psf.py
│   │   ├── streak.py
│   │   └── snr.py
│
│   ├── geometry/
│   │   ├── fov.py
│   │   ├── los.py
│   │   ├── eclipse.py
│   │   ├── occultation.py
│   │   └── exclusion_angles.py
│
│   ├── detection/
│   │   ├── detector_model.py
│   │   ├── event_finder.py
│   │   └── event_table.py
│
│   ├── constellation/
│   │   ├── models.py
│   │   ├── generator.py
│   │   ├── walker.py
│   │   └── design_space.py
│
│   ├── montecarlo/
│   │   ├── grid.py
│   │   ├── lhs.py
│   │   ├── sobol.py
│   │   └── runner.py
│
│   ├── od/
│   │   ├── observations.py
│   │   ├── tracklets.py
│   │   ├── batch_least_squares.py
│   │   ├── orekit_od_backend.py
│   │   ├── covariance.py
│   │   └── metrics.py
│
│   ├── analysis/
│   │   ├── propagator_validation.py
│   │   ├── geometry_validation.py
│   │   ├── optical_validation.py
│   │   ├── constellation_validation.py
│   │   ├── reacquisition_validation.py
│   │   ├── sensitivity.py
│   │   ├── pareto.py
│   │   └── plots.py
│
│   ├── io/
│   │   ├── parquet.py
│   │   └── run_metadata.py
│
│   └── visualization/
│       ├── app.py
│       ├── earth.py
│       ├── debris.py
│       ├── satellites.py
│       ├── fov.py
│       └── animation.py
│
├── tests/
├── scripts/
├── notebooks/
└── README.md
```

---

# 96. Encapsulación de Orekit

No dispersar llamadas directas.

Centralizar en:

```text
orekit_backend.py
time_system.py
frame wrappers
ephemerides wrappers
```

Documentar:

- Orekit version;
- Java version;
- Python integration mechanism;
- orekit-data;
- frame conventions;
- time scales.

---

# 97. Tests del Excel loader

Implementar tests para verificar:

- workbook existe;
- hojas existen;
- todos los campos requeridos existen;
- unidades reconocidas;
- tipos válidos;
- ausencia de duplicados;
- valores numéricos físicamente razonables;
- variables derivadas no tratadas como inputs independientes.

---

# 98. Tests del propagador

Implementar:

- circular orbit;
- slightly eccentric orbit;
- J2 RAAN precession;
- conservation checks;
- FastJ2 vs Orekit.

Generar error vs time.

---

# 99. Tests LVLH

Comprobar:

- orthogonality;
- handedness;
- radial direction;
- along-track direction;
- orbit-normal direction.

Validar contra Orekit.

---

# 100. Tests de geometría

Crear casos sintéticos:

- center of FOV;
- FOV edge;
- outside FOV;
- Earth blocking LOS;
- unobstructed LOS;
- illuminated object;
- eclipsed object;
- exclusion pass/fail.

---

# 101. Tests ópticos

Comprobar:

- aperture ↑ → photon count ↑;
- range ↑ → flux ↓;
- diameter ↑ → flux ↑;
- albedo ↑ → flux ↑;
- unfavorable phase ↑ → brightness ↓;
- focal/FOV relation;
- plate scale;
- f-number;
- streak.

Los valores de los inputs deberán proceder del workbook o de overrides explícitos.

---

# 102. Tests SNR

Comprobar:

- read noise ↑ → SNR ↓;
- background ↑ → SNR ↓;
- angular rate ↑ puede reducir SNR;
- aperture ↑ → SNR ↑;
- configured threshold aplicado correctamente.

---

# 103. Tests OD

Casos sintéticos:

- measurement noise ↑ → covariance ↑;
- segundo observador útil → observability ↑;
- tercer observador útil → uncertainty ↓;
- single angles-only tracklet → poor range observability;
- simultaneous stereo → improved geometry cuando baseline suficiente.

---

# 104. Phase 0 — Propagator Architecture

Implementar:

- PropagatorBackend;
- OrekitPropagator;
- FastJ2Propagator;
- frame handling;
- time systems;
- propagator cross-validation.

No avanzar a simulación masiva hasta validar FastJ2.

---

# 105. Phase 1 — Geometry Core

Implementar:

- MASTER loader;
- Cartesian/orbital conversion;
- LVLH;
- FOV;
- Sun/Moon;
- eclipse;
- occultation;
- exclusion angles;
- event table.

Empezar con población pequeña.

---

# 106. Phase 2 — Optical Validation

Primero:

- cargar Excel;
- validar Excel;
- construir configs.

Después implementar:

- detector;
- optical system;
- Lambertian photometry;
- PSF;
- streak;
- background;
- SNR;
- detection logic;
- plots.

---

# 107. Phase 3 — Constellation Performance

Implementar:

- constellation generation;
- detection pipeline;
- grid;
- Latin Hypercube;
- Sobol;
- KPI analysis;
- sensitivity.

---

# 108. Phase 4 — Reacquisition

Implementar:

- second observer;
- third observer;
- simultaneous observation;
- latency;
- observer geometry.

---

# 109. Phase 5 — Orbit Determination

Implementar:

- synthetic measurements;
- tracklets;
- angles-only BLS;
- covariance;
- single observer;
- two sequential;
- three sequential;
- two simultaneous.

Evaluar Orekit OD framework.

---

# 110. Phase 6 — Visualizer

Implementar:

- Earth;
- satellites;
- debris;
- trajectories;
- FOV;
- animation;
- detection coloring.

---

# 111. Primera entrega esperada

La primera entrega de Codex deberá centrarse en:

1. Repository architecture.
2. Orekit setup.
3. PropagatorBackend.
4. FastJ2Propagator.
5. OrekitPropagator.
6. FastJ2 vs Orekit validation.
7. Population loader.
8. Frames.
9. LVLH.
10. Synthetic geometry case.
11. Unit tests.
12. Propagator error plots.

No implementar todavía todo el modelo óptico.

---

# 112. Segunda entrega esperada

Después de cerrar propagación:

1. Generar geometric opportunities.
2. Obtener distribuciones de:
   - range;
   - relative velocity;
   - angular rate;
   - dwell time;
   - phase angle.
3. Generar diagnostic plots.
4. Validar eventos.

---

# 113. Tercera entrega esperada

Antes de empezar:

1. Leer `TRACE_Detector_Optical_Baseline.xlsx`.
2. Mostrar parámetros.
3. Validarlos.
4. Construir configs.

Después implementar Optical Validation.

---

# 114. Plots obligatorios de Optical Validation

Generar como mínimo:

- range vs apparent magnitude;
- range vs debris diameter;
- range vs SNR;
- angular rate vs apparent magnitude;
- angular rate vs SNR;
- angular rate vs streak length;
- FOV vs streak length;
- FOV vs limiting magnitude;
- FOV vs minimum detectable diameter;
- aperture vs limiting magnitude;
- aperture vs minimum detectable diameter;
- FOV vs focal length;
- FOV vs f-number;
- FOV vs plate scale;
- heatmaps.

---

# 115. Colores de scatter plots

Para todos los scatter plots con detección física:

```text
green = detectable
light grey = non-detectable
```

Opcional:

```text
diagnostic mode = rejection reason
```

---

# 116. Source-of-truth requirement

Codex **NO debe reconstruir los parámetros del detector u óptica utilizando conversaciones previas o valores recordados**.

Debe consultar:

```text
TRACE_Detector_Optical_Baseline.xlsx
```

Si:

- el fichero no existe;
- una hoja no existe;
- una unidad es ambigua;
- falta un parámetro requerido;
- existe una inconsistencia;

deberá:

1. identificarla;
2. reportarla;
3. detener únicamente la parte afectada.

No inventar valores.

---

# 117. Filosofía del desarrollo

Priorizar:

- claridad física;
- trazabilidad;
- reproducibilidad;
- modularidad;
- validation;
- testability;
- performance suficiente.

No optimizar prematuramente.

---

# 118. Clasificación de modelos

Cada modelo deberá identificarse como:

```text
baseline
approximation
reference
high-fidelity
configurable assumption
future refinement
```

---

# 119. Criterio final

El simulador TRACE no pretende inicialmente ser una herramienta SST operacional de máxima fidelidad.

Debe ser una herramienta de **Mission Analysis rápida, modular, reproducible y físicamente defendible**, capaz de utilizar modelos simplificados para grandes poblaciones siempre que dichos modelos estén contrastados frente a referencias de mayor fidelidad.

La arquitectura deberá permitir responder cuantitativamente:

1. ¿Qué población puede detectar TRACE?
2. ¿Qué condiciones geométricas producen esas detecciones?
3. ¿Qué FOV y apertura son más adecuados?
4. ¿Qué tamaño mínimo puede detectarse en condiciones realistas?
5. ¿Qué arquitectura orbital maximiza observaciones útiles?
6. ¿Cuál es la probabilidad de readquisición?
7. ¿Cuál es la probabilidad de observación simultánea?
8. ¿Cuánto mejora el conocimiento orbital mediante observaciones cooperativas?
9. ¿Qué variables tienen mayor influencia sobre el rendimiento?
10. ¿Existe una arquitectura TRACE técnicamente viable y suficientemente atractiva para estudios posteriores de mayor fidelidad?