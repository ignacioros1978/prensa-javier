# Prensa de Javier — instrucciones de mantenimiento

Este archivo es para Claude. Si estás leyendo esto desde una cuenta nueva de Claude, aquí tienes todo lo necesario para seguir manteniendo la app.

## Qué es

- Web estática en GitHub Pages: https://ignacioros1978.github.io/prensa-javier/
- La usa Javier, un señor mayor casi ciego por una retinosis pigmentaria, en su tablet Android (Chrome, con icono en la pantalla de inicio).
- La web le lee en voz alta titulares y resúmenes (Web Speech API). El botón «Hablar» abre el micrófono y entiende órdenes por voz en español.
- A Javier se le habla de **tú**, nunca de «usted» ni «don».
- `familia.html` es una versión con otro diseño para su hijo Ignacio, con los mismos datos.

## Archivos

- `index.html`: la app de Javier, en negro y amarillo, con letra grande. Contiene el catálogo de periódicos, con alias para la voz, y el intérprete de órdenes de voz (`handle()`).
- `familia.html`: la versión familiar.
- `noticias.json`: **el único archivo que cambia cada día**. Lo escriben las tareas programadas.
- `manifest.json` e `icono-*.png`: el icono de la pantalla de inicio.

## Tareas programadas (crear con modelo Sonnet)

Hay dos tareas, con zona horaria Europe/Madrid:

1. **«Noticias del día para la Prensa de Javier (lun-jue, 6:50 y 15:50)»**
   - cron: `CRON_TZ=Europe/Madrid 50 6,15 * * 1-4`
   - Usa el PROMPT A de abajo.
2. **«Noticias del fin de semana para la Prensa de Javier (vie-dom, 6:50)»**
   - cron: `CRON_TZ=Europe/Madrid 50 6 * * 5,6,0`
   - Usa el PROMPT B de abajo.

Importante:
- Las tareas programadas no tienen la herramienta add_repo. Los prompts ya lo tienen en cuenta: clonan con git y hacen push directamente (comprobado: funciona también en cuentas nuevas).
- **Permisos de WebFetch (aprendido el 17 de octubre de 2026 al traspasar la app a otra cuenta):** en una cuenta nueva, las tareas programadas NO pueden abrir con WebFetch las direcciones escritas en sus propias instrucciones (error PROVENANCE_REQUIRED, y nadie está para aprobarlo). La tarea termina a los pocos minutos sin guardar nada y aun así figura como «completada». Por eso los prompts entran a cada periódico a través de WebSearch: las URLs que devuelve una búsqueda sí se pueden abrir.
- Los prompts piden además no usar skills, subagentes ni procesos en segundo plano: en una tarea desatendida, lo que no esté terminado cuando acaba la respuesta se pierde.
- Para probar una tarea, lánzala a mano y comprueba que noticias.json cambia en GitHub (último commit «Noticias del …»). Que la ejecución diga «completada» no basta.

### PROMPT A (lunes a jueves)

