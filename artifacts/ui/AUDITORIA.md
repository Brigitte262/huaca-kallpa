# Auditoría visual de HUACA KALLPA

## Origen de los defectos

| Elementos originales | Causa comprobada | Corrección |
| --- | --- | --- |
| `CharacterSelectScreen.bg_base`, `panel`, `border_outer`, `border_inner`, `vignette`, tarjetas `shadow`, `glow`, `frame` | `color.rgb/rgba` recibían canales 0–255. La versión instalada espera 0–1 y saturaba los quads. | Colores de UI con `rgb32/rgba32`; paneles explícitos, sin placeholders. |
| `backdrop` y `sprite_ent` | Una textura ausente podía dejar un quad blanco; la carga fallida no necesariamente lanzaba una excepción. | Validación de archivo y resultado antes de crear el quad; búsqueda por nombre y carpeta absoluta. |
| `Track._bg_current`, `Track._bg_next` | Fondos hijos de `camera.ui`, con z=0.9/0.91, delante de los paneles y sprites originales del menú. | Capas del menú entre z=0.8 y z=0.3, delante del escenario. No se modificó Track. |
| Tarjetas originales, `name_txt`, `sub_txt`, `sep_bot`, `hint`, `cam_hint` | Tarjetas de altura 0.81–0.85 centradas en y=-0.13 salían de pantalla; nombres en -0.46 y subtítulos en -0.497 coincidían con controles y borde inferior. | Tarjetas de altura 0.408, nombres dentro de ellas, selección y controles en filas separadas. |
| `title_shadow` y `title` | Dos textos casi coincidentes; apariencia doble y pérdida de legibilidad. | Un único título con fuente Open Sans. |
| `HUD._panel_tl`, `_panel_tl_border`, `score_text`, `distance_text` | Activos desde el constructor, aunque todavía estaba abierta la selección. | Todos los elementos nacen deshabilitados; el estado del HUD decide cuáles mostrar. |
| PoseHUD `_bg_border`, `_bg`, `_calib_*`, `_lane_pads` y sus textos | Colores saturados, capas coincidentes y elementos en y=-0.496/-0.494; textos de carril sin propietario para limpieza. | Un único árbol de UI con columna lateral reservada y destrucción completa. |
| PoseHUD `_cal_panel_*`, `_cal_webcam_*`, `_err_*` | Panel central superpuesto, bordes delante del contenido y aviso de error demasiado estrecho para sus líneas. El modo gameplay nunca se activaba. | Calibración/error dentro del mismo panel lateral; modo sincronizado al confirmar personaje. |
| PoseHUD `_cam_border`, `_cam_entity`, `_cam_label` | Anchura dependiente del aspect de la ventana; posición no recalculada con la anchura real; orden de dibujo ocultaba el frame. | Preview pequeño con aspecto del frame, ancho máximo, esquina reservada y orden explícito imagen/borde. |
| `main.input` | Retorno anticipado en selección impedía procesar `C`. | `C` se procesa antes de delegar al menú. |
| Adaptador `snap_camera_error` | Solo comprobaba `NO_CAMERA`, pero PoseThread publica `NO_POSE` cuando no encuentra hardware. | Interpretación visual de `NO_POSE` sin frame como cámara no disponible. Clasificador intacto. |

## Alcance

Cambios en `main.py` limitados a arranque, consola UTF-8, configuración de ventana,
orden del input de UI y sincronización del modo visual. Cambios visuales en
`systems/ui.py`, `systems/pose_hud.py`, nuevo `systems/ui_layout.py` y constantes
UI añadidas a `config.py`. No se modificaron `vision/`, MediaPipe, reconocimiento,
colisiones, obstáculos, puntuación ni reglas del gameplay. No se abre ninguna
ventana OpenCV: se conserva `PoseThread(show_debug=False)` por defecto.

## Verificación

- `python main.py` ejecutado; arranque sin excepciones de Python.
- `python utils/verify_ui.py`: menú, ambos resaltados, calibración, preview,
  ocultación, estado listo, error y tamaños 1280×720, 1024×768 y 1440×600.
- `python utils/verify_production_ui.py`: inicialización real de main.py,
  escenario y jugador presentes, selección masculina, confirmación,
  `main.input('c')` mostrando/ocultando el preview y panel de calibración.
- Capturas reales del framebuffer inspeccionadas en `artifacts/ui/`:
  sin rectángulos blancos ni textos superpuestos en los estados comprobados.
- `py_compile` pasa para los siete archivos de código creados/modificados.
- Pylint no está instalado; no se instaló software adicional.
- Advertencias existentes de Panda3D: foco de ventana, perfil PNG e icono Ursina.

## Límite pendiente de hardware

PoseThread informa que no encuentra ninguna cámara en índices 0–3. Por eso se
verificó la presentación de calibración y webcam con frames RGB sintéticos,
claramente separados del controlador real. La captura de cámara física y la
calibración corporal real quedan pendientes de una webcam disponible. No se
modificaron permisos de Windows ni la detección para ocultar este problema.
