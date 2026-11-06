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

## Actualización: inclinación ESA y flujo empírico orbital

Esta sección **sustituye el estado de implementación anterior**. Se mantiene el
historial para distinguir hipótesis originales de decisiones posteriores.

### Estado y procedencia

La extracción y asignación de inclinación de figura 3.3a ya están implementadas.
El acceso HTTPS a CelesTrak y a DISCOS devolvió `Tunnel connection failed: 403
Forbidden` desde el proxy del entorno. No se ha obtenido un catálogo real:
**RAAN, e y argumento del perigeo siguen sin asignarse** en el CSV actual.
Se guardó en el borrador de red la incorporación de `celestrak.org`; guardar un
borrador no aplica ese cambio a la máquina. El usuario debe revisar y guardar
los ajustes; el producto puede requerir después publicar el entorno.

Se intentaron operaciones de lectura en:

- `https://celestrak.org/NORAD/elements/gp.php?GROUP=all&FORMAT=json`
- `https://celestrak.org/NORAD/elements/gp.php?GROUP=cosmos-2251-debris&FORMAT=json`
- `https://celestrak.org/pub/satcat.csv`
- `https://discosweb.esoc.esa.int`

El bloqueo del proxy se produjo antes de obtener respuesta del servicio. Por
tanto, ni la validez de la consulta `GROUP=all` ni su cobertura están verificadas.
No se han solicitado credenciales: el primer bloqueo es de acceso de red.
Las familias individuales de fragmentación no se aceptan como sustituto de un
catálogo representativo de todos los objetos DEB/R/B.

### Extracción de inclinación

1. Se usa el panel de residentes en LEO, página 68, figura 3.3a, estado a finales
   de 2025. Se extraen 574 celdas vectoriales no vacías del PDF original, cuyo
   SHA-256 se comprueba antes de extraer.
2. Sus límites reconstruyen intervalos de 40 km de perigeo y 3° de inclinación.
   Cada celda tiene un color de la paleta `inferno_r` de 256 entradas. El color
   se invierte a una coordenada normalizada de la paleta y luego a un conteo
   aproximado usando la escala logarítmica de la barra. La calibración se apoya
   en las marcas de décadas, no en suponer que el máximo corresponde a 10³.
3. La cuantización de la paleta impide recuperar conteos enteros exactos; se
   conservan pesos fraccionales aproximados. El residuo RGB máximo es menor
   de 4e-8. Esto verifica la identificación del color, no la precisión física
   de los conteos ni la representatividad estadística de la figura.
4. Las celdas no dibujadas tienen peso cero. No se confunde blanco con conteo 1.
   En cada banda de altura se normalizan los pesos para construir
   `P(intervalo de inclinación | intervalo de perigeo)`.
5. Se conserva la muestra de tamaños y altitudes de la entrega original. Para
   cada objeto, se elige un intervalo de inclinación con esas probabilidades y
   una inclinación uniforme **dentro del intervalo de 3°**, no uniforme en
   [0°,180°]. Semilla orbital independiente: 20260202.
6. Si una banda de perigeo está vacía se permite usar la banda no vacía más
   cercana; se registra el número de objetos afectados. En esta ejecución no
   se necesitó este fallback.
7. La figura usa perigeo y la población de partida usa `a-R`, definido como
   promedio de las altitudes de los ápsides, no altitud instantánea ni promedio
   temporal. Mientras falte e se usa h como proxy circular del perigeo. El CSV
   actual **no conserva los ceros de e como si fueran estimaciones empíricas**:
   omite esos parámetros. Se conserva a como descriptor de altitud.
8. La marginal de inclinación resultante no tiene por qué reproducir la marginal
   original del informe: se conserva su distribución condicional pero se
   repondera cada banda con la población de tamaños/altitudes de figura 2.9.
9. Figura 3.3 incluye objetos de diferentes tipos, incluidos payloads. Aplicar
   su inclinación al debris >=1 cm es una hipótesis de transferencia; no se
   puede sustraer la contribución de satélites activos a partir de este panel.
   Tampoco se conoce su dependencia con el tamaño dentro de cada banda.

### Procedimiento empírico preparado, aún no ejecutado con datos reales

1. Adquirir un snapshot de elementos GP y un SATCAT de clasificación de fuente
   pública identificada, conservando originales, URL, fecha de descarga y
   hashes. Se acepta CSV; `prepare_empirical_catalogue.py` no descarga datos ni
   infiere el tipo de objeto a partir de fragmentos del nombre.
2. Cruzar por NORAD_CAT_ID, rechazar IDs duplicados en GP y seleccionar tipos
   SATCAT `DEB` y `R/B`, no reentrados y geocéntricos. Se excluyen los payloads,
   también los inactivos: esta decisión reduce contaminación de satélites
   operativos pero elimina parte de los objetos no maniobrables reales.
3. Rechazar elementos no finitos, e fuera de [0,1), ángulos fuera de sus dominios
   y movimientos medios no positivos. Estimar a mediante la relación
   kepleriana con mu=398600,4418 km³/s², n en rad/s y radio terrestre 6.371 km.
   Es una aproximación con elementos medios GP; no sustituye la conversión
   SGP4 a estados osculadores, importante especialmente en los bordes de LEO.
4. Filtrar perigeo >=200 km y apogeo <=2.000 km. Así se definen residentes en
   el intervalo pedido, excluyendo órbitas que solo lo atraviesan. Se registran
   filtros, conteos, límites temporales y hashes en un JSON adjunto.
5. Para cada objeto sintético conservar a (y, por tanto, su distribución de
   altitud media). Seleccionar donantes con altitud media a +/-100 km y
   excentricidad compatible con **ambos ápsides** dentro de 200–2.000 km.
   La condición es `e <= min(h-200, 2000-h)/(R+h)`. No se recorta e después de
   muestrearla: se filtran donantes para evitar crear una distribución truncada
   con acumulaciones artificiales en los límites.
6. Si no hay donantes locales se usan hasta 50 donantes físicamente compatibles
   más cercanos en altitud. Se registra su uso y la mayor separación. Si no
   existe ninguno compatible, el proceso falla en vez de inventar una órbita.
7. Remuestrear con reemplazo la **tupla conjunta** `(e, Omega, omega)` de un
   mismo donante. No ajustar normales a ángulos ni promediar 359° y 1° como
   si fueran 180°. No se añade jitter a los elementos empíricos; se preservan
   ID y epoch del donante para trazabilidad.
8. Recalcular perigeo y apogeo del objeto sintético usando su a y la e muestreada.
   Entonces muestrear inclinación de ESA condicionada en el perigeo derivado.
   El tamaño no interviene en el remuestreo orbital: extender el catálogo de
   objetos grandes al régimen 1–10 cm sigue siendo una hipótesis.
9. Este factoriza el modelo como población base de (h,d), tuplas empíricas
   `(e,Omega,omega)|h` sujetas a los límites de LEO, e inclinación ESA `i|hp`.
   No conserva toda la dependencia de i con e/Omega/omega ni reproduce
   necesariamente las marginales del catálogo tras los filtros. Es una
   aproximación híbrida explícita, no una reconstrucción de la distribución
   orbital conjunta real. Se deben evaluar las bandas sin soporte y el efecto
   de selección, no afirmar de antemano que cualquier catálogo mejora todo.
10. Los ángulos GP se refieren a la convención orbital del producto GP/TLE
    (asociada a TEME), no se reinterpretan como elementos ICRF. Se conservan
    las epochs originales; **no se han propagado a una época común**. El RAAN
    y omega evolucionan por precesión, por lo que mezclar snapshots históricos
    amplios o etiquetarlos con febrero de 2026 produciría una distribución
    temporalmente inconsistente. Antes de una validación de misión se debe
    definir epoch, restringir antigüedad y propagar con SGP4 si procede.
11. Para e muy pequeña, omega está mal condicionado y su histograma puede
    reflejar convenciones del elemento orbital. Para simulación se deberá
    analizar también argumento de latitud o elementos no singulares. No se
    inventa una interpretación física de omega para órbitas exactamente
    circulares. Tampoco se asigna anomalía media o fase orbital todavía.
12. No hay datos reales adquiridos con los que validar este procedimiento.
    Las pruebas del preparador y del remuestreador usan **fixtures artificiales
    exclusivamente**, que no se incluyen como catálogo de producción.

### Gráficas y preferencia persistente del usuario

Desde esta entrega se usa un módulo común de estilo científico: texto serif
STIX, matemáticas Computer Modern, unidades SI o unidades indicadas en el eje,
ejes limpios con marcas internas y salidas PDF vectorial y PNG a 300 dpi.
Se usa MathText para el aspecto LaTeX. Se comprobó el motor LaTeX disponible,
pero falla por falta de `cm-super`; el renderizado MathText funciona sin ese
paquete y no requiere modificar la máquina para producir figuras vectoriales.

Los mapas tamaño–altitud e inclinación–altitud son histogramas 2D, no puntos
individuales: color = número de objetos sintéticos por celda, paleta inferno_r,
normalización logarítmica y celdas vacías blancas. Altitud: bins de 40 km;
inclinación: 3°; tamaño: 60 bins logarítmicos desde 1 cm hasta cubrir la muestra.
Los pesos estadísticos no se aplican a los colores: representan los 50.000
registros, no el número estimado de objetos reales. El histograma de altitud
apila las clases 1–10 cm y >=10 cm, sin normalizar a densidad.

También se generan mapa e histograma de semieje mayor. Su correlación diagonal
con altitud es una identidad a=R+h, no un hallazgo físico. Cuando haya catálogo,
se generarán mapas/histogramas de e, RAAN y omega (ángulos en bins de 6°;
e en 60 bins lineales). Mientras falten, no se dibujan falsos histogramas de
datos empíricos. `figure_manifest.json` lista las variables pendientes y
verifica que cada mapa y el histograma de altitud cuentan todos los objetos.

La extracción de inclinación se guarda en CSV/JSON y es reproducible desde el
PDF mediante `scripts/extract_esa_inclination.py`. Las comprobaciones incluyen
soporte de celdas vacías, distribución condicional de i, semillas, límites de
ápsides, conservación de tuplas de donantes y contabilización en figuras.

## Revisión de los archivos CelesTrak aportados el 2026-11-05

Se conservan los originales en `data/raw/celestrak/` con hashes SHA-256 y
procedencia declarada en `provenance.json`. El usuario los obtuvo de CelesTrak;
no se dispone de URL exacta ni hora de descarga. Se ha comprobado el contenido,
sin actualizar todavía los elementos de la población sintética.

- GP: 16.875 filas e IDs únicos, delimitador coma; epochs entre
  `2026-10-09T07:05:09.269952` y `2026-11-05T12:48:42.753024`.
- SATCAT: 71.262 filas, delimitador **punto y coma**. Tipos: 28.274 PAY,
  35.947 DEB, 6.923 R/B y 118 UNK. El lector de catálogo preparado previamente
  supone coma: deberá adaptarse o normalizar una copia, conservando el original.
- Los 16.875 GP cruzan con SATCAT: **16.871 PAY, cuatro R/B, cero DEB**.
  Los cuatro R/B figuran con estado operativo `+`; solo tres tienen perigeo
  >=200 km y apogeo <=2.000 km. No constituyen donantes representativos de
  basura espacial; no se deben usar esos tres para ajustar RAAN/omega del debris.
- SATCAT contiene 14.977 DEB/R/B no reentrados. Con ápsides numéricos finitos,
  apogeo >= perigeo, perigeo >=200 km y apogeo <=2.000 km, quedan **10.844**
  (9.846 DEB y 998 R/B). Otros 3.766 están fuera del intervalo de residentes
  y 367 carecen de ápsides válidos. Estas cifras no equivalen a una validación
  de vigencia de todos los objetos ni a cobertura de la población de 1 cm.

SATCAT incluye PERIGEE/APOGEE, INCLINATION y PERIOD: permite estimar una
distribución empírica de e a partir de los ápsides, usando
`e=(ha-hp)/(2*6371+ha+hp)`. Las altitudes están redondeadas; pequeñas e pueden
quedar cuantizadas o aparecer como cero. SATCAT no aporta EPOCH orbital,
RAAN ni argumento del perigeo: no permite reconstruir esas dos distribuciones
ni sincronizar los elementos a una época común. La ausencia de fecha de
reentrada no garantiza por sí sola una órbita vigente.