```
Prepara las noticias de hoy para la web «Prensa de Javier» (repositorio de GitHub ignacioros1978/prensa-javier, publicada con GitHub Pages). La usa Javier, un señor mayor casi ciego por una retinosis pigmentaria: la web le LEE EN VOZ ALTA los titulares y resúmenes, así que todo debe sonar natural al oído. Trabaja sin preguntar nada; nadie está mirando.

MUY IMPORTANTE: esta es una sesión desatendida que se cierra en cuanto termines tu respuesta. Haz TÚ MISMO cada paso, uno detrás de otro. NO uses skills, subagentes (Agent) ni nada en segundo plano. No termines hasta haber hecho el push del paso 5.

PERMISOS DE WEBFETCH: en esta sesión WebFetch rechaza (PROVENANCE_REQUIRED) las URLs que no hayan salido antes de una búsqueda o de otra página ya abierta, y nadie puede aprobarlas. Por eso, para CADA periódico: primero haz WebSearch (mode standard) con allowed_domains = su dominio (por ejemplo "portada noticias hoy" con allowed_domains ["libertaddigital.com"]) y abre con WebFetch la portada o las URLs de artículos que DEVUELVA esa búsqueda. Las URLs de artículos que aparezcan en una página ya abierta con WebFetch también se pueden abrir. Si una URL se rechaza, busca otra que haya salido en los resultados; no pidas permiso.

1. Para cada periódico, elige las 4 noticias más destacadas de hoy (salta opinión, pasatiempos, tiempo, precios de gasolina, publicidad y directos sin contenido):
   - Libertad Digital (id "ld") dominio libertaddigital.com
   - El Español (id "ee") dominio elespanol.com
   - El Debate (id "ed") dominio eldebate.com
   - The Objective (id "to") dominio theobjective.com
   - OKDiario (id "ok") dominio okdiario.com (quédate con noticias cuya URL contenga "/espana/")
   - elDiario.es (id "edi") dominio eldiario.es
   ABC, El Mundo, La Razón y El Confidencial están bloqueados para nuestras herramientas: NO intentes rodearlo con curl, cachés ni espejos. Si alguno de los seis de arriba falla, omítelo ese día.
2. Abre cada artículo elegido con WebFetch y pide los hechos con detalle (qué, quién, cuándo, cifras, contexto, reacciones).
3. Escribe para cada noticia, con TUS PROPIAS PALABRAS (nunca copies frases del artículo; como mucho una cita breve de menos de 15 palabras si es imprescindible):
   - "titular": claro y corto, entendible al oírlo.
   - "resumen": 110-170 palabras, frases cortas, tono neutro, atribuyendo al periódico o a las fuentes las afirmaciones polémicas ("según El Debate…"). Para el oído: nada de siglas raras sin explicar, fechas como "29 de noviembre" (no "29-N"), sin paréntesis ni viñetas, números romanos escritos con letra. Solo hechos del artículo; no inventes nada.
   - "url": la del artículo. "id": id del periódico + número (ej. "ee1").
4. Elige 8-10 noticias para "portada": las más importantes del día mezclando periódicos, sin repetir el mismo hecho, empezando por la más importante.
5. Guarda en GitHub (el repositorio ya está autorizado para esta tarea; NO busques ni uses ninguna herramienta add_repo, no existe aquí):
   a. Con Bash: git clone --depth 1 https://github.com/ignacioros1978/prensa-javier /tmp/pj
   b. Sustituye SOLO el archivo /tmp/pj/noticias.json por el nuevo, con esta estructura exacta (UTF-8, JSON válido):
{"fecha":"AAAA-MM-DD","fechaTexto":"lunes 19 de octubre","actualizado":"<ISO con zona +01:00/+02:00, hora de Madrid>","portada":["to3","ee2",...],"diarios":[{"id":"ld","nombre":"Libertad Digital","noticias":[{"id":"ld1","titular":"…","resumen":"…","url":"…"}]},{"id":"ee","nombre":"El Español",…},{"id":"ed","nombre":"El Debate",…},{"id":"to","nombre":"The Objective",…},{"id":"ok","nombre":"OKDiario",…},{"id":"edi","nombre":"elDiario.es",…}]}
      FECHA Y HORA: justo antes de escribir el archivo, ejecuta en Bash TZ=Europe/Madrid date -Iseconds y usa esa salida exacta para "actualizado", para "fecha" y "fechaTexto", y para la hora del mensaje del commit. No calcules ni inventes la hora.
      Mantén exactamente esos ids y nombres de periódico. Todos los ids de "portada" deben existir en "diarios". Valida el JSON con python3 -m json.tool antes de guardar.
   c. No toques index.html, familia.html ni ningún otro archivo. En /tmp/pj: git add noticias.json; git -c user.name=Claude -c user.email=noreply@anthropic.com commit -m "Noticias del <fecha> <hora>"; git push origin HEAD:main. Si el push falla por cambios remotos, haz git pull --rebase y vuelve a empujar una vez.
6. Termina con una línea: cuántas noticias guardaste, si algún periódico falló y si el push funcionó.
```

