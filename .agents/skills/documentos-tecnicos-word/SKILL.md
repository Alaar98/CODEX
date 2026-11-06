---
name: documentos-tecnicos-word
description: "Redactar, maquetar o revisar artículos científicos, informes de ingeniería y memorias técnicas en Microsoft Word (.docx), con una presentación de artículo LaTeX y el estilo personal de los informes de sistemas espaciales del usuario. Aplicar cuando el encargo de un documento técnico pida Word, DOCX o esta skill."
---

# Documentos técnicos en Word

1. Leer [la guía de estilo](references/estilo.md). Recoger propósito, idioma, datos, gráficas disponibles y requisitos del encargo. Aplicar la maquetación indicada por el usuario para el documento actual si modifica un valor por defecto.
2. Usar `assets/articulo-referencia.docx` como base de maquetación. Mantener estilos de título, encabezados jerárquicos, texto, pies y tablas. Para documentos largos, incluir portada e índices automáticos cuando proceda. Conservar el encabezado con el logo original en todas las secciones, incluida la primera página y las páginas pares. Si se introduce una sección independiente, comprobar que conserva el encabezado.
3. Construir tablas nativas y editables con los colores y reglas de la guía. Usar campos de Word para numeración y referencias cruzadas cuando sea viable. Insertar ecuaciones nativas editables (OMML). Una vía es convertir fórmulas LaTeX desde Markdown con Pandoc y la opción `--reference-doc`, y aplicar estilos de tablas, campos y ajustes de encabezado al resultado. Para los esquemas, generar un original vectorial con geometría calculada y usar una inserción compatible con Word y el visor de destino.
4. Renderizar el documento y revisar visualmente todas las páginas. Comprobar el logo, saltos, estilos, continuidad de tablas, pies, referencias, numeración y ecuaciones. Validar en el archivo DOCX que se mantienen tablas y ecuaciones editables. Entregar el DOCX. Adjuntar el PDF si se solicita.