El GP sí proporciona e, RAAN, omega y anomalía media, pero para una población
dominada por satélites activos. Transferir sus planos y orientaciones a basura
introduciría los patrones de operación de constelaciones, no una distribución
empírica de debris. **No se adopta esa transferencia como hipótesis**.

Para completar el procedimiento conjunto preparado se requiere un GP/OMM o TLE
que cubra objetos DEB y R/B de distintas familias, con NORAD_CAT_ID y epoch,
cruzado con este SATCAT. Las fechas GP recibidas son de octubre/noviembre de
2026, no de febrero de 2026: se deberá definir una referencia temporal coherente
o documentar y estudiar explícitamente ese desfase con el baseline ESA.

## Entrega de población orbital completa con los cinco CSV del usuario

Esta sección sustituye los estados anteriores de parámetros pendientes y de
epochs mezcladas. La población entregada tiene **50.000 registros con seis
elementos orbitales y estado cartesiano**, a una época orbital común. No se
afirma que las tres familias reconstruyan todo el entorno de basura real.

### Originales y selección

Se conservan, sin alterar sus bytes, los cinco CSV en `data/raw/celestrak/`:

| Archivo | Registros originales | Uso |
|---|---:|---|
| Chinese ASAT Test Debris_FENGYUN 1C.csv | 1.976 | Candidatos a donantes |
| IRIDIUM 33 Debris.csv | 109 | Candidatos a donantes |
| COSMOS 2251 Debris.csv | 584 | Candidatos a donantes |
| active_satellites_GP.csv | 16.875 | Archivo de referencia, excluido del muestreo |
| satcat.csv | 71.262 | Clasificación por NORAD_CAT_ID |

`provenance.json` contiene tamaño, delimitador, número de filas, rango de epochs
cuando existe y SHA-256 de cada original. No se inventan URL ni hora de descarga
que el usuario no haya proporcionado. `.gitattributes` evita normalizar los
saltos de línea de estos originales al guardarlos o recuperarlos con Git.

Los tres grupos reúnen 2.669 objetos únicos: 2.666 DEB y tres PAY. Se cruzan con
SATCAT, se excluyen PAY y UNK, objetos operativos (+, P, B, S, X), reentrados y
no geocéntricos. SATCAT se lee con su delimitador real, punto y coma; los GP
usan coma. El GP de satélites activos se archiva pero no se utiliza para
rellenar huecos ni para aumentar artificialmente la muestra de basura.

### Época, propagación y definición de elementos

1. Época orbital de la entrega: **2026-11-05T00:00:00Z**. Se elige un instante
   UTC fijo cercano a los snapshots recibidos, no la hora de ejecución.
2. Para limitar extrapolación temporal de TLE/GP se exige un desfase absoluto
   máximo de **7 días** respecto a esa época. Es un filtro de antigüedad de
   ingeniería, no garantía de precisión orbital; no se dispone de covarianzas.
3. Los GP se inicializan con `sgp4.omm` y se propagan con **sgp4 2.27**, modelo
   gravitacional WGS72 por defecto, hasta la época común. Se comprueban los
   códigos de error. Las epochs originales sin sufijo se interpretan como UTC,
   según el formato de GP; se conservan en el catálogo de referencia.
4. La salida SGP4 es posición/velocidad **TEME**, en km y km/s. Se convierten a
   elementos keplerianos instantáneos con mu=398600,4418 km³/s². Ese mu de
   conversión no es el mu interno WGS72 del propagador; está explícito en los
   metadatos. Los elementos resultantes describen el estado instantáneo bajo
   esa convención, no son los elementos medios originales GP.
5. Se rechazan estados inválidos/no elípticos y órbitas cuyos ápsides
   instantáneos quedan fuera de 200–2.000 km sobre la esfera R=6.371 km. Este
   criterio no equivale a asegurar residencia perpetua bajo perturbaciones ni
   a imponer altitud sobre un elipsoide o terreno real.
6. Resultado: **2.567 donantes** (1.890 FENGYUN, 570 COSMOS, 107 IRIDIUM).
   Rechazos: tres no DEB/RB, 90 por antigüedad y nueve por límites orbitales.
   La prioridad de filtros determina estas categorías excluyentes. En esta
   ejecución no hubo IDs duplicados ni errores SGP4 para candidatos admitidos.
7. Los GP aceptados tienen epochs originales entre 29 de octubre y 4 de
   noviembre de 2026. Se guardan los originales, el catálogo sincronizado,
   parámetros de propagación, hashes y conteos por familia en
   `data/reference/empirical_leo_debris.csv` y su JSON.

### Asignación a la población sintética

1. Se mantienen semilla 20260201, tamaños y muestreo ESA de altitud. Se siguen
   utilizando las distribuciones poblacionales de febrero de 2026 y la
   inclinación a finales de 2025. No se propaga el entorno estadístico ESA hasta
   noviembre: mezclar esas referencias con las orientaciones orbitales de
   noviembre es una hipótesis híbrida explícita, no una instantánea histórica
   real del entorno ni una evolución poblacional calculada.
2. Se remuestrea con reemplazo la tupla **(e, RAAN, omega)** de un mismo donante
   sincronizado. Se prioriza altitud media a +/-100 km, filtrando e para que,
   aplicada al a sintético, deje ambos ápsides dentro de los límites.
   Esta selección conserva correlaciones de la tupla entre sí, pero no toda
   su correlación con a ni la dependencia con inclinación o tamaño.
3. Sin donantes locales se toman hasta los 50 compatibles más cercanos. En la
   muestra entregada ocurre en **10.498 objetos, 20,996 %**. La máxima separación
   entre donantes candidatos de fallback y objeto ronda **1.577 km**. La falta
   de cobertura de estas familias a altas altitudes y sus e condicionan la
   selección: esa región **es extrapolación**, no una medición empírica local.
   Cada objeto guarda ID, familia, epoch original, altitud del donante,
   separación y bandera `donor_local_support`. Los metadatos también incluyen
   el máximo de la separación del donante efectivamente seleccionado.
4. Para **siete objetos** no había ninguna e de donante compatible con la
   altitud muestreada, por estar demasiado cerca de un borde. En vez de
   recortar e o inventar e=0, se desplaza h la mínima distancia al intervalo
   compatible con el donante menos excéntrico, con margen numérico de 1e-7 km.
   La mayor corrección es **0,98613 km**. Se guardan `esa_sampled_altitude_km`
   y `altitude_adjustment_km`; tamaños y número de objetos no cambian.
   Esta corrección reemplaza explícitamente la política inicial de abortar
   ante cualquier objeto sin soporte. No implica que esa e sea real en el borde.
5. Se calculan hp y ha usando la a sintética y la e remuestreada. Se muestrea
   inclinación de la figura ESA condicionada al **perigeo resultante**, no a
   la altitud media. No se requirió préstamo de bandas ESA vacías.
6. La asignación independiente de inclinación ESA puede romper la correlación
   de planos orbitales que tienen las familias originales con RAAN y omega.
   Se acepta como aproximación inicial solicitada; no se debe presentar como
   un conjunto de fragmentos reales coherentes de esas familias.
7. Distribución final de procedencia: 40.989 registros usan FENGYUN, 7.965
   COSMOS y 1.046 IRIDIUM. Las frecuencias resultan del soporte del catálogo y
   los filtros, **no son abundancias reales de esas familias en todo LEO**.
8. La fase se completa con **anomalía media uniforme en [0°,360°)**, semilla
   20260203, independiente del resto. Es una hipótesis sintética de mezcla en
   fase, no la anomalía empírica del donante. Se usa M uniforme, no anomalía
   verdadera uniforme, para representar tiempo uniforme a lo largo de la elipse.
9. Se resuelve Kepler y se calculan posiciones (x,y,z) en km y velocidades en
   km/s mediante conversión de los seis elementos en TEME a la época común.
   Es una conversión inicial kepleriana, **no se ha propagado aún cada objeto
   sintético con SGP4** ni se han definido BSTAR/área-masa para él. La etiqueta
   TEME no significa ICRF/J2000; las futuras transformaciones deben ser explícitas.
10. Se mantienen 47.400 tamaños de 1–10 cm y 2.600 >=10 cm. Transferir las
    propiedades orbitales catalogadas a 1–10 cm es una aproximación no validada.
    Tampoco se asigna masa sin una hipótesis de densidad, forma y área/masa.
11. Las curvas ESA de densidad son de ocupación espacial. Usarlas como una
    distribución de a-R y añadir e no reproduce exactamente esa ocupación
    radial: la fase desplaza cada objeto respecto a a-R. Se distinguen altitud
    media convencional a-R, perigeo, apogeo y altitud de la posición instantánea.
    Una reconstrucción de densidad radial más fiel requeriría otro ajuste inverso.

### Figuras, reproducibilidad y alcance de la validación

Se regeneran mapas e histogramas de a, e, i, RAAN, omega y M, además de
tamaño–altitud–conteo e histograma de altitud, con el estilo de publicación
acordado. Los mapas orbitales usan hp en X; el de tamaño y el histograma de
altitud usan a-R. Los bordes o envolventes en los mapas de e se deben en parte
a las restricciones de ápsides, no prueban una estructura física del debris.
Las celdas coloreadas cuentan registros sintéticos, sin aplicar su peso de
representación. Todos los mapas contabilizan los 50.000 registros.

`bash scripts/reproduce_population.sh` rehace la selección y sincronización de
donantes, población, figuras y auditoría desde los CSV originales, sin red.
El generador usa automáticamente el catálogo incluido cuando existe; el modo
parcial solo se solicita explícitamente con `--inclination-only`.

Las pruebas comprueban filtros, delimitadores, epochs, conversiones elementales,
conservación de tuplas, límites y conteos. La auditoría sobre los 50.000 registros
verifica hashes, elementos finitos, estado/energía, ápsides, época y marco comunes
y conversiones inversas de 100 objetos. Esto acredita consistencia computacional
y trazabilidad; **no valida representatividad global, precisión de observación,
covarianzas ni viabilidad de detección de TRACE**.

## Sensibilidad orbital: nueve alternativas y nominal preservada

**Nota de vigencia:** los modelos angulares iniciales de esta sección fueron
sustituidos por petición del usuario. La especificación vigente de RAAN/omega
es la corrección de 12/8/4 grupos equiespaciados al final del documento.

El usuario solicita tres poblaciones distintas por cada una de las variables
e, RAAN y omega, conservando la población actual como nominal. Se interpreta
como **nueve alternativas de 50.000 objetos más una nominal**, no una rejilla
de 27 combinaciones. No se ha renombrado, reescrito o reemplazado el CSV nominal,
sus metadatos ni su auditoría. Los hashes de esos tres archivos se verifican al
final y quedan registrados en `data/generated/sensitivity/manifest.json`.

### Variables controladas y fases emparejadas

En cada alternativa se modifica solo una de las tres variables independientes.
Se mantienen exactamente ID y orden de objetos, diámetros, altitud convencional
a-R, semieje mayor, inclinación, anomalía media nominal, epoch, marco y peso
estadístico. Los demás campos de e/RAAN/omega también se mantienen cuando no
son la variable del escenario. Se recalculan hp, ha y los seis componentes
cartesianos. Cambiar e modifica inevitablemente la altitud instantánea y los
ápsides; mantener a-R no equivale a mantener esos valores derivados.

**No se remuestrea la inclinación de ESA con el nuevo perigeo**: mantener i fija
rompe deliberadamente su condicionamiento original para aislar el efecto de e.
No se reinterpretan las alternativas como nuevas poblaciones derivadas de ESA.
Los campos heredados `donor_*` se conservan como trazabilidad del nominal, no
como evidencia empírica de los parámetros modificados; `donor_role` lo señala
en cada registro. Todos los escenarios son hipótesis de sensibilidad.

Se conserva la anomalía **media** M nominal, que fue uniforme en [0°,360°).
La anomalía verdadera no era uniforme en las órbitas excéntricas: no se cambia
esa convención. Emparejar M e IDs reduce variación de fase entre escenarios;
no impone igual posición instantánea si cambia e u omega. En el futuro deberá
mantenerse también la misma configuración de misión, duración y semillas del
detector para interpretar las diferencias como sensibilidad a la población.

