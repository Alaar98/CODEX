# Estilo de los informes técnicos

## Voz y estructura

Patrones extraídos de los trabajos de estructuras, potencia y ESATAN-TMS y del Caso de Estudio 3 (análisis de misión y térmico en inglés). Redactar en el idioma solicitado o, si no se indica, en el del encargo. Conservar el nivel técnico y la progresión de los informes. En inglés mantener la misma secuencia didáctica con giros naturales, sin traducir literalmente.

- Dar primero el propósito físico, el requisito o la decisión de diseño. Explicar el fenómeno antes de introducir el cálculo. Mantener el tono de un profesor que guía a lectores técnicamente preparados que ven el concepto por primera vez.
- Organizar por introducción, metodología, resultados, discusión y conclusiones cuando corresponda. Emplear secciones y subsecciones numeradas con títulos concretos. En informes largos usar portada e índices pertinentes. En un artículo corto integrar título, autoría si se facilita y resumen conciso en la primera página.
- Adoptar giros naturales como «Para ello, se calcula…» o «En la Figura 2.3 se muestra…» cuando ayudan a enlazar propósito y método. Interpretar después qué cambia y por qué. En el Caso 3 se explica, por ejemplo, cómo el tiempo máximo sin contacto pasa de ser un resultado de simulación a dimensionar la memoria de a bordo.
- Introducir símbolos, subíndices, unidades, referencias y convenciones de signo al primer uso. Numerar las ecuaciones citadas y explicar el significado físico y las consecuencias del modelo. Documentar hipótesis, condiciones iniciales y de contorno, simplificaciones, rango de validez y limitaciones relevantes. Separar requisitos, entradas, hipótesis, resultados e interpretación.
- Mantener trazabilidad de valores y fuentes. Diferenciar datos medidos, resultados de simulación y estimaciones. Si falta un dato, declarar la carencia o documentar una hipótesis claramente identificada cuando permita avanzar.

## Tablas y maquetación

- Usar una columna, tipografía serif, fondo blanco y jerarquía sobria. Colocar únicamente el logo de Thales Alenia Space arriba a la izquierda en todas las páginas salvo instrucción expresa. Usar el PNG original, mantener su proporción y reservar espacio para el encabezado. Centrar la numeración de página en el pie.
- Centrar la tabla y el título numerado encima. Adoptar numeración por sección (Tabla 2.5, Figure 2.3), encabezado azul claro, reglas finas y agrupación lógica. El Caso 3 combina una cabecera de grupo azul con la columna de parámetros en azul muy pálido y negrita en tablas de parámetro y valor. En tablas de resultados, aplicar el azul a la cabecera y dejar claro el fondo del cuerpo. Adaptar la anchura de la primera columna a los nombres largos.
- Colocar las unidades en encabezados o junto al valor cuando varíen por fila. Alinear cantidades comparables y ajustar cifras significativas según la precisión. Repetir cabeceras cuando una tabla se extienda a otra página. Explicar siglas, supuestos o procedencia al pie si aportan contexto.

## Gráficas y esquemas

- Revisar las gráficas y datos disponibles en el trabajo o el chat. Reutilizar las gráficas pertinentes ya generadas y seleccionar las que sustenten resultados, decisiones o verificaciones. Generar gráficas nuevas a partir de datos trazables si aportan información. Usar etiquetas con unidades, leyendas legibles, rangos comparables y pies descriptivos debajo. Citar y explicar la figura en el punto donde se usa.
- Crear un esquema técnico para ángulos, geometrías y variables espaciales del detector. Abrir los PNG de referencia según corresponda: `assets/angulo-fase.png`, `assets/iluminacion-oclusion.png`, `assets/campo-vision.png` y `assets/geometria-observacion.png`. Reproducir su lenguaje gráfico con geometría simple sobre blanco, ejes negros, vectores de posición o rayos naranjas, arcos verdes para ángulos, velocidades moradas, Tierra azul, detector gris y trazos discontinuos para construcciones. Distinguir también por rótulos y estilo de línea.
- Construir en vector mediante coordenadas y símbolos verificables. Indicar origen, ejes, plano, líneas de visión, normal, campo de visión y sentido de medida cuando correspondan. Mantener vértice, sentido y símbolos coherentes con las ecuaciones. Las referencias guían la estética. Recalcular la geometría y comprobar las convenciones en cada caso.
- Para un ejemplo de fase, marcar el vértice en el objeto y medir entre las direcciones objeto→Sol y objeto→observador. Si el vector de línea de visión del modelo apunta en la dirección contraria, distinguirlo en texto, ecuación y dibujo. Para variables del detector, dibujar la vista o el corte pertinente y marcar, según el modelo, eje óptico, plano focal, origen, dimensiones y coordenadas.
