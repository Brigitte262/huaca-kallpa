# Obstáculos apoyados en el camino

Se sustituyó el escalado visual doble y el centro Y proporcional al tamaño
por una proyección independiente de la posición usada en colisiones.

factor = 14 / max(1, 14 + z_position)
screen_scale = near_size * factor
floor_y = horizon_y + (near_floor_y - horizon_y) * factor
screen_x = lane_offset * factor

El sprite usa origin=(0,-0.5), por lo que floor_y ancla su base, no su centro.
Los márgenes transparentes se recortan únicamente al preparar la textura en
memoria, sin modificar los PNG. Las coordenadas de pantalla se convierten a
un quad orientado a cámara; se evita volver a aplicar un escalado artificial
sobre el escalado perspectivo ya realizado por la cámara.

Los seis assets tienen una altura próxima configurada y conservan su proporción.
El horizonte y el punto de contacto próximo están definidos en config.py.
El carril lógico queda fijo hasta el despawn, incluido el tipo moving, tal como
se solicitó. Sus nombres de tipo y reglas de evitación permanecen intactos.
No se modificaron spawner, collision.py, MediaPipe, Player ni la puntuación.

La entidad lógica conserva lane, z_position y obs_type. El sprite visual se
retira al destruir su propietario. Se mantiene el umbral de despawn original,
por detrás del jugador, y la limpieza segura del spawner.

Verificación:

- python utils/verify_grounded_obstacles.py: los seis assets renderizados a
  z=60,25,2; crecimiento monotónico, base descendiendo sobre el camino,
  carril constante, retiro conjunto del sprite y la entidad.
- Reglas de colisión comprobadas para grounded/jumping/sliding y low/high/moving:
  siguen iguales, usan solo carril lógico y distancia. Despawn seguro detrás.
- python utils/verify_game_flow.py: recorrido de juego y reconexión siguen pasando.
- Capturas de piedra, vasija, muro, columna, bloque y pórtico inspeccionadas.
- py_compile pasa para los archivos modificados y el verificador.

Capturas disponibles en este directorio: piedra.png, vasija.png,
muro_bajo.png, columna_caida.png, bloque_ceremonial.png, portico_alto.png.
