"""Beginner-oriented revision of the TRACE Word report; uses archived results only."""
from pathlib import Path
import json,hashlib,sys
from zipfile import ZipFile
from lxml import etree
from docx.shared import Cm,Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH,WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import build_trace_word_report as base

ROOT=base.ROOT; REPORT=base.REPORT; ASSETS=base.ASSETS
# Short expressions with explicit, single-level subscripts avoid the ambiguous
# chained scripts in the previous cumulative-distribution expression.
base.EQUATIONS=[
 ('shell',r'w_j=n_j\,4\pi(R+h_j)^2\,\Delta h_j','3.1'),
 ('prob',r'P_j=\frac{w_j}{\sum_k w_k}','3.2'),
 ('orbit',r'a=R+h,\qquad h_p=a(1-e)-R,\qquad h_a=a(1+e)-R','4.1'),
 ('scale',r'\delta=\frac{s}{f},\qquad f=\frac{W}{2\tan(\Theta/2)}','7.1'),
 ('phase',r'\Phi(\alpha)=\frac{\sin\alpha+(\pi-\alpha)\cos\alpha}{\pi}','8.1'),
 ('flux',r'F=F_{\odot}\,p\,\frac{d^2}{4r^2}\,\Phi(\alpha)','9.1'),
 ('electrons',r'S=\eta\,F\,\frac{\pi D^2}{4}\,T\,Q\,t_s','9.2'),
 ('snr',r'\mathrm{SNR}=\frac{S}{\sqrt{S+N[(B+I)t_e+\sigma^2]}}','10.1'),
 ('omega',r'\omega\simeq\frac{v_{\perp}}{r},\qquad L=\frac{\omega_c t_s}{\delta}','11.1'),
 ('transit',r't_{\mathrm{FoV}}\simeq\frac{r\Theta}{v_{\perp}}','11.2'),
 ('overlap',r't_s=\max(0,\,\min(b,v)-\max(a,u))','11.3'),
 ('point',r'\frac{d}{r}\leq H\delta','12.1'),
 ('peak',r'q_{\mathrm{peak}}=f_{\mathrm{peak}}\,N_{\mathrm{obj}}+(B+I)t_e','12.2'),
 ('mag',r'm=-2.5\log_{10}\!\left(\frac{F}{F_0}\right)','15.1'),
 ('margin',r'\Delta m=m-m_5,\qquad\Delta m\leq0\ \Longleftrightarrow\ \mathrm{SNR}\geq5','16.1'),
]

class IntroWriter(base.Writer):
 def __init__(self,math):
  super().__init__(math)
  self.doc.core_properties.author='AEK'
  self.doc.core_properties.subject='Explicación introductoria con fuentes, conceptos y resultados'
  self.doc.styles['Normal'].font.size=Pt(11)
  self.doc.styles['Normal'].paragraph_format.space_after=Pt(6)
  self.doc.styles['Caption'].font.size=Pt(9)
  self.doc.styles['Caption'].paragraph_format.line_spacing=1.0
  section=self.doc.sections[0]
  self.doc.styles['Header'].paragraph_format.tab_stops.clear_all()
  p=section.header.paragraphs[0]
  p.paragraph_format.tab_stops.add_tab_stop(Cm(15.4),WD_TAB_ALIGNMENT.RIGHT)
  r=p.add_run('\tTRACE · AEK');r.font.size=Pt(10);r.bold=True
  f=section.footer.paragraphs[0]
  for child in list(f._p):
   if child.tag!=qn('w:pPr'):f._p.remove(child)
  f.alignment=WD_ALIGN_PARAGRAPH.CENTER
  for name in ('PAGE','NUMPAGES'):
   if name=='NUMPAGES':f.add_run(' / ')
   field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),name)
   r=OxmlElement('w:r');t=OxmlElement('w:t');t.text='1';r.append(t);field.append(r);f._p.append(field)
  self.figure_inputs=[]
 def table(self,*args,**kwargs):
  t=super().table(*args,**kwargs)
  # A true empty paragraph gives visible separation even if Word collapses
  # paragraph spacing at a table boundary.
  p=self.doc.add_paragraph();p.paragraph_format.space_after=Pt(3)
  p.paragraph_format.space_before=Pt(0);p.paragraph_format.line_spacing=1
  p.add_run().font.size=Pt(6)
  return t
 def equation(self,key):
  super().equation(key)
  p=self.doc.add_paragraph();p.paragraph_format.space_after=Pt(2)
  p.paragraph_format.space_before=Pt(0);p.add_run().font.size=Pt(3)
 def fig(self,path,section,num,caption,width=14):
  path=Path(path);p=self.doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
  p.paragraph_format.space_after=Pt(2);p.paragraph_format.keep_with_next=True
  p.add_run().add_picture(str(ROOT/path),width=Cm(width))
  self.caption('Figura',section,num,caption)
  self.figure_inputs.append(str(path))
 def page(self,title):self.heading(title,page=True)

