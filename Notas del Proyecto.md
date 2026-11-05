# Notas del Proyecto

## 2026-11-05 · Identidad y alcance acordado

**TRACE** significa *Tracking and Reacquisition Architecture for Cooperative
Estimation of Uncorrelated Space Objects*. El proyecto se desarrolla en Python,
sin IA, para estudiar viabilidad, análisis de misión y optimización con óptica y
radiometría. El paquete conserva por compatibilidad el import
`space_debris_detection`; su nombre de distribución pasa a `trace-mission`.

Primera entrega: exactamente 50.000 objetos sintéticos, LEO entre 200 y 2.000 km,
diámetro equivalente desde 1 cm, CSV y gráfica tamaño–altitud. Se acepta una
aproximación basada en las figuras ESA; no se afirma disponer de datos MASTER.
Los documentos adjuntos son referencias, no autorización para desarrollar de
una vez todo el simulador descrito en la especificación.

## Fuentes y extracción

- `docs/references/ESA_Space_Environment_Report_2026.pdf`, página 31/152,
  sección 2.4, figura 2.8: número acumulado frente al diámetro de objetos que
  cruzan LEO; figura 2.9: densidad espacial frente a altitud para >1 cm y >10 cm.
- La fecha de referencia ESA es 1 de febrero de 2026. Las cifras del texto
  (1,5 millones entre 1 y 10 cm; 68.450 >10 cm incluyendo unos 11.300 payloads
  activos) son globales: **no se usan como proporciones de la población LEO**.
- Se extrajeron los vértices vectoriales de las curvas del PDF, no estimaciones
  visuales de una imagen rasterizada. `data/reference/extraction.json` registra
  SHA-256 del PDF, índices de trazados y calibraciones con las líneas de rejilla.
  Los CSV de referencia conservan las curvas calibradas para reproducir el estudio
  sin depender del lector PDF. Las coordenadas están redondeadas y la figura
  representa un modelo: no tienen precisión equivalente a datos fuente MASTER.
- En figura 2.9 se escogen las curvas discontinuas **Non-manoeuvrable** para
  reducir la contribución de satélites operativos maniobrables. No maniobrable
  no equivale exactamente a basura: puede incluir satélites activos no
  maniobrables. No podemos clasificarlos individualmente con estos datos.
- La figura 2.8 incluye todos los objetos. Se asume que su forma dentro de cada
  intervalo de tamaños aproxima también la de los no maniobrables. Esta
  mezcla de fuentes es una limitación explícita, pendiente de datos detallados.

## Hipótesis de población y órbitas

1. Tamaño = diámetro equivalente, en metros en el CSV y centímetros en la figura.
   La escala Y es logarítmica para mostrar todo el intervalo.
2. Altitud = altura de una **órbita circular equivalente** sobre una Tierra
   esférica de radio 6.371 km. Se asignan semieje mayor y excentricidad cero.
   Los perfiles ESA describen ocupación espacial, no una distribución de
   semiejes; convertirlos en órbitas circulares es una simplificación importante.
3. No se asignan inclinación, RAAN, argumento de periapsis, anomalía ni estados
   cartesianos. No se conocen sus distribuciones conjuntas a partir de estas dos
   figuras. La población sirve para el estudio tamaño–altitud, todavía no para
   propagación, encuentros, cobertura o readquisición. Tampoco se inventa masa.
4. Epoch convencional: `2026-02-01T00:00:00Z`. ESA da la fecha, no la hora;
   medianoche UTC es una convención, sin fase orbital asociada. No se asigna un
   marco inercial al no contener estados vectoriales.
5. Se interpola log10(densidad) linealmente con la altitud. Para los pocos km
   entre los extremos extraídos y 200/2.000 km se mantiene el valor extremo
   constante. Esto evita inventar estructura fuera de la curva disponible.
6. Las clases excluyentes son 1–10 cm y >10 cm. La densidad de la primera es
   `rho(>1 cm) - rho(>10 cm)`; se rechazan densidades negativas.
7. La probabilidad de altitud no es proporcional directamente a la densidad:
   se integra `rho(h) * 4*pi*(R+h)^2 dh`, sobre una malla de 0,25 km, mediante
   trapecios. Esa integral fija la proporción de las dos clases. Sus números
   absolutos son estimaciones aproximadas del perfil, no conteos oficiales.
8. Dentro de cada clase, tamaño y altitud se consideran independientes. Sí se
   conserva la diferencia entre perfiles de altitud de ambas clases; no se
   puede reconstruir una correlación continua completa con dos umbrales.
9. La curva acumulativa de tamaños se interpola en log(diámetro)–log(N) para
   obtener los extremos de cada clase. Se consolidan diámetros repetidos usando
   el menor N y se aplica una envolvente no creciente. Su inversión usa CDF
   lineal entre vértices en log(diámetro), eliminando mesetas. No se ajusta una
   ley de potencias global ni se supone distribución uniforme en tamaño.
