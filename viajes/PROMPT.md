Barrido de ofertas de viaje (lunes y jueves) para la app «Viajes» de Ignacio (repositorio de GitHub ignacioros1978/prensa-javier, carpeta viajes/, publicada con GitHub Pages en https://ignacioros1978.github.io/prensa-javier/viajes/). Responde en español y tutea a Ignacio. Trabaja sin preguntar nada; nadie está mirando.

MUY IMPORTANTE: esta es una sesión desatendida que se cierra en cuanto termines tu respuesta. Haz TÚ MISMO cada paso, uno detrás de otro. NO uses skills, subagentes (Agent) ni nada en segundo plano. No termines hasta haber hecho el push del paso 6. El repositorio ya está autorizado para esta tarea: NO busques ni uses ninguna herramienta add_repo.

PERMISOS DE WEBFETCH: WebFetch rechaza (PROVENANCE_REQUIRED) las URLs que no hayan salido antes en una búsqueda o en otra página ya abierta, y nadie puede aprobarlas. Abre solo URLs que hayan salido en los resultados de WebSearch o en páginas ya abiertas. Si una se rechaza, prueba otra; no pidas permiso.

1. PREPARAR
   a. Con Bash: git clone --depth 1 https://github.com/ignacioros1978/prensa-javier /tmp/pj
   b. Lee /tmp/pj/viajes/criterios.json (lo que hay que buscar) y /tmp/pj/viajes/ofertas.json (el resultado del barrido anterior).
   c. Ejecuta TZ=Europe/Madrid date -Iseconds para saber la fecha y hora reales de hoy. No la calcules ni la inventes.

2. HERRAMIENTAS. Cárgalas con ToolSearch en una sola llamada:
   "select:mcp__lastminute_com__search_flight_and_hotel_package,mcp__lastminute_com__select_hotel_options,mcp__lastminute_com__generate_booking_link,mcp__eDreams__search_flights,mcp__Booking_com__accommodations_search"
   Si alguna no aparece, sigue sin ella y anótala con estado "no disponible" en "fuentes".

3. BUSCAR (como máximo unas 40 búsquedas en total entre todas las herramientas)
   - Fechas: solo salidas dentro de "ventanaSalida" contando desde hoy, y nunca solapadas con "fechasOcupadas".
     · Pareja: elige 3 tandas de fechas de 3 o 4 noches (por ejemplo jueves-domingo o lunes-jueves).
     · Familia: elige los 3 o 4 próximos fines de semana de viernes a domingo dentro de la ventana, y además cualquier tramo de "festivosEscolaresAndalucia" que caiga dentro (de 2 a 4 noches). Nunca días de colegio entre semana.
   - Paquetes vuelo + hotel con lastminute (la fuente principal): origin SVQ y AGP (XRY si tiene vuelos), destination entre "destinosCandidatos", lang "es", sort "price", max_results 5. Pareja: adults "2", accommodation_type "1,14". Familia: adults "3", ch_ages "11,4", accommodation_type "3,14,1" (si no hay resultados, prueba adults "2;1" y ch_ages "11,4;"). Haz unas 14 búsquedas por perfil, variando destino, origen y fechas; empieza por los destinos que suelen ser más baratos (Lisboa, Oporto, Roma, Milán, Nápoles, Bolonia, Malta, Bruselas, París) y prueba también 2 o 3 que no hayas mirado la semana pasada.
   - Descarta cualquier resultado que no cumpla "calidadMinima": rating por debajo de 75 o con menos de 50 opiniones (rating 0 o reviews 0 cuenta como sin valorar: descártalo), a más de 4 km del centro, o con nombre de camping, hostel, albergue o similar.
   - Comprobación cruzada: para los 2 o 3 destinos más baratos de cada perfil, mira con eDreams (search_flights, ida y vuelta, mismos viajeros: pareja adults 2; familia adults 3 children 2) y Booking (accommodations_search) si vuelo y alojamiento por separado salen más baratos que el paquete con la misma calidad. Si sale más barato por separado, esa combinación también vale como candidata (tipo "Vuelo + hotel por separado").
   - Opcional, si te sobran búsquedas: WebSearch (mode standard) "chollo vuelo hotel desde Sevilla" o "desde Málaga" con allowed_domains ["viajerospiratas.es","chollometro.com"]. Solo úsalo si el precio y las fechas se pueden comprobar en la propia página y cumple los criterios.

4. ELEGIR
   - Para cada perfil, la oferta más barata en precio TOTAL que cumpla todos los criterios. En caso de precio parecido (menos de 40 € de diferencia), prefiere vuelo directo y mejor nota.
   - Enlace: si es de lastminute, llama a select_hotel_options (search_id, hotel_internal_id, date_from, date_to) y después a generate_booking_link con el pricing_id y el rate_id de la habitación más barata apta para todos; usa la URL que devuelva y el precio total que confirme. Si falla, usa como url https://www.lastminute.com/ y dilo en "porQue". Para eDreams o Booking usa la URL que devuelva la herramienta si la hay.
   - Añade hasta 2 "alternativas" por perfil, de destinos distintos al elegido.
   - NO INVENTES NADA: cada dato (precio, compañía, horarios, hotel, nota, distancia) tiene que salir de un resultado de herramienta. Si no conoces un campo, no lo pongas. La nota de lastminute viene sobre 100: escríbela sobre 10 con coma (rating 84 → "8,4").

5. ESCRIBIR /tmp/pj/viajes/ofertas.json (UTF-8, JSON válido) con esta estructura exacta:
{"actualizado":"<salida exacta de TZ=Europe/Madrid date -Iseconds>","semanaTexto":"<día de la semana y fecha de hoy, p. ej. jueves 22 de octubre>","estado":"ok",
 "pareja":{"destino":"Roma","pais":"Italia","origen":"Sevilla","fechaIda":"2026-11-12","fechaVuelta":"2026-11-15","fechasTexto":"jueves 12 al domingo 15 de noviembre","noches":3,"viajeros":"2 adultos","precioTotal":412,"precioPersona":206,"tipo":"Vuelo + hotel","vuelo":{"compania":"Wizz Air","directo":true,"detalle":"Ida 07:05 · vuelta 21:40"},"alojamiento":{"nombre":"…","estrellas":3,"nota":"8,4","zona":"a 1,2 km del centro"},"incluye":"Vuelos y 3 noches de hotel","porQue":"una o dos frases","fuente":"lastminute.com","url":"https://…","cancelable":false,
   "alternativas":[{"destino":"Oporto","fechasTexto":"20–23 nov","origen":"Sevilla","fuente":"lastminute.com","precioTotal":455,"url":"https://…"}]},
 "familia":{…misma estructura; "viajeros":"2 adultos y 3 hijos"…},
 "anteriores":[{"semanaTexto":"12 de octubre","pareja":{"destino":"Nápoles","precioTotal":380},"familia":{"destino":"Oporto","precioTotal":1105}}],
 "fuentes":[{"nombre":"lastminute.com","estado":"ok"},{"nombre":"eDreams","estado":"ok"},{"nombre":"Booking.com","estado":"sin resultados"}],
 "nota":""}
   - precioTotal y precioPersona son números en euros, sin texto. precioPersona = precioTotal dividido entre el número de viajeros, redondeado.
   - "anteriores": si el ofertas.json anterior tenía "estado":"ok", pon al principio un resumen de su semana (semanaTexto tal cual, por ejemplo «jueves 22 de octubre», y destino y precioTotal de pareja y familia) seguido de sus "anteriores"; guarda como máximo 8. Si tenía "estado":"pendiente", copia sus "anteriores" tal cual.
   - Si un perfil no tiene ninguna oferta válida, pon "pareja":{"motivo":"explicación corta"} (o "familia").
   - "fuentes": una entrada por cada fuente que hayas intentado, con estado "ok", "sin resultados" o "no disponible".
   - Valida con python3 -m json.tool antes de guardar.

6. GUARDAR EN GITHUB. No toques ningún otro archivo. En /tmp/pj: git add viajes/ofertas.json; git -c user.name=Claude -c user.email=noreply@anthropic.com commit -m "Ofertas de viaje del <fecha>"; git push origin HEAD:main. Si el push falla por cambios remotos, haz git pull --rebase y vuelve a empujar una vez.

7. MENSAJE FINAL (es lo que le llega a Ignacio por correo y al móvil; corto, sin tablas):
   «Ofertas de viaje:
   ❤️ Pareja: <destino>, <fechasTexto>, desde <origen>, <precioTotal> € en total (<fuente>).
   👨‍👩‍👧‍👦 Familia: <destino>, <fechasTexto>, desde <origen>, <precioTotal> € en total (<fuente>).
   Todo en https://ignacioros1978.github.io/prensa-javier/viajes/ · los precios cambian rápido, compruébalo antes de reservar.»
   Si algo falló (una fuente, el push), añádelo en una línea al final.
