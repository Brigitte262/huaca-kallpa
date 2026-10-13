# Verificación del reinicio de escenas

Se añadió `main.reset_visual_scene()` antes de una nueva ronda. Limpia obstáculos,
antorchas, partículas y decoración final; cancela el crossfade, reinicia sus índices
y temporizadores y restaura `camino_del_valle`. Track, fondo y raíces del HUD se
reutilizan. La inicialización repetida no crea otra escena.

El crossfade mezcla dos texturas sobre una sola superficie. Se eliminó el
desplazamiento UV con repetición que dividía el camino. Las texturas del escenario,
antorchas y decoración final se conservan en caché.

## Prueba ejecutada en Ursina

`python utils/verify_scene_reset.py`: tres rondas con Game Over, victoria y
reinicio durante una transición; R repetida y llamada repetida a init_entities.

| Reinicio | Entidades vivas | Fondos | Tiempo medio por frame |
|---|---:|---:|---:|
| 1 | 70 | 1 | 17.78 ms |
| 2 | 70 | 1 | 17.20 ms |
| 3 | 70 | 1 | 17.35 ms |

Sin acumulación de entidades ni caída progresiva de rendimiento en esta prueba.
No se afirma una garantía de 60 FPS en todo hardware. Las tres capturas
`round_*_restart.png` fueron inspeccionadas: camino del valle completo, sin división
ni segundo escenario. Los objetos de la ronda anterior quedan destruidos.

`python utils/verify_game_flow.py`: selección, calibración, cuenta atrás, carrera,
obstáculos, LEFT/RIGHT, JUMP, CROUCH, colisión y reinicio pasan usando salidas de pose
sintéticas. Estos ensayos no son una validación corporal frente a la webcam.
No se modificaron MediaPipe, controles, colisiones ni puntuación.

Los ensayos usan un archivo de récord independiente del récord real del usuario.
