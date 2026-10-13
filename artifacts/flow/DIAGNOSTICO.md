# Restauración del flujo jugable

Se conservó el menú y no se modificaron MediaPipe ni los clasificadores de `vision/`.
Copias anteriores a esta reparación: `artifacts/flow_backup/`.

Causas comprobadas:

- ENTER pasaba directamente de selección a `playing`; faltaban calibración y cuenta atrás.
- `camera_controller.target = player` no cambiaba `camera_controller.player`, que seguía apuntando al jugador destruido.
- `Track._bg_current` y `_bg_next` eran quads opacos en `camera.ui`: cubrían Player, obstáculos y pista, aunque existieran en la escena 3D.
- Track se actualizaba desde main y también automáticamente desde Ursina; Player/obstáculos seguían actualizándose fuera de `playing`.
- Los colores del mundo seguían usando canales 0–255 con funciones que esperaban 0–1.

Cambios:

- `character_select -> calibration -> countdown -> playing` explícito.
- `calibration` espera frame real y uno de los estados publicados solo después de completar la calibración: LEFT, CENTER, RIGHT, JUMP o CROUCH.
- `NO_POSE`, cámara ausente o calibración pendiente bloquean el inicio. Si la pose se pierde durante 3-2-1, vuelve a calibración y reinicia la cuenta.
- Player se recrea con el género elegido, sprite run y cámara conectada a esa instancia. Se activa al entrar en `playing`.
- main es el único propietario de las actualizaciones de Player, Track y obstáculos. Spawner, puntuación y colisiones se ejecutan durante `playing`.
- Los fondos de Track pasan al mundo 3D, unidos a la cámara y detrás de la geometría; ya no son una capa UI delante del juego.
- Webcam de 50% de altura durante calibración/cuenta atrás; vuelve al 15.5% al correr. C funciona en todas las pantallas.
- La cuenta atrás tiene un indicador pequeño sobre el preview, sin cubrir la imagen.
- El HUD anterior se oculta al reiniciar y esperar calibración.

Verificación:

`python utils/verify_game_flow.py` ejecuta el callback de main mediante el bucle real de Ursina. Pasó el recorrido selección masculina -> ENTER -> espera de calibración -> 3/2/1 -> Player visible -> obstáculos y distancia -> LEFT/RIGHT -> salto -> agacharse -> colisión/Game Over. También pasó selección femenina, pausa sin avance, reinicio, cámara ocultable y reducción automática del preview. Las entradas de pose y frames de esta prueba son sintéticos: no verifica al detector.

Capturas del framebuffer inspeccionadas: `artifacts/flow/01_menu_unchanged.png`, `03_large_calibration_camera.png`, `05_countdown_1.png`, `05_countdown_2.png`, `05_countdown_3.png`, `06_running_player_visible.png`, `07_obstacles_and_scroll.png`, `10_jump.png`, `11_crouch.png`, `12_collision_game_over.png`, `13_female_running.png`.

Se ejecutó `python main.py`. Además, `python utils/verify_camera_startup.py` ejecuta la fuente real de main, confirma ENTER y limita la ejecución a 15 segundos, sin reemplazar PoseThread ni clasificadores. Resultado del hardware: NO_POSE, sin frames; el juego queda en calibración. La captura correspondiente es `14_real_camera_startup.png`.

`py_compile` pasó. Pylint no está instalado. La prueba de replay usa su propio archivo de récord dentro de artifacts, separado de `high_score.json`.

Pendiente: repetir el recorrido corporal completo con una cámara física disponible. No se considera verificado el reconocimiento con hardware mediante el replay sintético.
## Cierre de recuperación de cámara

Se añadió supervisión del hilo de captura sin modificar los clasificadores.
Quince lecturas fallidas consecutivas liberan el dispositivo y borran el frame
antiguo. main reinicia un hilo de captura terminado, conservando la preferencia
visible/oculta del preview. Una nueva instancia exige su calibración original.
La carrera se congela al perder frames o al volver a calibración; se conservan
distancia, puntos y obstáculos. Tras recuperar señal y calibrar, vuelve 3-2-1.

Verificación adicional: cuatro pruebas de adquisición y pérdida de señal pasan.
El replay del bucle de Ursina pasa también desconexión, sustitución del hilo,
congelación del mundo, calibración y reanudación. Los clasificadores se compararon
contra la copia anterior y son idénticos. La prueba real de arranque sigue sin
recibir frames del dispositivo en este entorno.

Para prueba manual: ejecutar `python main.py`, seleccionar con A/D, confirmar
con ENTER, mantener hombros/caderas visibles hasta terminar calibración,
esperar 3-2-1, mover izquierda/derecha, saltar, agacharse y comprobar Game Over.
C oculta/muestra la cámara. R reinicia. Al conectar una externa, el sistema usa
la primera cámara funcional disponible; no exige un índice manual. Si la cámara
actual sigue funcionando, se conserva esa cámara; conectar otra no fuerza un
cambio durante la carrera. Si se pierde la señal, se busca una disponible y se
calibra nuevamente.