### Tres alternativas de excentricidad

Para cada semieje a fijo se calcula
`e_max = min((a-R)-200, 2000-(a-R))/a`, con R=6.371 km. Este límite garantiza
hp>=200 km y ha<=2.000 km. Los valores nominales ya satisfacen ese límite.
No se desplaza ningún semieje ni se vuelven a aplicar los ajustes de borde de
la construcción nominal; esos ajustes previos permanecen como controles.

| Escenario | Definición |
|---|---|
| eccentricity_circular | e=0 para todos los objetos |
| eccentricity_low | e=0,5·e_nominal |
| eccentricity_high | q=e_nominal/e_max; e=e_max·2q/(1+q) |

La transformación alta aumenta e para 0<q<1, se aproxima a un factor dos lejos
del límite y se satura suavemente al acercarse al soporte permitido. No es un
recorte duro `min(2e,e_max)`: evita acumular artificialmente objetos en el borde.
Tampoco es una ley física medida o un ajuste estadístico validado. Las versiones
baja/alta conservan la asociación por objeto con su e nominal; el límite depende
de a, por lo que no producen una distribución de e independiente de la altura.

**Circular:** el perigeo no existe físicamente. Se mantiene el valor numérico de
omega nominal como calibre para no introducir un segundo cambio independiente,
pero se marca `argument_of_perigee_defined=False`. Se guarda explícitamente
`argument_of_latitude_deg`, calculado desde el estado cartesiano. Para e=0:
`u=(omega_nominal+M_nominal) mod 360`. Como M nominal es uniforme e independiente
de omega, u es uniforme condicionado a omega. No se necesita otra realización
aleatoria de fase. El mismo estado puede representarse con omega=0 y M=u;
las pruebas comprueban esa invariancia de calibre. Los valores numéricos de
omega del archivo circular **no son una orientación física del perigeo**.

### Tres alternativas de RAAN

Se usan U uniforme en [0,1) y Z normal estándar independiente. Se comparten U y Z
entre las alternativas de RAAN para reducir ruido de comparación.

| Escenario | Definición en grados |
|---|---|
| raan_uniform | Omega=360·U |
| raan_four_planes | Omega=(90·floor(4U)+5·Z) mod 360 |
| raan_single_plane | Omega=(15·Z) mod 360 |

El segundo modelo tiene cuatro planos equiprobables centrados en 0°, 90°, 180°
y 270°, con anchura normal de 5° antes de envolver. El tercero está concentrado
en 0°, con anchura de 15°. Centros, número de planos y anchuras son elecciones
de contraste, no parámetros inferidos del entorno. El 0° se refiere al marco
TEME a la época nominal. Su alineación relativa con una futura constelación
puede importar; habrá que barrer la orientación global si resulta influyente.

### Tres alternativas de argumento del perigeo

Se emplean otros U y Z, independientes de los de RAAN y compartidos dentro de
las tres alternativas de omega. Los resultados se envuelven módulo 360°.

| Escenario | Definición en grados |
|---|---|
| argp_uniform | omega=360·U |
| argp_bimodal | omega=(90+180·floor(2U)+10·Z) mod 360 |
| argp_aligned | omega=(15·Z) mod 360 |

El caso bimodal concentra periapsis en 90° y 270° con pesos iguales y anchura de
10°; el alineado se centra en 0° con anchura de 15°. Son escenarios exploratorios
de orientación, sin afirmar que alguno represente a todo el debris real. Aquí
se mantiene e nominal, por lo que las órbitas siguen siendo excéntricas. Para
e muy pequeña, omega tiene interpretación débil aunque el estado sea definido.

### Semillas, archivos y validación

Semilla maestra de alternativas: **20261105**. Los streams angulares se obtienen
con NumPy SeedSequence([semilla,1]) para RAAN y ([semilla,2]) para omega. Las
transformaciones de e son deterministas. Los registros son emparejados, no
independientes estadísticamente entre escenarios: es deliberado para comparar.
Esta primera entrega contiene una realización por escenario; las repeticiones
Monte Carlo futuras pueden cambiar `--seed` y deben guardarse por separado.

Las nueve poblaciones se almacenan como CSV.gz completos y autocontenidos en
`data/generated/sensitivity/`, junto a JSON por escenario y manifiesto global.
El CSV nominal se referencia por ruta y hash; no se copia como una décima
realización nueva. Los gzip usan mtime fijo para permitir reproducción de bytes.
Los originales CelesTrak, la población nominal y las figuras nominales permanecen
sin cambios. Se regeneran con:

```bash
.venv/bin/python scripts/generate_sensitivity_populations.py
```

Las figuras están en `outputs/sensitivity/`: una comparación de histogramas por
variable (nominal y tres alternativas) y nueve mapas variable–altitud–conteo.
Todos usan el estilo de publicación común, PDF vectorial y PNG a 300 dpi. Los
mapas usan a-R en X para comparar exactamente las mismas bandas de semieje;
en las figuras orbitales nominales anteriores X era hp, por lo que deben leerse
las etiquetas antes de comparar. La comparación de e usa conteos logarítmicos
en Y para mostrar la población circular concentrada en e=0 junto al resto.

Se auditan los 50.000 objetos de cada variante: controles idénticos a nominal,
cambio de una sola variable independiente, finitud, límites de ápsides, radio
del estado dentro de los ápsides, energía y convención circular. Las pruebas
verifican además uniformidad/circularidad angular, concentración y semillas.
Esto prepara el experimento; **no calcula todavía detecciones, SNR, calidad de
medidas ni readquisición**, que requieren implementar y fijar la misión.

## Corrección solicitada: RAAN y omega en 12, 8 y 4 grupos exactos

Se sustituyen las seis alternativas angulares anteriores. No se modifican ni
la nominal ni los tres archivos de poblaciones de excentricidad. Ya no se usan
distribuciones angulares uniformes continuas ni normales envueltas en estos
escenarios. Son distribuciones **uniformes discretas sobre ángulos exactos**,
sin dispersión alrededor de cada plano/posición.

| Variable | Escenarios | Separación |
|---|---|---|
| RAAN | raan_12_planes, raan_8_planes, raan_4_planes | 30°, 45°, 90° |
| Argumento del perigeo | argp_12_positions, argp_8_positions, argp_4_positions | 30°, 45°, 90° |

Para K=12,8,4 se asignan ángulos `360*j/K`, j=0,...,K-1. El primer valor es 0°;
360° no se incluye como posición adicional, pues equivale a 0°. Para 12 son
0°,30°,...,330°; para 8, 0°,45°,...,315°; para 4, 0°,90°,180°,270°.

Se genera una permutación aleatoria de rangos 0,...,49.999 por variable y se
asigna a cada objeto la categoría `floor(K*rango/50000)`. Así se obtiene un
reparto equilibrado sin relacionar sistemáticamente el ángulo con tamaño,
altitud o inclinación. En 12 grupos no es posible dividir 50.000 exactamente:
ocho tienen 4.167 y cuatro 4.166 objetos; los 8 grupos tienen 6.250 cada uno;
los 4, 12.500 cada uno. No se eliminan ni duplican objetos.

La semilla maestra sigue siendo 20261105 y los streams siguen separados para
RAAN y omega. Se comparte la misma permutación entre K de la misma variable:
los grupos de 4 se subdividen coherentemente al pasar a 8 o 12, reduciendo
ruido de asignación en la comparación. La permutación de RAAN es distinta de
la de omega. Se conserva el resto de elementos, fase M, tamaños, IDs, a, i,
epoch y marco como en el experimento anterior de una variable por vez.

Se recalculan estados y argumento de latitud para cada variante angular. La
excentricidad se conserva nominal en las seis variantes; estas posiciones
discretas de omega no se aplican a la variante circular, que sigue manteniendo
su argumento de latitud uniforme y el perigeo físicamente indefinido.

El generador verifica que los archivos retirados coincidan con sus hashes y
metadatos previos antes de eliminarlos. Se retiran los seis CSV/JSON angulares
antiguos y sus mapas, y se actualizan los manifiestos y comparaciones. Cualquier
archivo antiguo con ediciones ajenas al generador bloquea su retirada para
preservarlo. Los controles revisan soporte angular exacto, separación, conteos
equilibrados, semillas y conservación de una sola variable modificada. La
nominal y los archivos de excentricidad se comprueban además mediante hashes.

## Organización de outputs: solo PNG y población en el nombre

Por petición del usuario, `outputs/` contiene únicamente PNG, también dentro
de subcarpetas. Se retiran de esa carpeta los PDF generados; los PDF originales
de referencia en `docs/references/` se conservan. Esta preferencia sustituye
la exportación PDF/PNG descrita en secciones históricas anteriores.

- Nominal: `trace_nominal_<variable>_<tipo_de_grafica>.png`.
- Alternativas: `trace_<scenario_id>_vs_altitude.png`, por ejemplo
  `trace_raan_12_planes_vs_altitude.png` o
  `trace_eccentricity_circular_vs_altitude.png`.
- Comparaciones: `trace_comparison_nominal_raan_12_8_4_planes.png`,
  `trace_comparison_nominal_argp_12_8_4_positions.png` y
  `trace_comparison_nominal_eccentricity_circular_low_high.png`.

El manifiesto de figuras nominales se traslada de outputs a
`data/generated/figure_manifest.json`; se actualizan el generador y la auditoría
para esa ubicación. Los metadatos de variantes permanecen junto a sus CSV.
El renderizador conserva tipografía, estilo científico y 300 dpi, y genera
solo PNG con esta convención de nombres. La reorganización no cambia los datos
de población ni sus parámetros orbitales.

## Aclaraciones previas a la implementación óptica

El usuario confirma instrumento fijo a la plataforma, sin mecanismo de
apuntamiento ni seguimiento del debris durante la exposición. Esto no fija
todavía la ley de actitud del satélite: un instrumento solidario a una
plataforma nadir-pointing no es inercialmente fijo. La velocidad sobre el
detector debe calcularse en el marco de cámara, incluyendo la actitud y su
evolución, antes de asumir una velocidad angular aparente.

La velocidad transversal relativa es la componente perpendicular a la línea
instrumento–objeto; su cociente con la distancia da la velocidad angular de la
línea de visión en un marco inercial. La componente radial cambia el rango y
no produce esa traslación angular de primer orden.

La fase alpha se mide en el objeto, entre las direcciones al Sol y al
observador. Para la esfera lambertiana hay flujo para 90<alpha<180 grados:
Phi(alpha)=[sin(alpha)+(pi-alpha)cos(alpha)]/pi, alpha en radianes. A 135 grados
es aproximadamente el 4,8 % del flujo a fase cero, manteniendo lo demás fijo.
Esto no equivale a la reflexión de una cara plana opaca.

El baseline Excel impone exclusión solar de 90 grados entre línea de visión
al debris y dirección aparente al Sol. En geometría cercana a la Tierra y
rango mucho menor que 1 UA, esa separación es aproximadamente 180-alpha.
Por tanto, alpha=135 grados puede servir como prueba del modelo radiométrico,
pero no como caso operativo aceptado con ese baseline. La propuesta anterior
de usarlo operativamente debe corregirse. La simulación debe comprobar los
ángulos exactos, no aplicar únicamente esta relación aproximada.

En fase cero, la plataforma queda aproximadamente entre Sol y objeto; puede
proyectar sombra. La fase sola no determina el sombreado: hacen falta tamaño,
forma, distancias y tamaño angular finito del Sol. Fase cero se interpreta
como referencia fotométrica ideal sin ocultación; para eventos reales deben
comprobarse por separado sombra de la plataforma y eclipse terrestre.

La saturación es un límite cercano posible, independiente del tránsito:
depende del pico de electrones por píxel, full well y ADC/modo de ganancia.
No se puede calcular numéricamente con el baseline actual. El límite por
tránsito/velocidad angular depende de la trayectoria en el FOV y del criterio
de aceptación de una traza. Cruzar en menos de 77 ms no implica señal nula:
puede haber detección parcial, con señal integrada solo mientras el objeto
esté dentro del campo. Ninguno de estos criterios se adoptará como distancia
mínima absoluta sin declarar sus hipótesis.