10. No se impone un tamaño máximo de ingeniería arbitrario: se trunca en el mayor
    diámetro representado por la figura 2.8. Se descarta la cola más allá de ese
    punto y se renormaliza. El corte exacto queda en el JSON generado.
11. Muestreo aleatorio con reemplazo, semilla 20260201, 50.000 registros; no se
    fuerza un número fijo por clase. Se proporciona un peso estadístico común
    igual a la integral de población representada / 50.000. La muestra no es
    una predicción de objetos detectables ni una lista de objetos reales.
12. Cada punto dibujado corresponde a una fila; no se aplica submuestreo al
    renderizado. Transparencia y tamaño pequeño reducen la superposición.

## Radiometría: referencia y diferencias pendientes

Referencia: `Space debris mission scientific paper.pdf`, sección 2.1, páginas
2–3 del PDF, ecuaciones (1)–(10). El paper usa una placa cuadrada de lado r,
reflexión difusa isotrópica y una aproximación monocromática:

```text
S = Q * Pc * tau / (h * nu)
Pc = 0.4 * rho * H * r² * D² / (8 * d²)
N² = S + K*n_pix*tau + I_dark*n_pix*tau + RN²*n_pix
SNR = S / sqrt(N²)
```

Incluye ruido de Poisson de señal y fondo, corriente oscura y lectura. Su
estimación de píxeles iluminados depende de streaking, velocidad transversal,
distancia, focal y geometría. No debe extrapolarse sin comprobar unidades,
régimen de validez ni imponer una PSF finita cuando la velocidad tiende a cero.
La reproducción de sus resultados numéricos es una validación pendiente.

El workbook `TRACE_Detector_Optical_Baseline (1).xlsx` propone una esfera
lambertiana, banda 450–750 nm, PSF gaussiana y parámetros diferentes de los del
paper. Usaremos sus valores leyendo el archivo al implementar Optical
Validation, con unidades validadas y sin copiar esos números como defaults.
No se identifica automáticamente lado de placa con diámetro equivalente, ni
reflectancia del paper con albedo geométrico de una esfera. La convención de
albedo, la normalización espectral del fondo en magnitudes y la ley de fase
requieren definición y trazabilidad antes de obtener límites de detección.

Los modelos iniciales `optics.py` y `radiometry.py` y el ejemplo previo son
ilustrativos; todavía no implementan esta validación TRACE ni todo el modelo
del paper. La población generada no usa SNR para seleccionar objetos.

## Validación y límites

Las pruebas verifican 50.000 registros, finitud, límites de tamaño/altitud,
coherencia circular y reproducibilidad. Comparan además proporciones de clase
y CDF de altitud con el modelo de muestreo. Son comprobaciones de implementación,
no validación externa del modelo ESA ni de las hipótesis orbitales.
Los hashes de las curvas y los parámetros de ejecución se guardan junto al CSV.
La publicación del entorno y la subida a GitHub son operaciones separadas.

## Resultado de la primera ejecución

- 47.400 objetos entre 1 y 10 cm y 2.600 mayores de 10 cm.
- Probabilidad modelada de la clase >10 cm: 5,2154 %; realización: 5,2 %.
- Corte superior de la curva de tamaño: aproximadamente 38,29 m (no es el
  tamaño máximo necesariamente presente en la muestra).
- Ocho pruebas superadas, incluidas CDF de tamaño y altitud.
- Versiones de ejecución verificadas conservadas en `requirements.lock.txt`.
- El extractor opcional `scripts/extract_esa_curves.py` usa PyMuPDF y comprueba
  el hash del PDF antes de regenerar los CSV. No se necesita PyMuPDF para
  generar la población desde los CSV ya incluidos.

## Distribución de inclinación disponible: revisión de figura 3.3

El informe sí contiene información utilizable: figura 3.3, página 68/152,
distribución de número de objetos frente a inclinación (bins de 3°) y altitud
de perigeo (bins de 40 km), con paneles de objetos residentes y que cruzan LEO.
La revisión inicial de población se limitó a las figuras 2.8–2.9; no se ha
incorporado todavía esta información a los registros generados.

Para una futura aproximación circular, el panel de residentes es la referencia
más coherente. Se propone extraer P(inclinación | banda de perigeo), conservando
la distribución de altitud ya obtenida. No debe confundirse perigeo con altitud
media salvo bajo la hipótesis circular. Esta figura del estado del entorno a
finales de 2025 no separa por sí sola el debris >=1 cm no maniobrable: incluye
objetos de otras clases y no da la inclinación de la población pequeña no
catalogada MASTER. Extenderla a todos nuestros tamaños sería una hipótesis de
transferencia con sesgo posible por payloads activos y selección de catálogo,
no un resultado directamente publicado por ESA. La escala de conteos es
logarítmica: al extraerla hay que invertir los colores a conteos antes de
normalizar; las celdas sin objetos no se tratarán como un objeto.

Esta propuesta sigue pendiente de implementación y validación. No se han
cambiado inclinaciones, RAAN, excentricidad ni argumento del perigeo.
