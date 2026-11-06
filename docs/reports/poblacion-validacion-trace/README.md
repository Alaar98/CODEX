# TRACE — población sintética y validación óptica y radiométrica

Documento principal: [TRACE_Informe_Poblacion_Validacion_Optica.docx](TRACE_Informe_Poblacion_Validacion_Optica.docx).

Informe breve en español: población híbrida ESA–CelesTrak, geometría y
tránsitos parciales, presupuesto radiométrico, ventanas ópticas y cruces de
24 horas. Incluye ecuaciones nativas OMML, tablas editables y figuras.

## Reproducir desde la raíz del repositorio

Requiere Python con los paquetes de `requirements.txt` de esta carpeta y
Pandoc disponible en PATH. Usa la plantilla Word de la skill local, la
población nominal y los resultados archivados; no vuelve a simularlos.

```bash
python scripts/build_trace_word_report.py
```

`ecuaciones.md` contiene el fuente LaTeX de las ecuaciones; Pandoc las
convierte a ecuaciones editables de Word. `assets/` contiene las ediciones
compactas de las figuras y el original SVG del esquema geométrico.
`fuentes.json` registra las entradas y sus SHA-256.

## Revisar el documento renderizado

Con LibreOffice disponible:

```bash
mkdir -p /tmp/trace-report-review
soffice --headless --convert-to pdf --outdir /tmp/trace-report-review docs/reports/poblacion-validacion-trace/TRACE_Informe_Poblacion_Validacion_Optica.docx
```

El control registrado en `verificacion.json` corresponde al DOCX entregado:
se revisan las páginas renderizadas, ecuaciones, logo, numeración, tablas,
figuras y trazabilidad. El PDF se usa como soporte de revisión; el documento
editable principal es Word.

Las gráficas se redibujan a tamaño de informe a partir de los CSV/JSON
nominales archivados. La figura de ventana óptica se limita a diámetros de
1 a 100 cm para evitar representar los máximos censurados de otros tamaños
como si fueran raíces calculadas. Los conteos de encuentros son sin pesos.