## Actitud de referencia confirmada: zenit local

El usuario establece apuntamiento al zenit o a un ángulo respecto al zenit,
que será una variable de estudio posterior, sin seguimiento del debris y con
instrumento fijo a la plataforma. Para el caso inicial se adopta offset cero:
boresight radial hacia fuera de la Tierra, z=r_sat/|r_sat|.

Se interpreta «actitud fija» como orientación constante respecto al marco
orbital local, no respecto a las estrellas: mantener el zenit durante la
órbita requiere una rotación de la plataforma en el marco inercial. No se
introducen maniobras de exploración, seguimiento del objeto ni movimiento
interno del instrumento. El cálculo de la velocidad angular en cámara deberá
incluir la evolución geométrica del marco local.

Como convención de roll inicial, el eje horizontal del detector sigue la
componente tangencial de la velocidad orbital (normalizada y perpendicular
a z), y el eje vertical es y=z cruz x, completando una terna dextrógira.
Es una convención de modelado explícita, no un requisito confirmado de
hardware. Para órbitas no circulares se usa la velocidad proyectada sobre
el plano perpendicular al radio. El futuro offset de zenit requerirá además
definir su azimut en ese marco; no es necesario fijarlo para offset cero.

## Primera iteración óptica: curvas de SNR, alcance y full well

Se implementa `optical_validation.py` y el generador
`scripts/generate_optical_validation.py`. Esta iteración es un estudio
condicional del instrumento, no una simulación de detecciones de las diez
poblaciones. Los CSV de población no se modifican; se comprueban sus hashes.
Las figuras llevan `instrument_reference` en el nombre para evitar atribuirlas
a la población nominal. Se guardan únicamente PNG, junto a tablas fuera de
outputs, en `data/generated/optical/`.

### Baseline, lectura y nuevo dato del detector

Los valores de detector/óptica se leen directamente del workbook, con detección
de duplicados, vacíos, unidades incorrectas, rangos inválidos e incoherencia de
dimensiones. Se convierten a SI. Focal, f/# y escala de placa se derivan; no se
tratan como variables independientes del FOV y tamaño del sensor.

El usuario aporta una imagen de la especificación de full well:

- Highest pixel gain: **15 ke− = 15.000 e−/píxel**.
- Lowest pixel gain: **>140 ke−**, conservado como límite inferior estricto
  de 140.000 e−/píxel, no como capacidad exacta de 140.000.

Se añaden los campos FWC_high_gain, FWC_low_gain_lower_bound,
FWC_low_gain_relation y FWC_selection en Detector_Baseline. La versión previa
se archiva sin modificar en
`docs/references/archive/TRACE_Detector_Optical_Baseline_before_full_well.xlsx`.
La fuente de estos cuatro campos es la imagen aportada en la conversación;
no se ha proporcionado una ficha completa ni se inventa su referencia.

Se asocia explícitamente el modo conceptual High Gain del baseline con
highest pixel gain, usando 15.000 e− y su ruido de lectura existente. Esta
asociación debe confirmarse con la cadena electrónica real. **No se combina
el límite >140 ke− con el ruido de lectura High Gain para afirmar prestaciones
del modo Low Gain**: falta caracterizar su modo de lectura. No se conoce la
ganancia de conversión ni el límite ADC; full well es el límite de carga,
no necesariamente el primer límite de saturación electrónica.

### Fotometría y ruido

1. Esfera equivalente lambertiana. Los albedos del workbook se interpretan
   como **geométricos**. La irradiancia del objeto en la apertura es
   `E_solar(lambda)*p*(d/(2r))²*Phi(alpha)`, con
   `Phi=[sin(alpha)+(pi-alpha)cos(alpha)]/pi`. No se identifican estos albedos
   con reflectancia de una placa ni con albedo de Bond.
2. El Sol se aproxima por un cuerpo negro de 5.772 K normalizado a irradiancia
   bolométrica de 1.361 W/m² a 1 UA. Se integran fotones solamente en la banda
   del workbook, con 2.049 puntos espectrales; transmisión y QE constantes en
   esa banda. Es un modelo de estudio, no una tabla AM0 medida.
3. El fondo 22 mag/arcsec² se interpreta como AB y Fnu plano en la banda;
   cero AB=3.631 Jy. Se convierte a electrones/píxel/s usando el área angular
   de cada píxel. La magnitud del objeto se expresa como magnitud AB equivalente
   al mismo flujo de fotones en banda; no se afirma reproducir una banda V.
4. SNR de extracción de una sola imagen: señal / raíz de la suma de Poisson
   de señal, fondo, corriente oscura y varianza de lectura. Se usa una apertura
   rectangular con margen 3 sigma de PSF alrededor de la traza horizontal.
   El número de píxeles se redondea hacia arriba en ambas dimensiones. Se
   adopta fracción de señal erf(3/sqrt(2))², conservadora para traza larga;
   no es una extracción óptima ni un matched filter.
5. La PSF gaussiana tiene el FWHM en píxeles del Excel, sin añadir otro término
   de difracción a esa PSF efectiva. Se ignoran vignetting, distorsión, variación
   espectral de PSF y variaciones espaciales de respuesta del sensor.

### Movimiento y límites del dominio

El caso de referencia usa un observador **circular a 600 km**, elegido como
hipótesis de ensayo y no como arquitectura de TRACE ya decidida. LOS al zenit;
velocidad relativa transversal positiva en along-track. La cámara gira con
LVLH a n=sqrt(mu/(R+h)³); la tasa aparente es `abs(v_perp/r-n)`. Esta resta
incluye rotación geométrica de la plataforma sin seguimiento del debris; no
es una fórmula general para cualquier dirección de encuentro. Hay posible
cancelación de tasas. Los encuentros reales necesitarán geometría vectorial,
actitud y propagación de observador/objetivo.

La longitud de traza es tasa aparente por exposición dividido por escala de
placa. El tránsito de referencia exige recorrer como máximo el diámetro del
FOV circular nominal durante toda la exposición: cruce central, velocidad
constante y margen de PSF de borde no modelado. El FOV circular corresponde a
la dimensión corta del detector; no se explota la diagonal rectangular.
No se simulan trazas parcialmente fuera del sensor. Por ello, el límite por
tránsito es de aceptación operativa, no ausencia física de señal más cerca.

Se limita el dominio de fotometría a fuentes no resueltas, usando d/r <= FWHM
por escala de placa. Las fuentes extendidas pueden ser detectables, pero no
con este modelo de PSF puntual. Ese límite de dominio puede determinar el
borde inferior de una región elegible y no debe llamarse saturación.

Se aplica la aproximación de exclusión solar alpha<=180−sun_exclusion_min.
Fase cero es referencia ideal sin sombra del satélite; faltan dimensiones del
bus para modelarla. No se calculan eclipses, obstáculos, accesibilidad de
órbitas ni otros criterios geométricos de misión en estas curvas. Una distancia
ópticamente alcanzable puede exceder las disponibles entre objetos LEO.

### Saturación y distancia mínima

La carga de saturación se evalúa **por píxel**, no sobre la señal total de
la traza ni sobre la señal extraída para SNR. Se integra exactamente sobre
el píxel central la convolución de PSF gaussiana y segmento horizontal uniforme
de movimiento. Se adopta alineación centrada en píxel que maximiza la carga
pico. En velocidad cero converge a la integral de PSF puntual, no diverge.

A la carga pico del objeto se suma fondo y corriente oscura durante toda la
exposición. Se rechaza si la carga media esperada es >=15.000 e−/píxel. No se
añade ruido de lectura a la carga almacenada. Tampoco se añade margen contra
fluctuaciones de Poisson o incertidumbre de full well: se trata de un límite
determinista de primer orden, no una probabilidad de saturación.

La elegibilidad combina SNR>=5 (del workbook), ausencia de saturación,
tránsito completo, dominio no resuelto y fase permitida. Se buscan **todos
los intervalos detectados por la malla**, sin presuponer un único intervalo
continuo o monotonicidad de SNR/saturación. La cancelación de movimiento puede
concentrar señal en pocos píxeles y alterar el comportamiento de saturación.
Se registran los motivos del borde inferior: full_well, transit,
point_source_domain o SNR. Por tanto, la distancia mínima depende del objeto
y del escenario; no se impone una sola distancia mínima para todo el debris.

El barrido de rango abarca 100 m a 20.000 km en 1.537 puntos logarítmicos;
se refinan las transiciones con 32 bisecciones. Intervalos extremadamente
estrechos entre puntos pueden no detectarse: la resolución se declara y se
comprueba convergencia en casos de referencia. Si el intervalo llega al borde
del barrido se marca censurado, y un triángulo en la gráfica indica que no se
ha encontrado un máximo físico. No se interpreta una meseta de 20.000 km como
distancia máxima real. Los JSON guardan todos los intervalos; la línea superior
comparativa es su envolvente, no implica que todo rango intermedio sea válido.

### Barridos y presentación

Se generan 14 PNG: rango–tamaño de referencia y cinco familias paramétricas;
SNR–distancia para un objeto de 10 cm en esas cinco familias; y SNR–magnitud
para apertura, FOV y velocidad. Los valores de apertura, FOV y albedo proceden
de límites/escenarios del Excel; la referencia usa los puntos medios de FOV y
apertura. Se exploran fases 0°,30°,60°,85° y velocidades transversales
0,1;1;5;10;15 km/s. Referencia: p nominal, fase 60°, v=5 km/s. Los tamaños
abarcan 1 cm a 10 m (61 puntos). La magnitud usa movimiento a rango de 100 km.

No se separan curvas de SNR–magnitud por fase/albedo: a igual magnitud ya se ha
fijado el flujo recibido. Los efectos de fase y albedo aparecen en rango–tamaño
y SNR–rango. Se usa 10log10(SNR) para comparación con la figura del paper;
SNR=5 se dibuja a 6,99 dB, no a 5 dB. Las porciones saturadas o fuera del
dominio se distinguen con trazos punteados; los CSV contienen las banderas.

### Relación con el paper y validación

Se evalúan las ecuaciones (1)–(7) con los parámetros de su tabla 1 y una
extracción especificada de 10 píxeles: para placa de 10 cm, rango 100 km,
la potencia es 4,16632653e−13 W, señal 15.981,44 e− y SNR 125,693.
Es una comprobación de ecuaciones/unidades, **no una reproducción completa
de la figura 2 ni de su límite de magnitud**.

La ecuación (9), tal como está impresa, da dimensiones de 1/longitud para
el supuesto número de píxeles. Una construcción con ancho de Airy y longitud
de traza necesita un factor de longitud de onda: se registra el valor literal
y el diagnóstico multiplicado por c/nu, sin aplicar una corrección silenciosa.
El modelo TRACE usa su propia PSF medida/conceptual y extracción, no esa
expresión dimensionalmente incompleta. También se conserva la diferencia
entre el criterio de tránsito central empleado aquí y el factor de la
ecuación (11) del paper; no se atribuye nuestro límite a una reproducción
literal de ese resultado publicado.

Las pruebas verifican fase lambertiana, escalados de flujo, equivalencia AB,
velocidad/ruido, convergencia de rango, ecuaciones del paper, límite puntual
de PSF, integración numérica independiente del píxel con traza y rechazo por
full well. No se calculan aún probabilidades de detección, falsas alarmas,
números de objetos detectados, readquisición o calidad orbital de TRACE.

En la referencia D=80 mm, FOV=14°, fase=60°, p=0,2, v_perp=5 km/s, h_obs=600 km,
el primer intervalo elegible comienza aproximadamente a 1,567 km para objetos
de 1 y 10 cm, limitado por tránsito. Para un objeto de 1 m comienza a 53,734 km,
limitado por full well. Son resultados condicionales a este modelo y exposición;
no distancias mínimas universales ni límites calculados del ADC. Las distancias
máximas ópticas tampoco se recortan a la geometría de encuentros LEO.

## Tabla Excel y comparación del observador a 450/600 km

El usuario solicita una tabla de casos con una columna por variable y mínimo
y máximo al final, además de una presentación más clara. Se crea
`TRACE_Resultados_Estudio_Optico.xlsx` en data/generated/optical, reproducible
con scripts/export_optical_results.py. Incluye hojas Guía, Resumen_10cm, Casos,
Intervalos y Comparacion_altitud, tablas filtrables, unidades en encabezados y
paneles inmovilizados. No modifica el Excel de baseline.

