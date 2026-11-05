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
