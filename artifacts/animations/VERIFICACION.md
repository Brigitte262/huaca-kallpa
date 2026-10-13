# Integración de animaciones

RUN: ocho frames a 11 FPS, en bucle. JUMP: tres frames distribuidos por
jump_progress durante los 0.5 segundos originales. CROUCH: tres frames
distribuidos por slide_timer durante los 0.8 segundos originales. Ambos
regresan a RUN al finalizar el estado. BASE y FLAG permanecen disponibles.

Las texturas se precargan y almacenan por personaje; cambiar de frame no abre
archivos ni modifica escala, posición, origen o collider. Se preparan sobre
un lienzo transparente de 512×512 con anclaje común de pies y altura visual
normalizada. Los movimientos de carril, salto y deslizamiento conservan sus
funciones y temporizadores originales.

Anomalía de asset: female_run_04.png contenía cuatro personajes en una lámina.
Se extrajo una sola pose con imagegen en female_run_04_single.png, usada como
frame 04 mediante PLAYER_FRAME_OVERRIDES. El original se conserva. Todos los
demás frames se cargan de sus archivos originales.

Track ya no crea la geometría del suelo marrón ni líneas de cuadrícula. Se
conservan avance, fondos, transiciones y lógica matemática de carriles.

Ciclo de vida del spawner: se descartan NodePaths vacíos antes de acceder a
ellos, y se retiran de la lista antes de destruirlos. El despawn se comprueba
antes de update. Las colecciones, el escudo y reset usan el mismo retiro
seguro. La lógica de colisiones y puntuación no se modificó.

Pruebas:

- python utils/verify_animations.py: dos partidas completas hasta Game Over
  en el bucle de Ursina, con salidas de pose reproducidas. Pasaron todos los
  frames, retorno a RUN, collider idéntico, transformaciones constantes en
  RUN y restablecidas al terminar acciones, y carga de FLAG.
- Regresión: nodo destruido aún presente en la lista y obstáculo en límite
  de despawn; retirados antes de volver a actualizar, sin AssertionError.
- python utils/verify_game_flow.py: selección, calibración, cuenta atrás,
  carrera, obstáculos, LEFT/RIGHT, salto, desliz, Game Over y recuperación
  de cámara siguen pasando.
- Capturas de RUN/JUMP/CROUCH/Game Over de ambos personajes inspeccionadas
  en artifacts/animations. Sin pista marrón. Previews de los ciclos RUN:
  female_run_cycle.gif y male_run_cycle.gif.
- Compilación de los archivos modificados pasa.

MediaPipe, clasificadores, hitboxes, reglas de colisión y cálculo de puntos
no se editaron. La cámara física sigue sin entregar frames en este entorno;
las partidas de verificación reproducen entradas en la conexión de pose.