Cada fila es un par tamaño/configuración, no un punto de SNR–magnitud. Los
casos nominales repetidos entre familias se consolidan por todas sus variables
y diámetro; se conserva la lista de familias originales. Los 19 registros de
configuración de los barridos contienen 14 configuraciones únicas, cada una
con 61 tamaños: **854 filas únicas a 600 km**. Se calculan otras 854 a 450 km
manteniendo los demás parámetros, con **1.708 filas** en Casos. No es un
factorial de todas las combinaciones posibles de instrumento y entorno.

Las dos últimas columnas son Alcance óptico mínimo [km] y Alcance óptico máximo
[km]. Se identifica la causa del límite inferior, número de intervalos y
censura del límite superior. Un máximo censurado de 20.000 km es un límite
inferior del alcance, no un máximo localizado. Si hay varios intervalos, la
envolvente mínimo–máximo puede contener huecos: Intervalos los conserva. Los
casos sin intervalo llevan alcances vacíos. Los porcentajes comparativos de
máximo quedan vacíos si cualquiera de los dos máximos está censurado.

Se añaden vistas de barras horizontales para objetos de 1, 10 y 100 cm, con
paneles separados de fase, albedo, FOV, apertura, velocidad y altitud. Cada
segmento azul es un intervalo elegible real del modelo; el mínimo se destaca
con punto naranja y se anota numéricamente, y el máximo también está rotulado.
Los ejes de distancia son lineales y compartidos dentro de cada figura. La
escala se adapta al tamaño del objeto. No se unen intervalos separados. Los
mapas analíticos anteriores se conservan para consulta técnica.

**Función de la altitud en el estudio actual:** 600 km fue una hipótesis de
ensayo para fijar el giro de una plataforma circular apuntada al zenit. No
es una altitud seleccionada u optimizada para TRACE. A rango, fase, tamaño y
velocidad transversal fijos, la altitud del observador no cambia directamente
la irradiancia recibida; cambia n en la tasa aparente abs(v_perp/r-n), y con
ello traza, extracción por píxeles, saturación y tránsito.

La tasa circular es 0,00108474152 rad/s a 600 km y 0,00112071920 rad/s a 450 km:
aumenta el 3,3167 %. En los 14 casos de 10 cm calculados, el máximo coincide
entre ambas altitudes porque el número entero de píxeles de extracción en el
borde de SNR permanece igual. Esto es parcialmente consecuencia de la
discretización del modelo, no prueba de invariancia física. El mínimo de
referencia pasa de 1,56725362 a 1,56723595 km (cambio de unos 1,8 cm); para
velocidades bajas el borde por full well sí cambia apreciablemente más.

Un cambio real de órbita altera además las distancias disponibles, velocidades
relativas, accesos, eclipses y tiempos de observación. Por ejemplo, un objeto
directamente al zenit a 800 km está a 200 km de un observador a 600 km, pero a
350 km de uno a 450 km: con iluminación idéntica, su irradiancia sería
(200/350)², aproximadamente 0,327 veces. Esta geometría no está incluida en
la comparación que mantiene r y v_perp como parámetros controlados. No se
deduce igualdad de rendimiento de misión ni se optimiza altitud con este ensayo.

## Comparación en una figura de 1, 5, 10 y 100 cm

Por petición del usuario se añade una figura con cuatro barras desplazadas por
condición: azul=1 cm, verde=5 cm, amarillo=10 cm y morado=100 cm. Se calculan
los cuatro diámetros exactos con el mismo modelo y baseline. En particular,
5 cm no se interpola ni se reemplaza por el punto próximo de la malla anterior.
Hay 60 combinaciones físicas únicas entre los casos de los cinco barridos a
600 km y la referencia adicional a 450 km, contando los cuatro tamaños.

Cada segmento es un intervalo elegible independiente. Círculo=extremo mínimo;
marca vertical=extremo máximo; flecha=alcance censurado por final del barrido.
Se conservan huecos. Se genera versión lineal y logarítmica con malla fina;
la segunda evita que la escala de los alcances de 100 cm oculte los de 1 cm.
No se comparan longitudes visuales de barras como si una escala logarítmica
fuera lineal: se lee la distancia indicada en el eje.

Los valores se exportan como size_comparison_cases.csv y se añaden al Excel
de resultados las hojas TamanosComparados e IntervalosTamanos. La hoja Casos
original de 1.708 filas se conserva. Para reproducir el Excel completo, ejecutar
primero export_optical_results.py y después plot_size_comparisons.py; el
exportador inicial reconstruye sus hojas y el segundo añade las nuevas.

El nuevo histograma usa el tamaño real de los 50.000 registros nominales,
conversión de metros a cm, sin pesos estadísticos. La vista completa incluye
todos los objetos mediante 60 bins logarítmicos (tamaño máximo observado
1.236,21 cm); el panel lineal de detalle usa bins de 0,25 cm para los 47.400
objetos de 1<=d<10 cm. Las alturas cuentan objetos por bin, no densidad: los
anchos de bin difieren entre paneles. Los CSV de bins permiten auditar ambos
conteos. Se verifica que el hash de la población nominal no cambia.

### Explicación física del giro LVLH

LVLH es el marco orbital local. Mantener el instrumento apuntado al zenit
requiere que el satélite cambie su orientación respecto a las estrellas a
medida que da la vuelta a la Tierra, aunque el instrumento no se mueva
respecto al bus. En la aproximación circular, el giro es 360 grados por órbita.
A 600 km la órbita dura 96,5389 min y el giro es 3,72907 grados/min;
a 450 km dura 93,4398 min y el giro es 3,85275 grados/min. El aumento del
3,3167 % es de esa tasa de orientación local, no de detectabilidad, alcance,
precisión ni un movimiento de seguimiento del debris.

Se añade un esquema radial con un objeto a 800 km y observadores alternativos
a 450 y 600 km: las distancias son 350 y 200 km. El ejemplo supone alineación
al zenit, no observadores reales coincidentes. Ilustra por qué una comparación
de misiones debe recalcular distancias/velocidades/encuentros, además del
pequeño cambio de giro usado en la prueba paramétrica actual.


## Revisión: observador a 450 km, tránsitos parciales y tamaño angular

Esta revisión sustituye en los resultados activos la referencia de 600 km y
el rechazo de tránsitos parciales descritos en las secciones históricas.
Todas las configuraciones del estudio óptico se recalculan a 450 km. Se
retiran de outputs las comparaciones antiguas 450/600 y el esquema asociado;
Git conserva sus versiones previas. La población nominal y las alternativas
orbitales no se modifican. El chequeo independiente del paper conserva los
parámetros publicados: es una referencia bibliográfica, no un caso TRACE.

**Tiempo visible y detección parcial.** Se conserva la LOS al zenit con actitud
fija en LVLH, sin seguimiento del objeto, y movimiento relativo transversal
en sentido along-track. Se aproxima la tasa como
omega=abs(v_perp/r - sqrt(mu/(R_T+450 km)^3)). Se mantiene la aproximación
paraxial/tangencial del modelo anterior: cruce central a lo largo del lado
corto del sensor, extensión de campo q=2 tan(FOV/2), velocidad y flujo
constantes durante una exposición. El tiempo de cruce es q/omega (infinito
si omega=0). El tiempo de señal es t_obj=min(t_exp,q/omega), y la longitud
de traza es L_px=omega*t_obj/delta. t_exp=77 ms.

Se supone que la exposición se centra temporalmente sobre el cruce para
obtener el máximo solapamiento posible. Por tanto, son ventanas ópticas
condicionales; una entrada cerca del final de una exposición puede producir
menos señal. No se asigna este tiempo máximo a encuentros reales ni se
calcula todavía la estadística de instantes de llegada. Tampoco se modelan
cuerdas descentradas, viñeteo o variación de PSF en los bordes.

La señal total antes de extracción es N_tot=Phi_gamma*A_eff*t_obj, y la
extraída S=N_tot*erf(3/sqrt(2))^2. Se conserva esta fracción conservadora
para la traza, incluyendo cruces del campo completo; no se hace una
integración bidimensional detallada del borde del detector. Se limita la
longitud de la máscara al ancho del campo:
n_px=ceil(min(L_px+6*sigma_px,q/delta))*ceil(6*sigma_px).
El ruido de fondo y la corriente oscura siguen integrando **t_exp completo**:
SNR=S/sqrt(S+n_px*((B_px+I_dark)*t_exp+sigma_read^2)). La saturación usa
N_tot multiplicado por la fracción pico de la PSF/traza, más fondo y dark
durante t_exp, frente a 15000 e-/píxel en High Gain.

Un tránsito parcial cuenta como detección condicional si SNR>=5, fuente
no resuelta, ausencia de saturación y exclusión solar satisfecha. El flag
full_transit solo clasifica; ya no veta. La línea del mínimo de tránsito
completo en las curvas es informativa. El barrido se amplía a 1 m–20000 km
con 2049 muestras logarítmicas y refinamiento de 32 bisecciones; siguen
indicándose límites censurados e intervalos separados. Las ventanas muy
estrechas pueden escapar a una malla finita.

**Umbral de tamaño angular.** Para FOV=14°, detector corto W=43,4 mm,
píxel p=10 micras y FWHM=2 px:
f=W/(2 tan(7°))=0,1767323175 m;
delta=p/f=5,658274696e-5 rad/px;
FWHM_px*delta=1,131654939e-4 rad, aproximadamente 23,34 arcsec.
No es una constante universal de resolución: depende del FOV y de la PSF
asumida. Es el límite operativo del modelo de fuente puntual, no una
validación de fotometría de fuentes extendidas ni un criterio de Rayleigh.
Con apertura variable y FOV fijo se mantiene FWHM=2 px por hipótesis; no se
recalcula una PSF por difracción en este estudio.

**Nueva figura de 50000 objetos.** Se calcula la distancia euclídea a un
observador ilustrativo en TEME=(6821,0,0) km, a 450 km sobre la esfera terrestre
de radio 6371 km, en la época nominal 2026-11-05T00:00:00Z. La posición
es una hipótesis explícita; no define inclinación ni fase orbital de la
futura misión. Cada registro nominal genera un punto sin ponderación.
Ejes logarítmicos: distancia en km y diámetro en cm. Línea roja discontinua:
d_cm=11,31654939*r_km. Debajo: d/r<=FWHM_px*delta, dominio no resuelto,
sombreado rojo transparente. Se incluyen los 50000 registros, aunque estén
ocultos por la Tierra o fuera del FoV; la figura no cuenta detecciones.
CSV de distancias, manifiesto con geometría/umbral/conteos y hash nominal
se guardan en data/generated/optical. El hash del nominal se verifica.

El Excel activo contiene 854 casos únicos a 450 km y hojas adicionales con
56 combinaciones exactas para diámetros de 1,5,10,100 cm. Los extremos mínimo
y máximo siguen siendo las dos últimas columnas; se conservan los huecos
en las hojas de intervalos. Ya no hay casos activos a 600 km.

## Color de los objetos: visibilidad y detectabilidad en la instantánea

A petición del usuario, la figura de tamaño frente a distancia conserva los
50000 objetos y el límite angular anterior, pero usa verde para los objetos
visibles y detectables y gris para el resto. **Debajo de la línea roja** se
cumple d/r <= FWHM_px*delta: fuente NO resuelta. Los 50000 objetos cumplen
este criterio para esta posición; estar en ese dominio no garantiza detección.

Se extiende la geometría ilustrativa ya adoptada, sin mover al observador
para buscar detecciones: r_obs=(6821,0,0) km TEME en
2026-11-05T00:00:00Z. Para disponer de velocidad y giro del campo se supone
órbita circular ecuatorial prógrada, v_obs=(0,7.644425686,0) km/s. Esta es una
hipótesis de visualización, no la selección de órbita de misión. Cámara fija
al bus en LVLH: zenit +X, horizontal +Y, vertical +Z. Campo rectangular
según W_x/(2f) y W_y/(2f); los 14 grados corresponden al lado corto.