def main():
 REPORT.mkdir(parents=True,exist_ok=True)
 w=IntroWriter(base.math_objects())
 O='outputs/';OP=O+'optical/';OS=OP+'summary/';S=O+'sensitivity/'
 # 1
 p=w.doc.add_paragraph('TRACE','Title');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
 p=w.doc.add_paragraph('Cómo construimos la población y\ncómo estudiamos su detección','Subtitle');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
 p=w.doc.add_paragraph('Guía introductoria · AEK · 6 de noviembre de 2026');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
 w.heading('1. Qué queremos averiguar')
 w.p('TRACE significa Tracking and Reacquisition Architecture for Cooperative Estimation of Uncorrelated Space Objects. La misión estudia si una cámara instalada en un satélite puede detectar fragmentos de basura espacial mediante la luz solar que reflejan. El instrumento está fijo al satélite y mira hacia el zenit: hacia fuera de la Tierra, aproximadamente en la dirección vertical local.')
 w.p('El trabajo tiene dos partes. Primero creamos un entorno de prueba: 50.000 objetos ficticios con tamaños y órbitas razonables. Después calculamos si la luz de esos objetos sería suficiente para distinguirlos del ruido de la cámara. Todo se calcula con modelos físicos y herramientas de Python, sin inteligencia artificial.')
 w.sub('1.1. Tres preguntas distintas')
 w.p('¿Dónde están los objetos? La población sintética responde con sus tamaños, órbitas y posiciones en una fecha común. No pretende identificar 50.000 fragmentos reales uno a uno.')
 w.p('¿Hasta qué distancia funciona el instrumento? La validación óptica y radiométrica calcula una ventana de distancia para un tamaño, iluminación y movimiento dados. “Óptica” se refiere a la formación de la imagen; “radiometría”, a cuánta luz y ruido registramos.')
 w.p('¿Cuántos encuentros aprovechables hay? La propagación de un día mueve el satélite y los objetos, comprueba cuáles atraviesan el campo de visión y aplica el modelo óptico a cada cruce.')
 w.sub('1.2. Cómo leer este informe')
 w.p('Las secciones 2–5 explican las fuentes y la población; 6–12 introducen el instrumento y sus ecuaciones; 13–16 muestran los resultados; 17 recoge los límites y próximos pasos. Cada figura se acompaña de una guía de lectura. Las referencias [1]–[6] se identifican en la sección 2: no es necesario haber visto los archivos del proyecto.')
 w.p('Idea clave: un objeto puede cruzar el campo de visión y aun así producir una señal demasiado débil. También puede ser brillante pero saturar el detector. Por eso “estar delante de la cámara” y “ser detectable” son condiciones diferentes.',bold=True)
 #2
 w.page('2. De dónde salen los datos')
 w.p('Se han combinado documentos con funciones diferentes. Los datos del entorno describen cómo podría ser la basura espacial; el Excel define el instrumento; el artículo científico orienta el cálculo de señal y ruido. Las instrucciones contenidas en los documentos no sustituyen las decisiones de modelado acordadas para TRACE.')
 w.caption('Tabla',2,1,'Fuentes utilizadas y función dentro del estudio.',above=True)
 w.table(['Referencia y documento','Qué aporta y cómo se utiliza'],[
 ('[1] ESA Space Environment Report 2026','Distribuciones aproximadas de tamaño, altitud e inclinación. Figuras 2.8–2.9 (página 31 del PDF) y 3.3a (página 68). Se digitalizan las figuras; no se dispone del catálogo completo subyacente.'),
 ('[2] CelesTrak: GP y SATCAT','CSV Chinese ASAT Test Debris_FENGYUN 1C, COSMOS 2251 Debris e IRIDIUM 33 Debris; SATCAT clasifica los objetos. Dan órbitas de referencia para excentricidad y orientación. El CSV active_satellites_GP se conserva, pero no se usa como donante de basura.'),
 ('[3] D’Anniballe, Felicetti y Hobbs (2025)','Preliminary analysis and design of an optical space surveillance and tracking constellation for LEO coverage. Acta Astronautica 231, 47–63. DOI: 10.1016/j.actaastro.2025.02.019. Archivo recibido: Space debris mission scientific paper.pdf.'),
 ('[4] TRACE_Detector_Optical_Baseline (1).xlsx','Resolución, píxeles, QE, transmisión, exposición, ruido, PSF y rangos de diseño. Full well de High Gain actualizado a 15.000 electrones/píxel.'),
 ('[5] TRACE_Mission_Validation_Specification (1).md','Documento de especificación recibido como contexto de validación. Para el comportamiento que aquí se describe prevalecen las decisiones posteriores y el código/resultados archivados.'),
 ('[6] Notas del Proyecto.md y resultados TRACE','Registro de hipótesis y procedencia; población nominal, tablas de alcance y resultados de cruces de 24 h. Son resultados de simulación, no observaciones del entorno real.')],[5.4,10])
 w.p('Ubicación en el repositorio: los PDF y el Excel están en docs/references/; los CSV originales, en data/raw/celestrak/; los resultados, en data/generated/; y las gráficas, en outputs/. El manifiesto fuentes.json de este informe registra las rutas y huellas SHA-256 utilizadas.',size=10)
 w.p('El artículo [3] inspira la estructura del presupuesto de señal y ruido. TRACE la adapta a su instrumento, su banda espectral, una esfera de reflexión difusa y el tratamiento de tránsitos parciales. No se presentan estos resultados como una reproducción literal del artículo.',size=10)
 #3
 w.page('3. Cómo elegimos tamaños y altitudes')
 w.p('LEO es la región de órbitas bajas terrestres. Aquí exigimos que las órbitas permanezcan entre 200 y 2.000 km de altitud y que el diámetro equivalente sea al menos 1 cm. El diámetro equivalente representa el tamaño de una esfera en el modelo; los fragmentos reales pueden tener otras formas.')
 w.p('Del informe ESA [1] tomamos curvas aproximadas de densidad y cantidad acumulada por tamaño. Una densidad expresa objetos por volumen: una capa más grande contiene más objetos aunque tenga la misma densidad. Por eso la probabilidad de elegir una capa se pondera por su volumen.')
 w.equation('shell');w.equation('prob')
 w.p('En estas ecuaciones, j identifica una capa; n es su densidad; h, su altitud; Δh, su espesor; R=6.371 km, el radio terrestre; w, un peso proporcional al número de objetos; y P, la probabilidad de seleccionar esa capa. Se usan unidades coherentes entre densidad y volumen.')
 w.fig(O+'trace_nominal_altitude_histogram.png',3,1,'Número de objetos sintéticos por intervalo de altitud media orbital. La altura de cada barra es un conteo; las concentraciones siguen los perfiles aproximados de ESA.',13)
 w.p('Se generan 47.400 objetos entre 1 y 10 cm y 2.600 de mayor tamaño. Dentro de cada grupo, el tamaño se sortea a partir de la curva acumulada N(>d): cuántos objetos superan un diámetro d. Se interpola en escala logarítmica y se supone independencia entre tamaño y altitud dentro del grupo. Esta es una aproximación, no una distribución conjunta completa medida por ESA.',size=10)
 #4
 w.page('3.1. Qué tamaños y combinaciones hemos obtenido')
 w.fig(O+'trace_nominal_object_size_histogram.png',3,2,'Distribución de tamaños de la población nominal. El eje horizontal expresa diámetro en centímetros; cada barra cuenta objetos en su intervalo.',14.8)
 w.p('Hay muchos más fragmentos pequeños que grandes. Esto es importante porque los pequeños reflejan menos luz y son más difíciles de detectar. El mayor objeto sorteado mide unos 12,36 m, aunque la curva de entrada se truncó a 38,29 m; un sorteo finito no tiene por qué alcanzar el límite de la curva.')
 w.fig(O+'trace_nominal_size_vs_altitude.png',3,3,'Mapa conjunto de tamaño y altitud. Cada celda reúne objetos; la barra de color indica cuántos hay, en escala logarítmica. Blanco significa celda vacía.',12.5)
 w.p('Cómo leer el mapa: elija una altitud en X y un tamaño en Y; el color indica la concentración. Es un mapa de población, no de detecciones. La escala logarítmica permite ver a la vez celdas con pocos objetos y celdas muy pobladas.',size=10)
 #5
 w.page('4. Cómo definimos una órbita')
 w.p('Una órbita necesita tamaño, forma, orientación y posición del objeto. No basta con decir “está a 800 km”. Utilizamos los seis elementos orbitales de la Tabla 4.1 y después los convertimos a posición y velocidad.')
 w.caption('Tabla',4,1,'Los seis parámetros orbitales, explicados desde su significado físico.',above=True)
 w.table(['Parámetro','Significado y origen en TRACE'],[
 ('Semieje mayor a [km]','Fija el tamaño de la elipse. Se obtiene de la altitud media h mediante a=R+h. No es la distancia entre el objeto y la cámara.'),
 ('Excentricidad e [sin unidad]','Mide cuánto se aparta la órbita de un círculo. e=0 es circular. Se toma de órbitas donantes de CelesTrak compatibles con permanecer en LEO.'),
 ('Inclinación i [°]','Ángulo del plano orbital respecto al ecuador. Cerca de 0° es ecuatorial; cerca de 90°, polar. Se sortea de la distribución ESA condicionada al perigeo.'),
 ('RAAN Ω [°]','Orienta el plano orbital alrededor del eje terrestre: indica dónde cruza el ecuador hacia el norte, medido desde una dirección de referencia.'),
 ('Argumento del perigeo ω [°]','Orienta el punto más cercano a la Tierra dentro del plano orbital. En un círculo no hay un perigeo físicamente distinguible.'),
 ('Anomalía media M [°]','Indica la fase temporal del objeto a lo largo de la órbita. Se sortea uniformemente entre 0 y 360°. No equivale a anomalía verdadera uniforme si la órbita es elíptica.')],[4.4,11])
 w.equation('orbit')
 w.p('El perigeo h_p es la altitud más baja y el apogeo h_a, la más alta. R es el radio terrestre. Se exige h_p≥200 km y h_a≤2.000 km. Esto limita cuánto puede crecer la excentricidad a una altitud dada: junto a los bordes del intervalo solo caben órbitas casi circulares.')
 w.p('Fecha de referencia: 5 de noviembre de 2026 a las 00:00:00 UTC. Todos los estados se expresan en el mismo marco, TEME. Una fecha común es indispensable para que “dónde está cada objeto” tenga un significado consistente.')
 #6
 w.page('4.1. Inclinación y excentricidad: origen y resultado')
 w.p('La inclinación se obtiene de la Figura 3.3a del informe ESA [1], digitalizada aproximadamente en celdas de 40 km de perigeo y 3°. Se selecciona la distribución de inclinación que corresponde al perigeo del objeto sintético.')
 w.fig(O+'trace_nominal_inclination_vs_altitude.png',4,1,'Inclinación frente a altitud de la población nominal. Las bandas muestran planos orbitales frecuentes; el color representa objetos por celda.',12)
 w.p('Para la excentricidad se usan los catálogos GP —General Perturbations, datos orbitales— de las tres familias de fragmentación [2]. Se cruzan con SATCAT, se filtran los objetos no adecuados y se retienen 2.567 donantes. Sus órbitas se llevan a la fecha común con SGP4 antes de extraer sus elementos instantáneos.')
 w.fig(O+'trace_nominal_eccentricity_vs_altitude.png',4,2,'Excentricidad frente a altitud. La forma del mapa combina los donantes disponibles y la exigencia de que perigeo y apogeo permanezcan dentro de 200–2.000 km.',10.5)
 #7
 w.page('4.2. RAAN y argumento del perigeo: qué se conserva')
 w.p('Para cada objeto se busca un donante de altitud parecida, preferentemente a ±100 km, cuya excentricidad sea compatible. Del mismo donante se copia la terna (e, Ω, ω). Así conservamos su asociación en vez de sortear esos tres parámetros por separado. La inclinación ESA se asigna de manera independiente de esa terna.')
 w.fig(O+'trace_nominal_raan_vs_altitude.png',4,3,'Orientación de los planos orbitales: RAAN frente a altitud. Las concentraciones reflejan las familias del catálogo donante; no son una medida de todo el entorno LEO.',10.5)
 w.fig(O+'trace_nominal_argument_of_perigee_vs_altitude.png',4,4,'Orientación del perigeo dentro del plano orbital. La estructura procede del mismo muestreo conjunto de donantes que la excentricidad y el RAAN.',10.5)
 w.p('Cuando no hay soporte local se recurre a hasta 50 donantes compatibles próximos en altitud. Ocurre en 10.498 objetos, el 20,996 %. Esos registros se marcan donor_local_support=False. El desajuste máximo llega a 1.576,51 km: la distribución es una aproximación híbrida y no debe presentarse como un catálogo empírico completo.',size=10)
 #8
 w.page('5. Cómo estudiamos la sensibilidad orbital')
 w.p('La población nominal se conserva sin cambios. Se construyen nueve alternativas, cambiando una sola variable cada vez. Se mantienen el semieje mayor, la inclinación y la anomalía media para que la comparación aísle el efecto de la variable modificada.')
 w.fig(S+'trace_comparison_nominal_raan_12_8_4_planes.png',5,1,'Comparación de RAAN nominal y alternativas con 12, 8 y 4 planos equiespaciados entre 0 y 360°. Menos planos significa mayor concentración de orientaciones.',14)
 w.fig(S+'trace_comparison_nominal_argp_12_8_4_positions.png',5,2,'Comparación del argumento del perigeo nominal y alternativas con 12, 8 y 4 posiciones equiespaciadas. Son escenarios diseñados, no distribuciones observadas.',14)
 w.p('Los grupos se reparten de forma equilibrada, sin dispersión aleatoria alrededor de cada ángulo. Estas figuras muestran cómo cambian las entradas. Por sí solas no dicen qué alternativa detecta más objetos: para ello hay que repetir los encuentros y la fotometría.',size=10)
 #9
 w.page('5.1. Excentricidad y límites de la población')
 w.fig(S+'trace_comparison_nominal_eccentricity_circular_low_high.png',5,3,'Alternativas de excentricidad circular, baja y alta frente al nominal. Sirven para comprobar cuánto dependen los resultados de la forma de las órbitas.',14.8)
 w.p('En las órbitas circulares el argumento del perigeo pierde significado físico. La posición dentro del plano se representa mediante el argumento de latitud, distribuido uniformemente de 0 a 360°. Así no se concentra artificialmente la población en un punto del círculo.')
 w.sub('5.2. Qué representa y qué no representa la población')
 w.p('La distribución de tamaños y altitudes es una aproximación a figuras de ESA; las orientaciones y formas proceden de tres familias de fragmentación. Sus datos no caracterizan directamente todos los objetos de 1 cm. Se mezclan referencias de fechas distintas, y tampoco se conservan todas las correlaciones posibles entre inclinación y los otros elementos.')
 w.p('El sorteo es reproducible: semillas 20260201 para tamaño/altitud, 20260202 para órbitas y 20260203 para fase orbital. Siete altitudes se ajustaron menos de 0,987 km para admitir una excentricidad compatible sin recortarla. Los controles verifican 50.000 identificadores, valores finitos, conversión orbital y límites de perigeo/apogeo.')
 w.p('La integral de densidad representa unos 354.821 objetos y daría un peso de 7,096 por muestra. Los resultados de detecciones de este informe son conteos directos de los 50.000 registros: no se multiplican por ese peso. La consistencia numérica no demuestra por sí sola fidelidad global al entorno real.',bold=True)
 #10
 w.page('6. Qué hace cada variable de la óptica')
 w.p('La óptica recoge luz y la enfoca sobre el detector. El detector transforma parte de esa luz en carga eléctrica. El Excel de referencia [4] proporciona los valores de partida; algunos parámetros ambientales, como albedo y fondo, siguen siendo hipótesis de trabajo.')
 w.caption('Tabla',6,1,'Parámetros ópticos nominales y sus efectos físicos.',above=True)
 w.table(['Variable y valor','Qué significa','Qué implica cambiarla'],[
 ('Apertura D = 80 mm','Diámetro útil por el que entra la luz.','El área crece con D²: más apertura recoge más fotones; también puede aumentar la saturación de fuentes brillantes.'),
 ('FoV corto Θ = 14°','Campo de visión: anchura angular de la escena en el lado corto del sensor.','Más campo cubre más cielo y alarga algunos cruces, pero con el mismo sensor hace que cada píxel cubra más ángulo y fondo.'),
 ('Focal f ≈ 176,73 mm','Distancia óptica que relaciona ángulos de entrada con posiciones en el plano focal.','Con sensor fijo, mayor focal estrecha el FoV y reduce el ángulo cubierto por cada píxel.'),
 ('Transmisión T = 0,8','Fracción de fotones que atraviesa la óptica en el modelo.','El 20 % se pierde antes del detector. Más transmisión aumenta la señal y el fondo óptico.'),
 ('Banda = 450–750 nm','Intervalo de longitudes de onda que se registra.','Delimita qué parte del espectro solar reflejado contribuye. Cambiarla cambia señal y fondo; no basta comparar vatios sin especificar la banda.'),
 ('PSF: FWHM = 2 píxeles','Una fuente puntual forma una mancha; PSF es su distribución de luz. FWHM es su anchura a la mitad del máximo.','Una PSF más ancha reparte la señal entre más píxeles: aumenta el ruido de extracción y reduce la carga pico.')],[4.1,5.5,5.8],param=True)
 w.p('PSF significa Point Spread Function. No quiere decir que el objeto mida físicamente dos píxeles: incluso un punto ideal se dibuja como una mancha. Aquí se supone una PSF gaussiana de 2 píxeles, constante al cambiar la apertura; no se recalcula un diseño óptico completo para cada diámetro.')
 w.p('Los barridos estudian aperturas de 60, 80 y 100 mm y campos de 8°, 14° y 20°. Son comparaciones bajo hipótesis controladas, no diseños ópticos fabricados ni calibrados.')
 #11
 w.page('6.1. Qué hace cada variable del detector')
 w.caption('Tabla',6,2,'Parámetros del detector: de los fotones a una medida con ruido.',above=True)
 w.table(['Variable y valor','Significado e implicación'],[
 ('Sensor: 4500 × 4340 píxeles','Número de celdas sensibles. Con píxeles de 10 µm, las dimensiones son 45 × 43,4 mm. Más píxeles permiten muestrear la escena con más detalle para un FoV dado.'),
 ('Paso de píxel s = 10 µm','Tamaño físico de un píxel. Junto con la focal determina su tamaño angular, llamado pixel scale o escala de píxel.'),
 ('QE o Q = 0,9','Eficiencia cuántica: en promedio se generan 0,9 electrones por fotón que llega al sensor en este modelo. Es una eficiencia de conversión, no una probabilidad de detección de objetos.'),
 ('Exposición t_e = 77 ms','Tiempo que acumula carga cada imagen. Una exposición más larga puede recoger más señal, pero también más fondo, corriente oscura y desplazamiento de la imagen.'),
 ('Ruido de lectura σ = 5 e⁻ RMS/píxel','Incertidumbre introducida al leer la carga de cada píxel. Se paga una vez por lectura y contribuye como varianza σ².'),
 ('Corriente oscura I = 0,01 e⁻/píxel/s','Carga generada sin luz. Su media puede calibrarse; su fluctuación estadística sigue contribuyendo al ruido.'),
 ('Full well: 15.000 e⁻/píxel','Capacidad máxima de carga en High Gain. Si el píxel más iluminado se llena, la imagen se satura aunque la señal total parezca buena.'),
 ('Fondo: 22 AB mag/arcsec²','Brillo superficial uniforme supuesto del cielo. Cada píxel recoge fondo según su área angular y toda la exposición. No es la magnitud de un objeto individual.')],[5,10.4],param=True)
 w.p('El dato de Low Gain es >140.000 electrones/píxel: una cota inferior, no una capacidad exacta. No lo combinamos con el ruido de lectura de High Gain para afirmar prestaciones de otro modo. La saturación electrónica del ADC tampoco se incluye por falta de caracterización completa.')
 w.p('Unidades: e⁻ significa electrones; ms, milisegundos; µm, micrómetros; nm, nanómetros. RMS expresa el tamaño típico de una fluctuación. Los electrones son cuentas de carga, no energía óptica.')
 #12
 w.page('7. Escala de píxel: cuánto cielo cabe en un píxel')
 w.p('Imagine una cuadrícula sobre el cielo. Cada celda es un píxel del detector. La escala δ indica el ángulo que cubre cada celda. Se calcula con el tamaño físico s y la focal f; también podemos obtener f a partir del ancho corto W=43,4 mm y el FoV corto Θ.')
 w.equation('scale')
 w.p('Con s=10 µm y f≈176,73 mm obtenemos δ=5,6583×10⁻⁵ rad/píxel, equivalentes a 11,67 segundos de arco por píxel. Un segundo de arco es 1/3.600 de grado. Para usar estas ecuaciones todos los tamaños deben estar en la misma unidad y Θ en radianes.')
 w.p('En las curvas con eje SNR [dB], el umbral lineal SNR=5 aparece a 6,99 dB, no a 5 dB. La sección 10 explica esa conversión.')
 w.p('La PSF de 2 píxeles equivale por tanto a una anchura angular de 2δ=1,13165×10⁻⁴ rad=23,34 segundos de arco. Este es el valor de FWHM_px·δ que define el límite de objeto puntual del modelo.')
 w.fig(OP+'trace_instrument_reference_snr_vs_range_fov.png',7,1,'SNR frente a distancia para distintos FoV, con las demás entradas de referencia fijadas. La línea de SNR=5 separa señal suficiente e insuficiente en este barrido.',14.5)
 w.p('Por qué cambiar el FoV no tiene un efecto único: con el mismo sensor, ampliar el campo aumenta el ángulo de cada píxel. La imagen se desplaza por menos píxeles para una misma velocidad angular, pero cada píxel recibe más fondo. También cambia el tiempo dentro del campo. La curva reúne esos efectos; “más FoV” no equivale siempre a “más sensibilidad”.')
 #13
 w.page('8. Albedo y fase: cuánta luz refleja el objeto')
 w.p('El albedo geométrico p describe cuán brillante es una superficie comparada con una referencia difusa. No debe interpretarse sin más como un porcentaje de toda la energía reflejada. En TRACE se usa p=0,2 y se exploran 0,05 y 0,5; estos valores son hipótesis, no medidas individuales de los 50.000 objetos.')
 w.p('La fase α es el ángulo Sol–objeto–observador, medido en el objeto. A 0° vemos su cara iluminada de frente; a 90°, parte de ella; por encima de 90° todavía puede verse una zona iluminada. Solo a 180° se anula la luz de la esfera difusa ideal. Un eclipse es otra condición geométrica: que la Tierra u otro cuerpo tape la iluminación.')
 w.equation('phase')
 w.p('Φ es la fracción de brillo respecto a fase cero en el modelo de esfera lambertiana: Φ(0°)=1, Φ(60°)≈0,609 y Φ(90°)≈0,318. La ecuación se evalúa en radianes. Una superficie lambertiana dispersa la luz de forma difusa; los destellos especulares reales no se modelan.')
 w.fig(OP+'trace_instrument_reference_snr_vs_range_phase.png',8,1,'Efecto de la fase sobre SNR y distancia. Compare curvas a una misma distancia: una fase menos favorable reduce la luz recibida y normalmente acorta el alcance.',14)
 w.p('El caso de referencia de las curvas utiliza fase 60°. En los encuentros de un día se calcula la fase de cada geometría Sol–objeto–observador; no se obliga a todos los cruces a tener 60°.')
 #14
 w.page('9. De la luz reflejada a los electrones de señal')
 w.p('La señal se construye en dos pasos. Primero calculamos los fotones que llegan al instrumento. Después aplicamos el área de apertura, las pérdidas de la óptica, la eficiencia cuántica y el tiempo durante el que el objeto contribuye a la imagen.')
 w.equation('flux')
 w.p('F es el flujo recibido en fotones por metro cuadrado y segundo. F⊙ es el flujo solar de fotones en la banda 450–750 nm a 1 unidad astronómica; p, el albedo geométrico; d, el diámetro; r, la distancia cámara–objeto; y Φ, el factor de fase. d y r deben estar en la misma unidad. Doblar el diámetro multiplica el flujo por cuatro; doblar la distancia lo divide por cuatro.')
 w.p('F⊙ se obtiene integrando el espectro solar en la banda. Se aproxima el Sol por un cuerpo negro de 5.772 K normalizado a 1.361 W/m²; cada fotón de longitud de onda λ tiene energía hc/λ, con h constante de Planck y c velocidad de la luz. Así convertimos energía óptica en número de fotones, sin confundir ambas cantidades.')
 w.equation('electrons')
 w.p('S es la señal extraída en electrones; D, la apertura; T, la transmisión; Q, la QE; t_s, el tiempo efectivo de señal; y η≈0,9946, la fracción recuperada por la máscara de extracción ideal. El área πD²/4 se expresa en m² si F está en fotones/m²/s.')
 w.fig(OP+'trace_instrument_reference_snr_vs_range_albedo.png',9,1,'A mayor albedo, mayor señal a la misma distancia. El efecto se calcula con el mismo instrumento; no significa que conozcamos el albedo real de cada fragmento.',13.5)
 #15
 w.page('10. Qué es el SNR y cómo decidimos una detección')
 w.p('Una imagen tiene una señal útil y fluctuaciones que pueden ocultarla. SNR significa Signal-to-Noise Ratio: relación señal/ruido. Un SNR de 5 indica que la señal calculada es cinco veces el ruido típico de la medida. Aquí se usa como umbral de estudio; no es una garantía de detección por un algoritmo real.')
 w.equation('snr')
 w.p('S es la señal del objeto, en electrones. N es el número de píxeles usados para sumar su imagen. B es la tasa de fondo por píxel; I, la corriente oscura por píxel; t_e, la exposición completa; y σ, el ruido de lectura por píxel. S y las cantidades dentro de la raíz se interpretan como cuentas y varianzas de electrones en el modelo de Poisson.')
 w.p('En las gráficas archivadas se usa la convención SNR_dB=10·log₁₀(SNR). Así, el umbral lineal SNR=5 se dibuja a 6,99 dB y SNR=1 a 0 dB. Esta es la escala concreta de estas figuras; la decisión de detección siempre usa el SNR lineal. Un valor negativo en ese eje indica SNR menor que uno, no luz negativa.')
 w.p('La señal del propio objeto también fluctúa: de ahí el término S bajo la raíz. El fondo y la oscuridad acumulan ruido durante toda la exposición, incluso si el objeto solo está presente parte del tiempo. La lectura aporta una incertidumbre adicional en cada píxel que se extrae.')
 w.fig(OP+'trace_instrument_reference_snr_vs_range_aperture.png',10,1,'Comparación de aperturas. Una apertura mayor recoge más fotones y eleva el SNR en los casos mostrados. La línea horizontal señala SNR=5.',13.5)
 w.p('Si la luz se reparte por una traza larga, crece N y sumamos ruido de más píxeles. Por eso dos objetos con la misma magnitud aparente pueden tener distinto SNR: no tienen por qué tener el mismo tiempo de señal, traza o fondo de extracción.')
 #16
 w.page('11. Movimiento y tiempo dentro del FoV')
 w.p('La velocidad relativa es la diferencia entre la velocidad del debris y la del observador. Su componente transversal v⊥ es la parte perpendicular a la línea que los une: es la que hace desplazarse la imagen por el cielo. La componente que se acerca o aleja cambia la distancia, pero no produce por sí sola ese barrido lateral.')
 w.equation('omega')
 w.p('ω es la velocidad angular aproximada en rad/s. L es la longitud de la traza en píxeles, δ la escala angular por píxel y ω_c la velocidad angular vista por la cámara, que incluye su giro al mantener el zenit. En esta ecuación L se refiere al tiempo efectivo t_s, no siempre a los 77 ms completos.')
 w.equation('transit')
 w.p('La aproximación de tránsito usa Θ en radianes y supone un cruce central, movimiento uniforme y distancia casi constante. Un cruce por un borde recorre una cuerda menor. La simulación utiliza las entradas y salidas reales del campo rectangular, no esta aproximación para todos los objetos.')
 w.sub('11.1. Un tránsito parcial sí puede contar')
 w.p('Si la exposición ocupa el intervalo [a,b] y el objeto está dentro del campo entre [u,v], el tiempo que aporta señal es la longitud de la intersección:')
 w.equation('overlap')
 w.p('Ejemplo: exposición de 0 a 77 ms y objeto dentro del campo de 25 a 110 ms. La parte común va de 25 a 77 ms, por lo que t_s=52 ms. La señal integra 52 ms; el fondo y la oscuridad, 77 ms. No se exige que todo el tránsito quepa en la exposición ni que el objeto permanezca 77 ms. Se acepta si alcanza SNR≥5 y cumple los demás criterios.')
 w.p('La simulación selecciona el mejor centro de exposición encontrado para cada cruce: sincronización ideal. Una cámara con cadencia fija y tiempos muertos podría aprovechar menos cruces. Esta diferencia debe estudiarse antes de estimar una tasa operacional de detección.')
 #17
 w.page('12. Por qué existe un límite cercano')
 w.p('Acercar un objeto aumenta su brillo, pero no garantiza que la imagen siga siendo válida. Puede verse extendido, saturar un píxel o moverse tan deprisa que el tiempo útil sea muy corto. El mínimo admisible es el que impone la combinación de estos criterios; no se atribuye solo a la velocidad.')
 w.equation('point')
 w.p('d/r es el tamaño angular aproximado del objeto; H=2 píxeles es la FWHM de la PSF y δ, la escala de píxel. Debajo de esa anchura lo tratamos como fuente puntual. Para 10 cm, este criterio por sí solo requiere r≥0,884 km. No significa que todo objeto más lejano se detecte: todavía debe estar iluminado, en el campo y tener señal suficiente.')
 w.equation('peak')
 w.p('N_obj es el total de electrones del objeto antes de extracción; f_peak, la fracción que cae en el píxel más cargado, calculada con PSF gaussiana y traza; q_peak, su carga incluyendo fondo y oscuridad. Se exige q_peak<15.000 e⁻. Se comprueba un píxel, no la suma completa de la traza.')
 w.fig(OS+'trace_nominal_unresolved_source_limit_sso_observer_450km.png',12,1,'Instantánea de la población y límite puntual. Por encima de la línea roja el objeto sería resuelto y queda fuera del modelo; por debajo cumple esta condición. Los colores separan visibilidad y detección en esa instantánea.',12.7)
 w.p('En esta instantánea, gris significa ni visible ni detectable; lila, visible pero no detectable; verde, visible y detectable. La región sombreada está por encima del límite y queda fuera de la hipótesis puntual.',size=10)
 w.p('Esta figura es una foto geométrica de un instante, no el resultado acumulado de un día. Cada punto es un objeto; su distancia depende de su posición y de la del observador en ese instante.',size=10)
 #18
 w.page('13. Ventanas de alcance: qué nos dicen los barridos')
 w.p('En estas pruebas fijamos condiciones de referencia y cambiamos una variable cada vez. Referencia: apertura 80 mm, FoV corto 14°, exposición 77 ms, fase 60°, albedo 0,2, velocidad transversal 5 km/s y observador nominal a 450 km. Se combinan SNR, saturación y fuente puntual.')
 w.fig(OP+'trace_instrument_reference_range_vs_size_nominal.png',13,1,'Ventana óptica nominal frente a tamaño de objeto. Lea el mínimo y el máximo para cada tamaño; los tránsitos parciales pueden contribuir. Las distancias son entre cámara y objeto, no altitudes orbitales.',13)
 w.p('Cómo leerla: seleccione un tamaño en el eje horizontal y busque las distancias que permanecen dentro de la ventana admisible. El límite superior exige señal suficiente; el inferior reúne restricciones de saturación, tamaño angular y tiempo útil. La escala logarítmica permite abarcar varios órdenes de magnitud.')
 w.p('Estas distancias son condicionales: una ventana amplia no implica que existan muchos objetos en ella, ni que queden iluminados y dentro del FoV. Para convertir alcance en detecciones hay que simular los encuentros.')
 w.caption('Tabla',13,1,'Alcances del caso de referencia para cuatro tamaños.',above=True)
 w.table(['Diámetro [cm]','Mínimo [km]','Máximo [km]'],[('1','0,088','37,19'),('5','0,442','298,15'),('10','0,884','697,54'),('100','53,755','8.502,11')],[4.4,5.5,5.5])
 w.p('Para 100 cm el límite cercano es mucho mayor que el que daría solo la condición puntual: interviene la saturación. Los 8.502 km del máximo son un alcance óptico condicional, no una afirmación de visibilidad desde una órbita LEO para todas las direcciones.',size=10)
 w.page('13.1. Cómo cambian las ventanas al variar el diseño')
 w.p('Estas dos figuras conservan el mismo modelo nominal y cambian una sola entrada. Así podemos atribuir la diferencia al parámetro estudiado; no estamos comparando dos misiones completas.')
 w.fig(OP+'trace_instrument_reference_range_vs_size_aperture.png',13,2,'Alcance frente a tamaño para distintas aperturas. La óptica de mayor diámetro recoge más luz, pero también puede saturar antes a distancias pequeñas.',12)
 w.fig(OP+'trace_instrument_reference_range_vs_size_velocity.png',13,3,'Alcance frente a tamaño para distintas velocidades transversales. La velocidad modifica tanto el tiempo útil como la traza y la saturación; no produce un simple factor constante.',12)
 w.p('Cada curva es un resultado instrumental. Los intervalos separados y los máximos limitados por el barrido deben leerse según la leyenda; no son una distribución de la población. Estos efectos también se reflejan en las curvas SNR de las secciones anteriores.',size=10)
 #19
 w.page('14. Del instrumento al encuentro: simulación de un día')
 w.p('Para saber qué objetos pasan realmente por la cámara hay que dar una fecha y mover todas las órbitas. Se simulan 24 horas desde el 5 de noviembre de 2026 a las 00:00 UTC. Se utiliza el mismo nominal de 50.000 objetos, sin regenerarlo.')
 w.caption('Tabla',14,1,'Órbita y actitud del observador utilizadas en la simulación diaria.',above=True)
 w.table(['Parámetro','Valor o interpretación'],[
 ('Órbita inicial','Circular osculante a 450 km; semieje mayor inicial 6.821 km; excentricidad inicial 0.'),
 ('Inclinación','97,1877°: órbita heliosíncrona aproximada, SSO. Su plano precesa aproximadamente al ritmo anual del Sol.'),
 ('Orientación inicial','RAAN 130,1326°; argumento de latitud 0°. LTAN 06:00, hora solar local del nodo ascendente.'),
 ('Apuntamiento','Zenit en el marco local orbital, LVLH. El instrumento no sigue al debris y gira respecto a las estrellas al recorrer la órbita.'),
 ('Propagación','Gravedad central y achatamiento terrestre J2, integrador RK4; paso 20 s e interpolación para resolver cruces. Altitud resultante: 442,46–450,00 km.')],[4.4,11])
 w.p('“450 km circular” describe el estado inicial de dos cuerpos. Al incluir J2 aparecen variaciones de altitud; no se fuerza una esfera de radio constante. Se eligió esta SSO porque dio más objetos detectables en el barrido exploratorio previo. No se ha demostrado que sea la órbita globalmente óptima.')
 w.p('Los pasos de propagación no son imágenes de la cámara. La trayectoria se interpola entre estados y se buscan las intersecciones con las caras del campo; así se pueden resolver cruces más cortos que 20 s. Los centros de exposición se prueban con separación de hasta 0,25 s y refinamiento local.')
 w.p('En cada cruce se comprueba: pertenencia al campo rectangular, iluminación solar, ausencia de ocultación terrestre, exclusión solar de 90°, fuente puntual y ausencia de saturación. Entre exposiciones candidatas se busca el mayor SNR válido. Los cruces parciales pueden aceptarse.')
 w.caption('Tabla',14,2,'Conteos de 24 horas, sin multiplicar por pesos de población.',above=True)
 w.table(['Etapa','Cruces','Objetos distintos'],[('Cruzan geométricamente el FoV','16.578','13.304'),('Tienen una exposición en el dominio válido','8.312','7.344'),('Además alcanzan SNR≥5','271','251')],[8,3.7,3.7])
 w.p('Un mismo objeto puede cruzar más de una vez: por eso hay más cruces que identificadores distintos. Estos resultados suponen sincronización ideal de la exposición. Cambiar la órbita sí modifica los encuentros, sus velocidades y su iluminación, aunque no cambie la ley física del instrumento.',size=10)
 #20
 w.page('15. Qué significa la magnitud aparente')
 w.p('La magnitud aparente resume el brillo que llega al observador. Su escala está invertida: un número mayor significa menos luz. Una diferencia de cinco magnitudes equivale a un factor cien en flujo. No es el tamaño del objeto: un fragmento grande lejos puede parecer más débil que uno pequeño cerca.')
 w.equation('mag')
 w.p('F es el flujo de fotones recibido en la banda y F₀ el flujo de referencia de magnitud cero en esa misma banda. Se usa una magnitud AB equivalente: el cero parte de 3.631 Jy de densidad de flujo espectral constante y se integra entre 450 y 750 nm. No es una medición fotométrica multibanda de un fragmento real.')
 w.fig(OS+'trace_nominal_sso450km_24h_apparent_magnitude_vs_range.png',15,1,'Magnitud aparente frente a distancia en los cruces válidos de 24 horas. Cada símbolo representa un cruce, no necesariamente un objeto distinto.',13.5)
 w.page('15.1. Brillo y velocidad transversal durante el día')
 w.p('La distancia, el tamaño y la iluminación cambian de un cruce a otro. Por eso la velocidad transversal no determina por sí sola el brillo. Esta vista ayuda a reconocer qué velocidades aparecen en los encuentros, manteniendo la clasificación por tamaños.')
 w.fig(OS+'trace_nominal_sso450km_24h_apparent_magnitude_vs_transverse_velocity.png',15,2,'Los mismos cruces, ahora frente a velocidad relativa transversal. La dispersión combina tamaño, distancia y fase; no se espera una relación única entre magnitud y velocidad.',14)
 w.p('Azul: 1–5 cm; verde: 5–10 cm; lila: 10 cm o más. Punto: primer cruce; cruz: segundo; triángulo: tercero y posteriores. No se representan los cruces excluidos del dominio válido. Estas dos figuras muestran brillo, sin frontera de detección.',size=10)
 w.p('Los símbolos de revisita cuentan cruces en orden temporal, no imágenes sucesivas de la misma exposición. Se selecciona un instante representativo por cruce: el de mayor SNR válido encontrado. Por tanto, la nube no es una serie de todos los fotogramas de un día.')
 #21
 w.page('16. Cómo leer las gráficas de detectabilidad')
 w.p('No hay una sola magnitud límite para todos los cruces: un objeto rápido deja una traza distinta y puede contribuir menos tiempo. Para comparar cada cruce con su propio umbral calculamos m₅, la magnitud que daría SNR=5 con esa traza, tiempo y ruido. Después restamos:')
 w.equation('margin')
 w.p('Por debajo de cero el cruce es suficientemente brillante; por encima, demasiado débil. Esta equivalencia se aplica dentro del dominio válido del modelo: no elimina los requisitos de iluminación, campo, fuente puntual y saturación.')
 w.fig(OS+'trace_nominal_sso450km_24h_magnitude_margin_vs_range.png',16,1,'Margen de magnitud frente a distancia. La línea roja discontinua es SNR=5; el sombreado rojo marca SNR<5. Cada cruce usa su propio límite m₅.',13.5)
 w.page('16.1. Detectabilidad y velocidad transversal')
 w.p('Esta vista pregunta si los cruces rápidos y lentos superan su propio límite de brillo. Un punto por encima de cero tiene SNR menor que 5, aunque pueda ser brillante en términos absolutos. La causa puede ser una señal útil breve o una traza que obliga a sumar ruido de más píxeles.')
 w.fig(OS+'trace_nominal_sso450km_24h_magnitude_margin_vs_transverse_velocity.png',16,2,'Margen frente a velocidad transversal. Se conservan los mismos colores por tamaño y símbolos de revisita. La velocidad es una de varias variables que determinan el resultado.',14)
 w.p('Las dos figuras corresponden a los 8.312 cruces válidos de 7.344 objetos. De ellos, 271 cruces de 251 objetos alcanzan SNR≥5. No se dibuja toda la población fuera del FoV ni se cuentan detecciones de objetos ocultos.',size=10)
 w.p('La mayor parte de la población pequeña es difícil de detectar en esta configuración. Aun así, el tamaño no basta para clasificar cada punto: importan simultáneamente distancia, fase, velocidad y tiempo de señal. Esta gráfica permite comparar esos resultados sin imponer un umbral de magnitud universal.')
 #22
 w.page('17. Qué hemos validado y qué queda por hacer')
 w.sub('17.1. Qué sabemos con este primer estudio')
 w.p('Hemos construido un banco de pruebas reproducible, con tamaños y órbitas definidos, y un modelo que relaciona luz reflejada, respuesta de la cámara, movimiento y ruido. Podemos estudiar cómo cambian los alcances al modificar fase, albedo, FoV, apertura y velocidad, y aplicar ese mismo modelo a encuentros concretos.')
 w.p('El modelo acepta tránsitos parciales si su SNR alcanza 5 y pasan los demás filtros. Distingue límite lejano por señal débil y límites cercanos por saturación o tamaño angular. La simulación nominal de un día produce 251 objetos distintos detectables bajo sus hipótesis; no es todavía una previsión garantizada de rendimiento en vuelo.')
 w.sub('17.2. Qué comprobaciones se han hecho')
 w.p('Los controles de población verifican identificadores, valores, ápsides y conversiones de estados orbitales. En una muestra de 5.000 objetos, reducir el paso dinámico de 20 a 10 s conserva los 1.708 cruces; la mayor diferencia de entrada es 5,865 ms. Reducir el muestreo fotométrico a 0,125 s conserva las clasificaciones del estudio diario. Son comprobaciones de estabilidad numérica, no comparación con observaciones reales.')
 w.sub('17.3. Hipótesis que más condicionan las conclusiones')
 for t in [
 'Población: solo tres familias donantes, soporte local incompleto y tamaños centimétricos no medidos directamente por esos catálogos. Conviene ampliar fuentes y comparar con/sin los 10.498 objetos extrapolados.',
 'Reflectancia: esfera difusa y albedo supuesto. Se omiten forma real, rotación irregular y destellos especulares; el brillo real puede cambiar mucho.',
 'Instrumento: PSF gaussiana constante, QE y transmisión simplificadas por banda, fondo uniforme y extracción ideal. Faltan caracterización fuera de eje, luz terrestre y límite de ADC.',
 'Geometría: Sol aproximado, sombra terrestre cilíndrica y dinámica central+J2. Se omiten arrastre, terceros cuerpos y otros términos de mayor precisión.',
 'Operación: se elige el mejor instante de exposición, sin imponer cadencia y tiempos muertos. SNR≥5 no especifica por sí solo falsas alarmas, asociación de objetos ni precisión de seguimiento.'
 ]:w.p('• '+t,size=10)
 w.sub('17.4. Siguiente paso recomendado')
 w.p('Simular una cadencia real y repetir el estudio con las poblaciones alternativas y distintos albedos, fondos y PSF. Comparar objetos únicos detectados, revisitas y calidad de medida. Después se podrá enlazar esta validación óptica y radiométrica preliminar con un análisis completo de viabilidad de misión.')
 w.p('Trazabilidad: fuentes y gráficas conservan sus referencias [1]–[6] (sección 2). El archivo fuentes.json acompaña al Word; verificacion.json registra la revisión documental. No se ha cambiado la población nominal ni repetido las simulaciones para redactar esta versión.',size=9)
 update=OxmlElement('w:updateFields');update.set(qn('w:val'),'true');w.doc.settings.element.append(update)
 final=REPORT/'TRACE_Informe_Poblacion_Validacion_Optica.docx';w.doc.save(final)
 previous=json.loads((REPORT/'fuentes.json').read_text())
 paths={i['path'] for i in previous['inputs'] if not i['path'].startswith('outputs/')};paths.update(w.figure_inputs)
 specification=list((ROOT/'docs').rglob('*Validation_Specification*'))
 paths.update(str(p.relative_to(ROOT)) for p in specification if p.is_file())
 manifest={'document':final.name,'revision':'Guía para principiantes; sustituye el informe breve',
 'template':str(base.TEMPLATE.relative_to(ROOT)),'equations_editable_omml':len(base.EQUATIONS),
 'figures':[{'path':p,'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest()} for p in w.figure_inputs],
 'inputs':[{'path':p,'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest()} for p in sorted(paths)],
 'scope':'Resultados nominales archivados; sin regenerar población ni simulaciones. Figuras existentes reutilizadas sin cambiar sus datos.',
 'entrypoint':'scripts/build_trace_intro_report.py'}
 (REPORT/'fuentes.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 print(final);print(f'{len(w.figure_inputs)} figuras; {len(base.EQUATIONS)} ecuaciones')

if __name__=='__main__':main()
