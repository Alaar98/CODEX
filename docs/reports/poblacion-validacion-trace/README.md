# TRACE — guía de población y validación óptica y radiométrica

[Descargar el informe Word](TRACE_Informe_Poblacion_Validacion_Optica.docx).

Revisión para lectores principiantes: explica las fuentes, la construcción de
la población y cada variable del instrumento antes de introducir las ecuaciones.
Incluye 22 figuras existentes del proyecto, con guías de lectura, 15 ecuaciones
OMML editables y siete tablas de datos nativas. Sustituye al informe breve.
Se retira el esquema temporal; el tránsito parcial se explica mediante un
intervalo de exposición, su intersección con el cruce y un ejemplo numérico.

El encabezado conserva el logo y añade «TRACE · AEK» a la derecha. El pie
contiene campos Word PAGE / NUMPAGES. Tras cada tabla se deja un párrafo de
separación. Las ecuaciones usan notación simplificada con símbolos definidos;
la antigua fórmula acumulativa de subíndices encadenados se sustituye por una
explicación del muestreo de tamaños y ecuaciones sencillas del muestreo por capas.

## Reproducción

Requiere Python con los paquetes de `requirements.txt` de esta carpeta y Pandoc.
Desde la raíz del repositorio:

```bash
python scripts/build_trace_intro_report.py
```

El comando anterior `python scripts/build_trace_word_report.py` también genera
la revisión actual. Este archivo conserva las utilidades compartidas de Word;
no restaura la versión anterior. Ningún comando regenera los resultados físicos.

`ecuaciones.md` contiene las fórmulas LaTeX convertidas a OMML. `fuentes.json`
registra rutas y SHA-256 de documentos, datos y PNG utilizados. Las imágenes
se insertan desde los originales existentes en `outputs/`; no se alteran los
CSV ni las gráficas de la población o de los estudios.

## Revisión de la maquetación

```bash
mkdir -p /tmp/trace-report-review
soffice --headless --convert-to pdf --outdir /tmp/trace-report-review docs/reports/poblacion-validacion-trace/TRACE_Informe_Poblacion_Validacion_Optica.docx
```

El PDF es un soporte temporal de revisión. El entregable principal es el DOCX.
`verificacion.json` registra la comprobación del documento y de todas las
páginas renderizadas, incluido encabezado, paginación, fórmulas y espacios.