El Sol se aproxima mediante longitud media y anomalía solar desde J2000,
corrección de longitud 1.915 sin(g)+0.020 sin(2g) grados y oblicuidad media.
La dirección ecuatorial media de fecha se utiliza como aproximación TEME,
sin corrección de nutación/equinoccio: no es una efeméride solar de precisión.
Se usa Sol en el infinito y sombra terrestre cilíndrica, sin penumbra, con
Tierra esférica opaca de radio 6371 km. La ocultación de la línea de visión
se calcula con la distancia mínima del segmento observador-objeto al centro
terrestre. No se modela sombra del propio satélite ni luz terrestre dispersa.

La fase de cada objeto es arccos(-LOS dot s_Sol). Se calcula la velocidad
relativa de los estados nominales, incluyendo la velocidad del observador;
se resta omega_LVLH cross delta_r para obtener el movimiento en cámara.
La norma de la derivada transversal de LOS determina la longitud de traza.
Se mantiene constante el albedo geométrico nominal p=0.2. No se usan fase
60 grados y velocidad 5 km/s como sustitutos de la geometría de los objetos.

La exposición de 77 ms se centra en la época nominal. En coordenadas
 tangentes (delta_y/delta_x,delta_z/delta_x), la intersección de la trayectoria
lineal con ambos límites del campo determina el tiempo de señal. Se admiten
solapamientos parciales con SNR>=5. Se conservan fondo/dark durante toda
la exposición y el criterio de carga pico High Gain <15000 e-/píxel.
La fotometría y PSF siguen siendo las aproximaciones del estudio óptico.
Para este mapa se exige que el centro esté dentro del campo en el instante
central; un objeto que solo entra después no se clasifica como visible en
esa instantánea. No hay propagación ni conteos acumulados de misión.

Visible = dentro del campo, línea no ocultada por la Tierra, iluminado y
exclusión solar de boresight >=90 grados. Verde = visible, SNR>=5,
fuente no resuelta, no saturado y exclusión solar de la LOS satisfecha.
Gris no identifica una causa única: los flags del CSV permiten distinguirlas.
El SNR se pone a cero en sombra (no hay señal solar directa); los demás
objetos tienen el SNR del solapamiento calculado, incluso si están ocultos,
pero nunca se clasifican como detectables si no son visibles.

Resultado de esta instantánea: 3 objetos dentro del campo; los 3 en sombra
terrestre; 0 visibles y detectables. Por ello los 50000 puntos son grises y
la leyenda verde indica cero. No se ha cambiado la geometría para forzar
puntos verdes. Esto no demuestra un rendimiento nulo de TRACE: únicamente
clasifica este instante y esta posición ilustrativa. El CSV de distancias
incluye ahora todos los flags, fase, tasa aparente, tiempo visible y SNR;
el JSON registra la geometría, el Sol aproximado y los conteos. Se verifica
que el hash de la población nominal permanece intacto.


## Época seleccionada con más visibles y tres categorías de color

Por petición del usuario se sustituye la instantánea anterior por otra con
más objetos visibles. Se mantiene la misma órbita circular ecuatorial
prógrada a 450 km, su estado inicial y la cámara al zenit. No se cambian
inclinación, óptica, albedo, población ni condiciones para fabricar detecciones.
Se propagan **ambos**: observador y los 50000 debris; cambiar solamente el
Sol o la etiqueta de fecha manteniendo sus posiciones no sería consistente.

Propagación breve de dos cuerpos: para cada debris M(t)=M0+sqrt(mu/a^3)*dt,
resolviendo Kepler y conservando a,e,i,Omega,omega. Se comprueba primero que
los elementos en dt=0 reproducen los seis componentes cartesianos guardados
(tolerancia relativa 1e-10 y absoluta 1e-8 en sus unidades). El observador
gira un ángulo n_obs*dt en su órbita circular. La cámara gira con él:
eje radial=zenit, eje tangencial=along-track, normal orbital=+Z. La línea
de visión, el campo rectangular, la fase solar y la velocidad aparente se
recalculan en cada época. Se conserva la integración de tránsitos parciales
centrada sobre la época seleccionada.

Se usan los ejes TEME fijos de 2026-11-05T00:00:00Z como referencia inercial
aproximada durante el barrido. No se propagan con SGP4 los GP originales ni
se pretende obtener estados TEME de fecha precisos; la población ya contiene
sus propios estados sintéticos. Se omiten J2, arrastre y cambio de los ejes
TEME. Se conserva la aproximación solar y de sombra cilíndrica anterior,
actualizando la dirección solar para cada instante. Es una visualización
breve de primer orden, no propagación de misión de alta fidelidad.

**Selección reproducible:** dt=0,15,30,... segundos, mientras dt<T_obs,
donde T_obs=5606.386763 s (93.439779 min). Son 374 instantáneas. Se elige
el mayor número de visibles (dentro del campo, sin ocultación, iluminados,
con exclusión solar del boresight satisfecha). Si hay empate se elige la
primera. No se usa el número de detecciones ni el SNR para seleccionar.
La tabla completa se guarda como snapshot_epoch_scan_450km.csv. Este es el
máximo **de la malla**, no un máximo continuo garantizado ni una tasa media.

Época elegida: 2026-11-05T01:23:15Z, dt=4995 s. Estado del observador en los
ejes nominales: r=(5281.479828,-4316.481418,0) km,
v=(4.837563616,5.919055865,0) km/s. Se conserva a=6821 km, e=0, i=0.
Hay 13 objetos dentro del campo y los 13 cumplen visibilidad. Ninguno cumple
SNR>=5: el SNR varía entre 0.00637 y 0.83546. Sus tamaños son
1.0159–9.7791 cm y sus distancias 628.94–1521.55 km.

Colores mutuamente excluyentes: verde=visible y detectable; lila=visible y
no detectable; gris=no visible. Resultado: **0 verdes, 13 lilas, 49987 grises**.
Los tres grupos conservan todos los objetos, incluso si sus puntos se
superponen. Los objetos destacados se dibujan encima del gris. El dominio
no resuelto sigue sombreado en rojo transparente por debajo de la línea;
los 50000 objetos lo cumplen también en esta época. Se actualizan la figura,
la tabla por objeto y el manifiesto, manteniendo el hash del nominal.

Esta instantánea se selecciona deliberadamente para mostrar más visibles;
no se usa como estimación imparcial del rendimiento de TRACE. Los ceros
verdes no se han reemplazado por detecciones hipotéticas para completar
la leyenda. El estudio óptico paramétrico y su Excel permanecen iguales.

## Comparación inicial del observador ecuatorial con órbitas SSO a 450 km

A petición del usuario se estudia si una geometría SSO mejora los objetos
detectables respecto a la ecuatorial anterior. Se conserva la población,
la cámara al zenit, los 450 km, apertura 80 mm, FOV corto 14 grados, exposición
77 ms, albedo nominal 0.2, ruido, High Gain, criterio no resuelto y SNR>=5.
No se sustituye la referencia ecuatorial ni el Excel del barrido instrumental.

**Definición SSO.** Para a=6371+450=6821 km y e=0 se usa la tasa secular
nodal de primer orden por J2:
dot(Omega)=-(3/2)*J2*sqrt(mu/a^3)*(R_J2/a)^2*cos(i),
igualada a +2*pi/(365.2422*86400) rad/s. Se toma mu=398600.4418 km^3/s^2,
J2=1.08262668e-3 y R_J2=6378.137 km. Este radio de referencia del potencial
J2 no cambia la convención esférica de altitud 6371 km usada por el proyecto.
La inclinación resultante es **97.18768658 grados**, retrógrada.

La inclinación SSO no fija el horario solar de la órbita. Se prueban cuatro
LTAN (hora solar local aproximada del nodo ascendente): 06:00, 10:30, 13:30,
18:00. A la época inicial 2026-11-05T00:00:00Z se aproxima
RAAN=RA_Sol+15*(LTAN-12), módulo 360 grados, con la misma dirección solar
aproximada que usa el modelo. RA_Sol=220.13259849 grados. Los RAAN iniciales
son, respectivamente, 130.13259849, 197.63259849, 242.63259849 y
310.13259849 grados. Es LTAN aproximado basado en esa RA solar, no una
conversión de efemérides solares de alta precisión. Se fija u inicial=0
(en el nodo ascendente). El argumento del perigeo en e=0 es una convención
numérica 0 y no una orientación física medible del perigeo.

**Comparación homogénea y límites.** Cinco escenarios: ecuatorial anterior y
las cuatro SSO. Misma ventana inicial y duración, una órbita del observador
T=5606.386763 s, muestreo cada 15 s (374 épocas por caso). Se propagan los
50000 debris y observador con el modelo corto de dos cuerpos, conservando
los planos en los ejes TEME iniciales. J2 se utiliza aquí para seleccionar
la inclinación SSO, pero no se integra dinámicamente ni para el observador
ni para los debris. En una órbita, la precesión solar buscada es de unos
0.064 grados; se omite junto al arrastre y demás perturbaciones en esta
aproximación. No es una simulación de mantenimiento SSO a largo plazo.
La cámara usa los ejes radial, tangencial y normal del plano inclinado,
incluyendo la dirección correcta del giro LVLH en el movimiento aparente.

En cada muestra se aplican campo, ocultación terrestre, iluminación,
exclusión solar, tiempo visible parcial, SNR y saturación como antes.
Se registran máximos simultáneos, promedios por muestra y conjuntos de IDs
visibles/detectables distintos en al menos una muestra. **No se suman como
objetos diferentes las reobservaciones de un mismo ID.** La tabla de barrido
completa y el resumen se guardan en sso_observer_scan.csv y
sso_observer_comparison.csv; hipótesis y hashes en sso_observer_audit.json.

Resultados de objetos distintos detectables **en las muestras**, durante
esta ventana: ecuatorial 1; SSO 06:00, 10; SSO 10:30, 3; SSO 13:30, 5;
SSO 18:00, 8. Máximos simultáneos detectables: 1 en todos los casos.
Máximos simultáneos visibles: 13,15,12,14,17 respectivamente.
Los objetos distintos visibles muestreados son 109,345,202,211,350.
El cero de la figura ecuatorial previa correspondía únicamente a su época
seleccionada por máximo de visibles, no a todo el barrido: en otra muestra
hay 1 detectable. No se debe comparar ese cero aislado con el acumulado
muestreado de una SSO.

El resultado preliminar favorece varias geometrías SSO en esta prueba,
pero el factor 10/1 de la SSO 06:00 **no es un factor de mejora de misión**.
La malla de 15 s puede perder tránsitos breves; no integra detecciones entre
muestras ni garantiza detectar todos los encuentros. Hay una única fase
inicial y una sola órbita por caso; el horario solar también cambia. Faltan
comparaciones más largas y resolución temporal adaptada a los encuentros
antes de estimar rendimiento, seleccionar LTAN u optimizar la misión.

Se añade una gráfica temporal comparativa y una figura tamaño-distancia
SSO con gris/lila/verde. Para esta última se escoge explícitamente el caso
con más IDs detectables muestreados (06:00) y dentro de él la instantánea
con más detectables simultáneos, después más visibles, empate a la primera.
Es una selección deliberada para mostrar las categorías, identificada en
la figura/manifiesto; no es el instante medio ni el de máximo de visibles
de toda la exploración. Su tabla por objeto se guarda aparte como
sso_selected_snapshot_objects.csv. Se conserva la figura ecuatorial previa
y se comprueba que la población nominal no cambia.

La imagen SSO seleccionada corresponde a 2026-11-05T00:22:00Z (LTAN 06:00):
10 visibles, de ellos 1 verde y 9 lilas; 49990 grises. El mayor SNR visible
en ese instante es 9.50919. Se ha verificado que los 50000 registros se
conservan y los conteos de la imagen coinciden con su tabla de objetos.


## Corrección visual: sombreado del dominio de fuentes resueltas

Por petición del usuario se mueve el sombreado rojo transparente **por encima**
del límite d/r=FWHM_px*delta en las figuras ecuatorial y SSO. Esta región
corresponde a fuentes resueltas y queda fuera de la hipótesis de objeto
puntual del modelo. La región inferior, no resuelta, queda sin sombrear.
Se actualizan las leyendas para identificar el dominio excluido. Este cambio
es visual: no modifica el criterio de tamaño angular, los parámetros,
los cálculos ni la clasificación gris/lila/verde de los objetos.

