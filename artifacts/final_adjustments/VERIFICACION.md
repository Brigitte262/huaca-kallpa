# Ajustes finales: reacción, gestos y pórtico

## Cambios aplicados

- Spawns entre 2.6 y 3.6 segundos, con mínimo absoluto de 2.6 incluso cuando
  la dificultad aplica su multiplicador. Separación global mínima de 52
  unidades entre peligros (o más si la velocidad de scroll configurada lo exige).
- El spawner conserva el candidato pendiente y espera si su profundidad
  invadiría la ventana de reacción de un obstáculo activo. Esto considera
  también el orden de llegada de los pórticos, que aparecen más lejos.
- Pórtico alto a 84 unidades: 4.2 segundos con el scroll actual de 20 unidades/s.
  Altura visual próxima de 0.32 a 0.37, manteniendo proporciones y el PNG actual;
  la abertura también crece. Conserva tipo high: solo sliding evita su colisión.
- Nueva capa BodyActionBridge después del clasificador existente: ambas muñecas
  claramente por encima de la cabeza -> JUMP; acortamiento claro del torso y
  descenso relativo de hombros -> CROUCH. Usa el baseline existente, confirmación,
  confianza, histéresis y cooldown. No reemplaza MediaPipe ni la clasificación lateral.
- Despacho a Player: no se consume una acción rechazada porque Player esté ocupado.
  CROUCH mantenido conserva sliding y el último frame crouch_03; cuando el torso
  vuelve a neutral, termina el desliz y regresa a RUN. Se siguen mostrando 01,02,03.

## Diagnóstico

El clasificador activo solo medía desplazamientos simultáneos de hombros/caderas;
no había una regla de muñecas por encima de la cabeza en el código actual.
Además, el despacho consumía flancos aun si Player rechazaba la acción y el
slide vencía a los 0.8 segundos aunque el usuario siguiera agachado.

Por eso no bastaba con conectar un método de Player: la capa añadida mapea las
posturas solicitadas sobre landmarks ya detectados, conservando los métodos
originales del clasificador y el detector.

## Verificación

- python utils/verify_final_adjustments.py: landmarks sintéticos en formato
  MediaPipe -> calibración original -> clasificador original -> puente ->
  main.update -> Player. Brazos arriba generan JUMP; torso inclinado genera
  CROUCH, mantenido más de 0.8 s; el pórtico cruza el umbral sin Game Over.
- Reglas high comprobadas: grounded y jumping chocan; sliding no choca.
- Acción CROUCH solicitada durante un salto llega después de aterrizar.
- Simulación de 120 segundos a máxima dificultad: 41 spawns, separación mínima
  de tiempo y profundidad comprobada en cada par de peligros activos.
  Registro: spawn_times.txt.
- Cinco pruebas negativas: neutralidad, un solo brazo, baja confianza,
  pulso breve y calibración sin completar no generan nuevas acciones.
- Cuatro pruebas de adquisición/pérdida de cámara siguen pasando.
- verify_game_flow.py pasa selección, calibración, 3-2-1, carrera, LEFT/RIGHT,
  JUMP/CROUCH, colisión/Game Over y recuperación de cámara.
- py_compile pasa. Capturas reales del framebuffer inspeccionadas:
  01_arms_up_jump.png, 02_bent_torso_crouch.png y 03_portal_passed_crouching.png.
- Los métodos originales desde _classify_lateral en PoseThread se compararon
  con la copia previa y permanecen idénticos. pose_detector.py, HUD,
  selección y score.py no se editaron.

La ejecución real de arranque no recibió frames de webcam en este entorno.
La prueba corporal con hardware sigue siendo manual; no se presenta el replay
sintético como verificación de detección real de MediaPipe.
