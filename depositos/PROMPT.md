Revisión de los mejores depósitos a plazo del mercado español para la página «Top 5 depósitos» de la Cartera de Ignacio (repositorio de GitHub ignacioros1978/prensa-javier, carpeta depositos/, publicada en https://ignacioros1978.github.io/prensa-javier/depositos/). Trabaja sin preguntar nada; nadie está mirando. No envíes mensajes a nadie.

MUY IMPORTANTE: sesión desatendida que se cierra en cuanto termines tu respuesta. Haz TÚ MISMO cada paso, uno detrás de otro. NO uses skills, subagentes (Agent) ni nada en segundo plano. No termines hasta haber hecho el push del paso 5. El repositorio ya está autorizado para esta tarea: NO busques ni uses ninguna herramienta add_repo.

PERMISOS DE WEBFETCH: WebFetch rechaza (PROVENANCE_REQUIRED) las URLs que no hayan salido antes en una búsqueda o en otra página ya abierta, y nadie puede aprobarlas. Abre solo URLs que hayan salido en los resultados de WebSearch o en páginas ya abiertas. Si una se rechaza, prueba otra; no pidas permiso.

1. PREPARAR
   a. Con Bash: git clone --depth 1 https://github.com/ignacioros1978/prensa-javier /tmp/pj
   b. Lee /tmp/pj/depositos/top5.json (el ranking anterior).
   c. Ejecuta TZ=Europe/Madrid date -Iseconds para saber la fecha y hora reales. No la calcules ni la inventes.

2. BUSCAR (como máximo unas 14 llamadas entre WebSearch y WebFetch)
   - WebSearch (mode standard) del tipo «mejores depósitos a plazo fijo» + mes y año actuales, con allowed_domains ["helpmycash.com","rankia.com","iahorro.com","finanzarel.com","bankimia.com"], y abre con WebFetch 2 o 3 de los rankings más recientes que salgan.
   - Para los candidatos con TAE más alta, comprueba la oferta en la web del propio banco si sale en una búsqueda (WebSearch con allowed_domains = el dominio del banco). Si la web del banco da otra TAE o la oferta ya no existe, manda la web del banco.
   - Qué cuenta:
     · Solo depósitos a plazo fijo para particulares, en euros, comercializados en España.
     · Con garantía de un fondo de garantía de depósitos de un país de la Unión Europea (España, Alemania, Francia, Países Bajos, Lituania, Portugal, Italia…), hasta 100.000 € por titular.
     · Plazo entre 3 y 36 meses.
     · NO cuentan: cuentas remuneradas, depósitos estructurados o combinados con fondos, ofertas con regalo en vez de intereses, ni bancos de fuera de la UE.
     · Si una oferta exige condiciones (ser cliente nuevo, domiciliar la nómina, importe máximo pequeño…), puede entrar, pero escríbelo en "condiciones".
   - NO INVENTES NADA: cada TAE, plazo, importe y condición tiene que salir de una página que hayas leído hoy. Si dos fuentes no coinciden, usa la de la web del banco o, si no la tienes, la más reciente, y dilo en "nota".

3. ELEGIR los 5 de mayor TAE, de bancos distintos (si un banco tiene varios plazos, quédate con su mejor TAE y menciona los otros plazos en "nota" si es útil). Ante una TAE parecida (menos de 0,05 puntos de diferencia), primero el que no tenga condiciones.

4. ESCRIBIR /tmp/pj/depositos/top5.json (UTF-8, JSON válido) con esta estructura exacta:
{"actualizado":"<salida exacta de TZ=Europe/Madrid date -Iseconds>","fechaTexto":"lunes 19 de octubre","estado":"ok",
 "top":[{"banco":"Nombre del banco","producto":"Depósito … (nombre comercial)","tae":2.85,"tin":2.81,"plazoMeses":12,"plazoTexto":"12 meses","minimo":1000,"maximo":100000,"condiciones":"Sin condiciones","garantia":"Fondo de Garantía de Depósitos de España (100.000 €)","pais":"España","url":"https://… (la página de la oferta, mejor en la web del banco)","fuente":"web del banco o comparador donde lo comprobaste","nota":""}],
 "anteriores":[{"fechaTexto":"jueves 15 de octubre","mejor":{"banco":"…","tae":2.9}}],
 "fuentes":["helpmycash.com","web de Banco X"],
 "nota":""}
   - tae, tin, minimo, maximo y plazoMeses son números (sin texto ni %). Si no conoces tin, minimo o maximo, no pongas ese campo.
   - "anteriores": si el top5.json anterior tenía "estado":"ok" y top no vacío, pon al principio {"fechaTexto": su fechaTexto, "mejor": {"banco","tae"} de su primer depósito}, seguido de sus "anteriores"; guarda como máximo 8. Si tenía "estado":"pendiente", copia sus "anteriores" si los tiene.
   - Si no encuentras al menos un depósito fiable, deja "estado":"ok", "top":[] y explica en "nota" por qué.
   - Valida con python3 -m json.tool antes de guardar.

5. GUARDAR EN GITHUB. No toques ningún otro archivo. En /tmp/pj: git add depositos/top5.json; git -c user.name=Claude -c user.email=noreply@anthropic.com commit -m "Top 5 depósitos del <fecha>"; git push origin HEAD:main. Si el push falla por cambios remotos, haz git pull --rebase y vuelve a empujar una vez.

6. MENSAJE FINAL (corto, una línea por depósito): «<posición>. <banco>: <TAE> % TAE a <plazo>». Si algo falló, añádelo en una línea al final.