## Mapas de SNR: magnitud aparente y velocidad transversal frente a distancia

Por petición del usuario se añaden dos PNG científicos para la configuración
nominal: apertura 80 mm, FOV corto 14 grados, exposición 77 ms, High Gain,
observador circular a 450 km. La segunda figura usa **diámetro 5 cm**, elegido
explícitamente por el usuario, albedo geométrico 0.2 y fase 60 grados.
La primera fija v_perp=5 km/s. Ambas mantienen tránsitos parciales mediante
el máximo solapamiento de cruce central, ruido de fondo y dark durante toda
la exposición y el giro LVLH. No son gráficos de la población ni conteos
geométricos de misión; no se propagan órbitas para estos mapas instrumentales.

1. Eje Y: magnitud aparente AB equivalente en la banda 450–750 nm, entre
0 y 20 mag. Eje X: rango logarítmico de 0.01 a 20000 km, 1001 muestras.
La magnitud APARENTE ya determina el flujo recibido: NO se aplica otra vez
un factor inverso al cuadrado de la distancia. La distancia solo cambia
la velocidad angular, la traza y el tiempo de señal de una fuente con ese
brillo aparente fijo. Tampoco se multiplican de nuevo albedo y función de
fase: sus efectos sobre el flujo ya están contenidos en la magnitud.
No se fija diámetro en este mapa; se asume fuente puntual. Su condición de
resolución angular no puede inferirse solo de la magnitud sin más hipótesis.

Se calcula el límite de magnitud analíticamente dentro del modelo:
si V=n_px*((B_px+I_dark)*t_exp+sigma_read^2) y q=5,
S_req=(q^2+sqrt(q^4+4*q^2*V))/2;
m_lim=-2.5*log10(S_req/S_m0), donde S_m0 es la señal extraída para m_AB=0.
Se sustituye de nuevo en OpticalModel.evaluate para comprobar SNR=5 con
precisión numérica. Una fuente con mayor magnitud es más débil: la zona
por encima de m_lim tiene SNR<5 y se sombrea en rojo transparente.
La magnitud límite puede aumentar al crecer el rango porque, a flujo
aparente FIJO, la traza se acorta. No significa que alejar un objeto físico
de tamaño y fase constantes lo vuelva más fácil de detectar.

2. Eje Y: velocidad relativa transversal positiva along-track, 0–15 km/s,
751 muestras. Eje X: rango logarítmico 0.01–2000 km, 1401 muestras.
Se usa omega=abs(v_perp/r-n_LVLH) como en el estudio nominal. El brillo se
calcula ahora para el objeto fijo de 5 cm, e incluye su pérdida 1/r^2.
La línea roja discontinua es el contorno SNR=5 de la malla; se conserva
cualquier no monotonía debida a la compensación de giro LVLH y al número
entero de píxeles de extracción. Se interpola el contorno entre muestras:
en un salto del número de píxeles puede no existir una raíz exacta SNR=5.
El manifiesto registra la desviación al evaluar sus vértices (máxima
aproximadamente 0.28 de SNR en esta malla), sin suavizar artificialmente
los escalones físicos/discretos del modelo. El rojo marca SNR<5.

En ambas figuras la saturación de carga se marca con rayado gris separado:
el SNR formal calculado más allá de full well no representa fotometría lineal
válida. En la segunda, el dominio de fuente resuelta d/r>FWHM_px*delta se
marca con fondo gris (r<0.44183 km para 5 cm y FOV nominal). El rojo no
representa la unión de todos los motivos de rechazo; únicamente SNR<5.
Una región sin rojo aún debe cumplir fuente puntual, no saturación y las
condiciones geométricas/de iluminación de misión antes de hablar de detección.

Los barridos incluyen rangos que no corresponden necesariamente a encuentros
LEO disponibles: son mapas condicionales de respuesta del instrumento.
En el corte nominal v_perp=5 km/s, los intervalos elegibles para 5 cm son
0.44183079–298.15011885 km, coherentes con el estudio anterior.

Reproducción: scripts/plot_snr_range_maps.py. Curva de magnitud, vértices del
contorno de velocidad, mallas numéricas comprimidas NPZ y manifiesto con
unidades/hipótesis/hash del Excel se guardan en data/generated/optical.
Los PNG quedan en outputs/optical/summary y usan el estilo compartido a
300 dpi. Las poblaciones y los CSV de referencia ESA no se modifican.

## Gráficas de magnitud y velocidad con todos los objetos y color por tamaño

El usuario aclara que desea puntos para los 50000 objetos, no únicamente
mapas continuos del instrumento. Se añaden dos figuras de población nominal
sin sustituir los mapas instrumentales de referencia. Se usa la misma
instantánea SSO anterior: LTAN 06:00, 450 km, i=97.18768658 grados,
RAAN=130.13259849 grados, 2026-11-05T00:22:00Z. Se propagan todos los objetos
al instante seleccionado y se recalculan fases, velocidades y detectabilidad;
no hay una nueva búsqueda de una época favorable.

El color identifica tamaño, con intervalos disjuntos: azul 1<=d<5 cm
(45035 objetos), verde 5<=d<10 cm (2365), lila d>=10 cm (2600).
Exactamente 5 cm pertenece al verde; exactamente 10 cm pertenece al lila.
El marcador identifica detectabilidad: cruz para no detectable, estrella
de su mismo color de tamaño con borde negro para detectable. Se dibujan
los 50000 registros en cada figura, aunque muchos se superponen. Los
colores de estas dos nuevas figuras ya no representan visibilidad: se
siguen las nuevas instrucciones del usuario. No se cambian las anteriores
figuras con gris/lila/verde por visibilidad.

La magnitud es AB equivalente de la reflexión solar usando el tamaño,
albedo nominal 0.2, distancia y fase de cada objeto. Un objeto en sombra
o con la línea de visión tapada por la Tierra no tiene flujo solar directo
al instrumento en este modelo: no se le asigna una magnitud numérica ficticia.
Se representan sus puntos con la misma distancia y color en una franja
categórica rotulada «Sin señal», separada del eje numérico de magnitud.
Hay 9661 registros con magnitud solar directa finita y 40339 en esa franja.
No se descartan los objetos fuera del campo: pueden tener magnitud finita
si hay iluminación y línea de visión, pero no son detectables por la cámara.
El valor de posición gráfica de la franja no es una magnitud física.

El eje de velocidad muestra la norma del componente de v_debris-v_observador
perpendicular a la línea de visión, en km/s, antes de descontar el giro de
la cámara. El SNR individual usa la tasa angular vectorial calculada por
classify_snapshot, que sí descuenta el giro LVLH. No se sustituye por el
modelo escalar along-track cuando el movimiento real tiene otra dirección.

Se mantienen curvas y sombreado rojo solo como **referencia nominal**:
magnitud límite a 5 km/s en el primer panel; SNR=5 para d=5 cm, fase=60 grados
y movimiento along-track en el segundo. No existe una frontera universal
en esos planos para objetos con tamaños, fases, direcciones y velocidades
diferentes. Por eso el rojo de referencia no determina la clasificación
de los puntos; esta se calcula por objeto con SNR>=5, no saturación,
fuente puntual, iluminación, campo de visión y exclusión solar.
Un objeto detectable de más de 10 cm puede aparecer dentro de la zona roja
correspondiente al objeto de referencia de 5 cm sin contradicción.

Resultado: 10 visibles, de los que 1 es detectable; 49999 no detectables.
Son los mismos conteos de la instantánea SSO anterior. Los mapas no se
interpretan como conteos acumulados ni como rendimiento medio de misión.
El CSV population_snr_scatter_objects.csv guarda los 50000 IDs con grupo,
ambas coordenadas físicas, magnitud vacía cuando no está definida, posición
gráfica de franja, SNR y flags. El manifiesto population_snr_scatter_audit.json
registra conteos, geometría, convenciones y hashes. Se comprueba que la
población nominal no cambia.

Reproducción: `.venv/bin/python -m scripts.plot_population_snr_scatter`.
Las dos imágenes son PNG a 300 dpi en outputs/optical/summary, con prefijo
trace_nominal_sso450km y sufijo all_objects.

## Propagación de 24 horas, cruces por el campo y margen respecto a SNR=5

El usuario solicita acumular los cruces por el campo durante un día en la
órbita que dio más objetos distintos detectables: SSO nominal 450 km,
LTAN 06:00. Se conserva el estado inicial de aquella órbita: semieje
osculante kepleriano inicial 6821 km, e=0, i=97.18768658 grados,
RAAN=130.13259849 grados y argumento de latitud inicial 0. Se mantiene
el instrumento fijo al zenit, ejes horizontal along-track y vertical normal
orbital, apertura 80 mm, FOV corto 14 grados, exposición 77 ms y albedo 0.2.
El intervalo es 2026-11-05T00:00:00Z a 2026-11-06T00:00:00Z (86400 s).

**Decisión confirmada por el usuario sobre el eje Y.** Una magnitud aparente
no fija por sí sola el SNR de todos los cruces: también cambian la traza,
los píxeles de extracción y el tiempo de señal. El usuario elige representar
Delta_m=m_AB-m_AB,lim(SNR=5), calculando el límite individual con esa misma
geometría/exposición. Se muestran Delta_m frente a distancia y frente a
velocidad relativa transversal. Ahora existe una única frontera rigurosa
Delta_m=0: dentro del dominio válido, Delta_m<=0 equivale a SNR>=5.
El rojo transparente indica Delta_m>0, SNR<5. No se usan las curvas
nominales de 5 cm/5 km/s de las figuras anteriores para clasificar objetos.

**Dinámica.** El modelo breve de dos cuerpos utilizado antes no reproduce
la precesión SSO a lo largo de un día. Se añade gravedad zonal J2 a todos
los debris y al observador, integrando sus estados cartesianos con RK4,
paso 20 s. Se usa mu=398600.4418 km^3/s^2, J2=1.08262668e-3 y radio
geopotencial 6378.137 km. La altitud y ocultación conservan el radio esférico
6371 km. No hay propagación SGP4 nueva ni modificación de los GP originales:
se integran los estados de la población sintética ya entregada, en los ejes
TEME de su época inicial tratados como inerciales. No se añaden arrastre,
armónicos superiores, perturbaciones solar/lunar o correcciones de ejes
terrestres. El Sol mantiene el modelo aproximado anterior, actualizado
para cada instante, con sombra cilíndrica sin penumbra ni sombra del bus.

La órbita del observador es circular **osculante inicialmente respecto al
modelo central**; al integrar J2 su radio no es estrictamente constante.
En este día su altitud oscila entre 442.45635 y 450.00000 km: «450 km» es
la referencia inicial mantenida del caso anterior, no una imposición de
altitud constante ni un ajuste nuevo a altitud media exacta de 450 km.
La tasa/orientación de la cámara se deriva de r,v y aceleración J2,
incluyendo la variación de la normal del plano. La velocidad transversal
mostrada es la norma de la velocidad relativa perpendicular a LOS; la
traza usa la derivada de LOS en cámara, descontando su giro vectorial.

**Búsqueda de cruces, no una malla de detección de 20 s.** En cada intervalo
de propagación se construye una interpolación cúbica Hermite de las tres
coordenadas en cámara y sus derivadas. El campo rectangular exige X>0,
|Y|<h_x*X y |Z|<h_y*X, con h_x=W_x/(2f), h_y=W_y/(2f). Se usan las cotas
de Bernstein de los cúbicos como filtro conservador y se calculan todas
las raíces de las cinco caras, comprobando cada intervalo intermedio.
Un objeto puede generar un cruce aunque esté fuera del campo en ambos
extremos del paso: no se descarta por no aparecer en una instantánea.
La completitud se refiere a ese modelo interpolado con su precisión finita,
no a una certificación analítica de toda trayectoria real.

Los tramos adyacentes de un mismo objeto se unen en un único cruce. Una
salida seguida de reentrada constituye otro cruce. Se ordenan por entrada
y por ID para asignar ordinales cronológicos por objeto durante el día.
El primero usa punto circular; segundo, cruz; tercero y posteriores,
triángulo. Se cuentan también cruces en sombra o con veto solar para que
el ordinal represente cruces geométricos, no solo detecciones. Hay cuatro
cruces que intersectan los límites temporales de la simulación, marcados
como truncados en la tabla; no se inventa su trayectoria fuera del día.