### PROMPT B (viernes a domingo)

Es igual que el PROMPT A, con estos cambios:

- Al final del primer párrafo se añade: «Esta es la ÚNICA actualización del día (viernes, sábado y domingo solo hay una, por la mañana).»
- Se añade un párrafo después del de PERMISOS DE WEBFETCH: «NÚMERO DE NOTICIAS POR PERIÓDICO: los viernes, 4; los sábados y domingos, 3. Mira la fecha de hoy (hora de Madrid) para saber cuál aplica.»
- Paso 1: «elige las noticias más destacadas de hoy (4 o 3 según el día; …)».
- Paso 4: «Elige para "portada" las más importantes del día mezclando periódicos (8-10 los viernes, 7-9 los sábados y domingos), …».
- En el ejemplo del JSON: "fechaTexto":"domingo 18 de octubre".

## Cómo hacer cambios

- Para cambiar el diseño o las órdenes de voz, edita `index.html` (o `familia.html`) y haz push a `main`. GitHub Pages publica en uno o dos minutos.
- No cambies los ids de periódico ("ld", "ee", "ed", "to", "ok", "edi") sin cambiar también el catálogo de `index.html` y `familia.html`.
- Prueba siempre en la tablet de Javier con Chrome. El micrófono solo funciona abriendo la web en Chrome, no dentro de la app de Claude.

---

# App «Viajes» (carpeta `viajes/`)

Web de ofertas de viaje para Ignacio y Rosa: cada lunes, la mejor escapada en pareja y el mejor viaje en familia (2 adultos y 3 hijos de 14, 11 y 4 años) a una ciudad europea, saliendo de Sevilla, Málaga o Jerez.

- Web: https://ignacioros1978.github.io/prensa-javier/viajes/ (enlazada desde el Portal de Casa con la tarjeta «Viajes»).
- `viajes/index.html`: la página. Solo lee `ofertas.json`.
- `viajes/ofertas.json`: **el único archivo que cambia**. Lo escribe la tarea programada.
- `viajes/criterios.json`: qué buscar (orígenes, viajeros, noches, presupuesto, calidad mínima, fechas ocupadas, festivos escolares, destinos). Para cambiar la búsqueda, cambia este archivo; la tarea lo lee cada vez. **Actualiza `fechasOcupadas` y `festivosEscolaresAndalucia`** cuando haya viajes nuevos o empiece otro curso.
- `viajes/PROMPT.md`: el prompt exacto de la tarea.

## Tarea programada

- Nombre: «Ofertas de viaje de la semana (lunes, 7:47)»
- cron: `CRON_TZ=Europe/Madrid 47 7 * * 1`
- Avisos: correo y notificación al móvil (el mensaje final de la tarea es el resumen).
- Conectores que necesita la cuenta: **lastminute.com** (paquetes vuelo + hotel, la fuente principal), **eDreams** (vuelos) y **Booking.com** (alojamiento). Al crear la tarea se adjuntan los conectores que tenga la cuenta; si falta alguno, conéctalo antes.
- lastminute solo admite niños de hasta 11 años: la hija de 14 cuenta como adulto (adults 3, ch_ages "11,4").
- Para probarla: lánzala a mano y comprueba que hay un commit nuevo «Ofertas de viaje del …» y que `viajes/ofertas.json` tiene "estado":"ok".

## Depósitos (carpeta depositos/)
- Página: https://ignacioros1978.github.io/prensa-javier/depositos/ · se abre desde la Cartera (Liquidez › Reserva estratégica › «Top 5 del mercado»).
- La Cartera le pasa el mejor depósito vivo en la dirección: ?mi=<TAE>&ent=<entidad>&nom=<nombre>&vence=<AAAA-MM-DD>.
- top5.json lo escribe la tarea programada «Top 5 depósitos (lunes y jueves)». Sus instrucciones están en depositos/PROMPT.md.
