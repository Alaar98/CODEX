---
name: documentos-tecnicos-latex
description: "Redactar, maquetar o revisar artículos científicos, informes de ingeniería y memorias técnicas en LaTeX (.tex, PDF compilado, Overleaf), con el estilo personal de los informes de sistemas espaciales del usuario. Aplicar cuando el encargo de un documento técnico pida LaTeX, TeX, Overleaf o esta skill."
---

# Documentos técnicos en LaTeX

1. Leer [la guía de estilo](references/estilo.md). Recoger propósito, idioma, datos, gráficas disponibles y requisitos del encargo. Aplicar la maquetación indicada por el usuario para el documento actual si modifica un valor por defecto.
2. Partir de `assets/articulo.tex` y copiar el logo adjunto al proyecto. Adaptar el idioma de Babel, la portada, las secciones, las referencias y las unidades al encargo. Para un informe largo, incluir índice de contenidos y, según el número de elementos, índices de figuras y tablas.
3. Usar ecuaciones LaTeX nativas, referencias cruzadas con etiquetas semánticas y bibliografía trazable si hay fuentes. Usar TikZ o dibujos vectoriales exportados a PDF para geometrías y detectores. Comprobar que las figuras y las ecuaciones comparten símbolos y convenciones. Usar tablas editables en LaTeX y el estilo cromático de la guía. Para tablas extensas, repetir la cabecera con longtable.
4. Compilar hasta resolver las referencias, por ejemplo con `latexmk -pdf -interaction=nonstopmode -halt-on-error articulo.tex`. Revisar el registro y las páginas renderizadas. Verificar en portada y páginas interiores que el logo se muestra y no se solapa. Revisar cortes, fórmulas, legibilidad, tablas, unidades y numeración.
5. Entregar el PDF compilado y el proyecto fuente reproducible con sus archivos necesarios y rutas relativas. Si la compilación está bloqueada, identificar la dependencia o el error pendiente y distinguir el fuente del PDF que se haya podido verificar.