**Un representante por cruce.** Se busca la exposición con mayor SNR válido
encontrado, con muestras de centros de exposición separadas como máximo
0.25 s, al menos 17 por cruce y refinamiento local de 65 puntos. Se añaden
puntos centrales, límites de exposición completa y nudos de interpolación.
El tiempo de señal es la intersección real entre [t-38.5 ms,t+38.5 ms] y
[entrada,salida]; se admiten cruces parciales y cruces de menos de 77 ms.
Fondo, dark y ruido de lectura siguen usando una exposición completa.
Se supone que podemos centrar una exposición en ese instante: es un estudio
con sincronización ideal, no una cadencia fija de frames con tiempo muerto
ni una simulación de electrónica de lectura. Se registra el mejor SNR
**encontrado**, sin afirmar un máximo global analítico.

El representante se busca primero dentro de las condiciones de validez:
objeto iluminado, sin ocultación, dentro del campo, exclusiones solares
satisfechas, fuente no resuelta y carga pico <15000 e-/píxel. Se conserva
la PSF/traza/extracción del modelo óptico previo. Si el cruce no contiene
un candidato válido, se conserva un representante visible o geométrico y
se dibuja en una franja categórica «Excluidos», sin una Delta_m ficticia.
Así el rojo indica únicamente SNR<5, y no se confunde una fuente saturada,
resuelta o sin luz con una detección válida por tener alto SNR formal.

Para cada exposición candidata se calcula el ruido no debido a la fuente
V=n_px*((B+I_dark)*t_exp+sigma_read^2) y la señal requerida
S_req=(25+sqrt(625+100*V))/2. Con S0, señal para m_AB=0 en esa misma traza
y tiempo visible, m_AB,lim=-2.5 log10(S_req/S0). Se conserva m_AB real,
m_AB,lim y Delta_m por separado en la tabla. Se verifica la equivalencia
Delta_m<=0 y SNR>=5 para todos los representantes válidos.

**Resultados de la simulación.** Se propagan los 50000 objetos sin alterar
sus archivos nominales. Se obtienen 16578 cruces de 13304 IDs distintos:
13304 primeros cruces (puntos), 2227 segundos (cruces) y 1047 terceros o
posteriores (triángulos). Un mismo objeto puede tener hasta 27 cruces.
Los colores siguen las instrucciones del usuario: azul 1<=d<5 cm,
verde 5<=d<10 cm, lila d>=10 cm. Hay 15060, 811 y 707 cruces en esos grupos.

8312 representantes cumplen el dominio del modelo; 8266 están excluidos.
271 cruces válidos alcanzan SNR>=5, pertenecientes a 251 objetos distintos.
Por tamaños son 2 cruces del grupo azul, 27 del verde y 242 del lila;
objetos distintos: 2,27,222 respectivamente. Hay 378 representantes con
señal durante menos de una exposición completa. Los resultados no son
una tasa operacional demostrada: dependen de esta población aproximada,
la dinámica adoptada, la iluminación y la sincronización ideal de exposición.

**Verificación numérica.** Se repite el día con paso 10 s para los primeros
5000 objetos: aparecen los mismos 1708 cruces, con los mismos IDs/ordinales.
Las diferencias máximas de entrada/salida frente a 20 s son 5.865/4.332 ms;
la mediana de la diferencia mayor de cada cruce es 0.429 ms. La diferencia
máxima de posición del observador es 10.905 m. Esto verifica convergencia
en esa subpoblación; no elimina toda incertidumbre de fronteras rasantes.
Se repite la fotometría de todos los cruces con muestras de centros cada
0.125 s: se mantienen las 16578 clasificaciones de validez y detección,
271 cruces SNR>=5 y 251 IDs distintos. Las pruebas incluyen cruces rápidos
entre extremos exteriores, múltiples entradas de un cúbico, interpolación,
gradiente del potencial J2, conservación de energía/convergencia a un día,
derivada del marco y normalización de una exposición parcial sintética.

**Archivos y reproducción.**
`.venv/bin/python -m scripts.propagate_day_encounters`
`.venv/bin/python -m scripts.plot_day_encounters`
Los datos están en data/generated/encounters: estados de interpolación NPZ,
manifiesto de propagación, CSV con una fila por cruce, resumen fotométrico
y validación numérica. Los PNG científicos de 300 dpi están en
outputs/optical/summary/trace_nominal_sso450km_24h_magnitude_margin_vs_*.png.
Las pruebas auxiliares de convergencia se reproducen con
`--step 10 --limit 5000 --tag validation_5000_step10` en el propagador y
`--sample .125 --suffix _refinement_check` en el segundo script. Se conserva
el resumen validado, sin archivar productos temporales duplicados.

El resumen de convergencia se regenera, tras los dos refinamientos, con
`.venv/bin/python -m scripts.validate_day_encounters`. Las 42 pruebas de
la suite pasan.


## Figuras de 24 h sin cruces excluidos

Por petición del usuario se elimina la franja «Excluidos» y todos sus puntos
de las dos gráficas de 24 h. Se representan solamente los cruces por el FoV
con representante válido (`valid=True`), conservando también los de SNR<5:
8312 cruces correspondientes a 7344 objetos distintos. De ellos 271 cruces
alcanzan SNR>=5, de 251 objetos distintos, igual que antes.

Los 8266 cruces excluidos también eran cruces geométricos por el campo,
pero no cumplían alguna condición del dominio óptico/de iluminación. Ahora
se omiten visualmente; no se eliminan del CSV completo ni se reclasifican.
No se cambia la propagación, el SNR, la normalización, los colores por tamaño
ni los ordinales/símbolos de revisita. Los ordinales siguen contando todos
los cruces del día, incluidos los que no se muestran: no se renumeran al
filtrar la figura. Se actualizan límites de ejes, pies de figura y manifiesto.

El renderizado se separa del cálculo para reutilizar resultados guardados:
`.venv/bin/python -m scripts.plot_day_encounters --plots-only`.


## Dos vistas adicionales con magnitud aparente sin umbral de SNR

Por petición del usuario se añaden las mismas dos figuras de cruces válidos
de 24 horas, pero con la magnitud aparente AB (`magnitude_ab`) directamente
en el eje Y, frente a distancia y velocidad relativa transversal. No se
dibuja la línea SNR=5, sombreado de SNR ni una clasificación visual por
detectabilidad. Se conservan los 8312 cruces válidos de 7344 objetos, los
colores de tamaño y los símbolos de primer/segundo/tercer cruce y posteriores.
Los cruces excluidos siguen sin representarse.

Se reutilizan exactamente los mismos registros e instantes representativos
del CSV existente; no se vuelve a propagar ni se cambia la selección de
exposición de cada cruce. Por tanto, aunque estas figuras no muestran SNR,
sus instantes siguen siendo los de mayor SNR válido encontrados en el
estudio previo. La magnitud se lee sin restarle la magnitud límite, usando
las mismas hipótesis de albedo, fase, iluminación y banda AB anteriores.
Las dos figuras de margen normalizado se conservan como vistas separadas.

Reproducción: `.venv/bin/python -m scripts.plot_day_encounters --plots-only --apparent-magnitude`.
Los nombres PNG contienen `sso450km_24h_apparent_magnitude_vs_`; el manifiesto
fotométrico añade `apparent_magnitude_figures` y su convención. El CSV de
cruces y las poblaciones no se modifican.


## Incorporación de skills de documentación LaTeX y Word

Se incorporan, por petición del usuario, los paquetes ZIP
`documentos-tecnicos-latex.zip` y `documentos-tecnicos-word.zip` como skills
locales en `.agents/skills/`. Se conservan sin modificaciones todos los
archivos de cada paquete: SKILL.md, metadatos de interfaz, guía de estilo,
plantilla TEX o DOCX, logo y cuatro esquemas de referencia, además del icono.
`docs/skills-provenance.json` registra los SHA-256 de los ZIP originales
y de cada archivo extraído. Se verifica la igualdad de bytes con las entradas
de ambos archivos comprimidos.

AGENTS.md registra cuándo aplicar cada skill en encargos de documentos.
Se reserva `docs/reports/<nombre>/` para fuentes, documentos compilados y
recursos vectoriales de informes, respetando que outputs/ solo contiene PNG.
Las convenciones físicas, fuentes y trazabilidad de TRACE se mantienen al
redactar documentos. Incorporar los paquetes no constituye la generación
o validación de un informe nuevo, ni cambia los cálculos del proyecto.

## Informe breve de población y validación óptica y radiométrica

Por petición del usuario se aplica la skill local documentos-tecnicos-word
para generar `docs/reports/poblacion-validacion-trace/TRACE_Informe_Poblacion_Validacion_Optica.docx`.
Se conserva la plantilla suministrada, incluido su logo; el informe contiene
siete páginas, 19 ecuaciones OMML editables, tres tablas de datos nativas y
cuatro figuras. El esquema de fase y solapamiento temporal tiene original SVG.
Las gráficas compactas usan el estilo científico compartido y los resultados
nominales archivados; no se repite la propagación ni se cambia la población.

El texto distingue datos e hipótesis: aproximación ESA–CelesTrak, soporte
limitado de los donantes, fase Lambertiana, PSF gaussiana, umbral SNR≥5,
fuente no resuelta, saturación por píxel y sincronización ideal del frame.
Un tránsito parcial contribuye con el tiempo de solapamiento dentro del
FoV; el ruido de fondo y de oscuridad integra la exposición completa.
El observador de referencia parte de una SSO circular osculante de 450 km,
cuya altitud varía bajo J2. Los conteos de encuentros se presentan sin pesos,
y los alcances ópticos condicionales no se interpretan como cobertura real.

`fuentes.json` registra los SHA-256 de las entradas utilizadas y
`verificacion.json` documenta los controles del DOCX y la revisión visual de
todas las páginas renderizadas. El PDF temporal solo sirve para revisión.
La reproducción documental usa `python scripts/build_trace_word_report.py`,
Pandoc y los paquetes descritos en la carpeta del informe. Los dos CSV de
referencia ESA previamente modificados en el entorno no se utilizan ni se
incluyen en este cambio; se preservan sus modificaciones.

## Revisión didáctica del informe Word para principiantes

Se sustituye el informe breve por una explicación progresiva: propósito,
fuentes identificadas por título y función, construcción de población,
definición de elementos orbitales, óptica/detector, señal y ruido, cruces
parciales, alcances y encuentros diarios. Se explican PSF, FWHM, QE, albedo
geométrico, fase, escala de píxel, exposición, ruido, fondo y full well con
valores, unidades y consecuencias físicas. Las hipótesis se distinguen de
los datos y de los resultados archivados.

Se reutilizan 22 figuras existentes, sin modificar sus datos ni regenerarlas.
Se retira el dibujo temporal del documento y sus recursos ya innecesarios;
el solapamiento parcial se explica con intervalos y el ejemplo de 52 ms de
señal dentro de una exposición de 77 ms. Se simplifica la notación de las
15 ecuaciones OMML para evitar los subíndices encadenados problemáticos.
Siete tablas nativas explican fuentes, elementos, parámetros y resultados.

Por indicación del usuario, todas las páginas llevan «TRACE · AEK» arriba
a la derecha, además del logo original a la izquierda. El pie utiliza los
campos PAGE / NUMPAGES. Después de las tablas se inserta un párrafo vacío
con separación explícita. Cada figura tiene guía de lectura y procedencia
trazable en fuentes.json. Se revisan todas las páginas renderizadas y las
ecuaciones, no solo el XML del Word.

Las curvas SNR archivadas usan 10·log10(SNR), según el generador existente;
el informe explica esa convención y que el umbral lineal 5 se representa a
6,99 dB. Se mantiene esa convención gráfica sin alterar los resultados.
El criterio de detección sigue aplicándose al SNR lineal.

Entrada principal: scripts/build_trace_intro_report.py. El comando anterior
build_trace_word_report.py delega en la revisión actual y conserva las
utilidades de formato compartidas. No se modifica la población nominal,
el Excel, los modelos ni los resultados científicos. Se preservan los dos
CSV de referencia ESA previamente modificados en el entorno.
