from ursina import color

# ----------------------------------------------------------------------------
# SCREEN SETTINGS
# ----------------------------------------------------------------------------
WINDOW_TITLE = "Huaca Kallpa – Runner Moche"
WINDOW_SIZE = (1280, 720)
WINDOW_BORDERLESS = False
WINDOW_FULLSCREEN = False

# ----------------------------------------------------------------------------
# COLOR PALETTE – Temática Moche
# Inspirada en la Huaca de la Luna: terracota, ocre/dorado, crema, adobe,
# azul pizarra oscuro y negro.
# ----------------------------------------------------------------------------
# Fondo (cielo nocturno sobre el valle Moche)
COLOR_BACKGROUND   = color.rgb32(15, 12, 30)          # Azul muy oscuro / negro-índigo

# Pista (adobe apisonado)
COLOR_TRACK        = color.rgb32(180, 120, 70)         # Terracota media

# Líneas de la cuadrícula
COLOR_GRID_LINES   = color.rgba32(120, 70, 30, 60)     # Sombra marrón semitransparente

# Jugador  (preparado para ser reemplazado por sprite Moche)
COLOR_PLAYER       = color.rgb32(220, 170, 60)         # Oro/ocre brillante

# Obstáculos
COLOR_OBS_LOW      = color.rgb32(190, 100, 45)         # Adobe rojizo  (vasija / piedra baja)
COLOR_OBS_HIGH     = color.rgb32(100, 55, 25)          # Adobe oscuro  (muro / pórtico alto)
COLOR_OBS_MOVING   = color.rgb32(210, 140, 50)         # Ocre dorado   (elemento móvil)

# Coleccionables
COLOR_ORB          = color.rgb32(240, 200, 60)         # Oro Moche (puntos)
COLOR_SHIELD       = color.rgb32(60, 130, 180)         # Azul cobalto (escudo / huaco)

# UI
COLOR_UI_TEXT      = color.rgb32(245, 230, 190)        # Crema / hueso (texto HUD)
COLOR_MENU_TITLE   = color.rgb32(230, 180, 50)         # Oro Moche (título menú)
COLOR_MENU_TEXT    = color.rgb32(245, 230, 190)        # Crema

# Texturas
TEXTURE_TRACK      = 'assets/track_texture.png'
TEXTURE_WALL       = 'assets/wall_texture.png'
TEXTURE_WOOD       = 'assets/wood_texture.png'
TEXTURE_METAL      = 'assets/metal_texture.png'
TEXTURE_ORB        = 'assets/orb_texture.png'

# ----------------------------------------------------------------------------
# GAME SETTINGS
# ----------------------------------------------------------------------------
# Track / Pista
TRACK_WIDTH            = 10.0
TRACK_LENGTH           = 100.0
TRACK_SCROLL_SPEED     = 20.0          # Velocidad base (unidades/s)
GRID_SPACING           = 5.0
GRID_ANIMATION_SPEED   = 0.5

# Sistema de carriles
LANE_POSITIONS         = [-2.0, 0.0, 2.0]   # X de los carriles: Izquierda, Centro, Derecha
LANE_COUNT             = 3
LANE_SWITCH_SPEED      = 12.0               # Velocidad de suavizado visual
LANE_SPEED             = 10.0               # Legacy (conservado)

# Jugador
PLAYER_SIZE            = (0.8, 0.8, 0.8)
PLAYER_START_LANE      = 1                  # Carril central
PLAYER_START_Y         = 0.5
PLAYER_START_Z         = 0.0
JUMP_HEIGHT            = 2.5
JUMP_DURATION          = 0.5
SLIDE_DURATION         = 0.8
SLIDE_HEIGHT_SCALE     = 0.4

# Coleccionables
COLLECTIBLE_SIZE           = 0.5
COLLECTIBLE_HEIGHT         = 0.8
SHIELD_DURATION            = 5.0
SCORE_PER_UNIT             = 10
SCORE_PER_SECOND           = 10
SCORE_ORB                  = 100

# Obstáculos
OBS_LOW_SIZE               = (1.0, 0.6, 1.0)
OBS_LOW_HEIGHT             = 0.3
OBS_HIGH_SIZE              = (1.0, 2.5, 1.0)
OBS_HIGH_HEIGHT            = 1.25
OBS_MOVING_SIZE            = (1.0, 1.2, 1.0)
OBS_MOVING_HEIGHT          = 0.6
OBS_MOVING_SPEED           = 5.0
OBSTACLE_DESPAWN_DISTANCE  = -10.0
OBSTACLE_SPAWN_DISTANCE    = 60.0
SPAWN_INTERVAL_MIN         = 2.6
SPAWN_INTERVAL_MAX         = 3.6
OBSTACLE_COLLISION_THRESHOLD = 1.5

# Cámara
CAMERA_POSITION        = (0, 6, -14)
CAMERA_ROTATION_X      = 15
CAMERA_FOLLOW_SPEED    = 0.1

# HUD
UI_SCORE_POSITION      = (-0.85, 0.45)
UI_DISTANCE_POSITION   = (0.65, 0.45)
UI_SHIELD_POSITION     = (0, 0.35)
UI_GAME_OVER_POSITION  = (0, 0)
UI_FONT_SIZE           = 1.5
UI_COLOR               = color.rgb32(245, 230, 190)   # Crema Moche

# Menú
UI_MENU_TITLE_POS      = (0, 0.2)
UI_MENU_SUBTITLE_POS   = (0, 0.1)
UI_MENU_INSTRUCT_POS   = (0, -0.2)

# Velocidad / Dificultad
INITIAL_SPEED              = 20.0
MAX_SPEED                  = 50.0
SPEED_INCREMENT            = 0.5
DIFFICULTY_SCALE_DISTANCE  = 500.0

# VFX
SHAKE_INTENSITY_COLLISION  = 0.5
SHAKE_DURATION_COLLISION   = 0.4
SHAKE_INTENSITY_SHIELD     = 0.3
SHAKE_DURATION_SHIELD      = 0.2
CAMERA_TILT_ANGLE          = 2.0
CAMERA_TILT_SPEED          = 3.0

# Colisiones
PLAYER_COLLISION_RADIUS    = 1.0
COLLECTIBLE_SPAWN_CHANCE   = 0.3

# Debug
DEBUG_MODE = False

# ----------------------------------------------------------------------------
# CONTROL POR POSE (MediaPipe)
# ----------------------------------------------------------------------------
POSE_ENABLED       = True    # False → solo teclado
POSE_CAMERA_INDEX  = 0       # Índice de la webcam (0 = predeterminada)
# Stable UI design canvas; all dimensions are measured against screen height.
UI_ASPECT = 16 / 9
UI_CANVAS_SIZE = (UI_ASPECT, 1)
UI_INK = color.rgb32(22, 15, 18)
UI_CARD = color.rgb32(44, 28, 25)
UI_CREAM = color.rgb32(245, 230, 190)
UI_GOLD = color.rgb32(230, 175, 50)
UI_TERRACOTTA = color.rgb32(150, 73, 47)
UI_MENU_SHADE = color.rgba32(22, 15, 18, 225)
UI_MENU_BACKGROUND = 'assets/backgrounds/camino_del_valle.png'
UI_FONT = 'OpenSans-Regular.ttf'
UI_CHARACTER_CARDS = (
    ('female', -0.43, 'GUARDIANA', 'Guerrera del Valle'),
    ('male', 0.05, 'GUARDIÁN', 'Señor del Templo'),
)
UI_SIDEBAR_X = 0.64
UI_SIDEBAR_WIDTH = 0.41
UI_WEBCAM_HEIGHT = 0.155
UI_WEBCAM_Y = -0.31
UI_POSE_PANEL_Y = 0.04
UI_POSE_PANEL_HEIGHT = 0.39
UI_LAYER_PANEL = -1
UI_LAYER_CONTENT = -1.1
UI_RESIZE_EPSILON = 0.0001

UI_CAMERA_IMAGE_ORDER = 20
UI_CAMERA_BORDER_ORDER = 19
UI_WEBCAM_MAX_WIDTH = 0.35

# Run startup and world backdrop (UI design is unchanged).
RUN_COUNTDOWN_SECONDS = 3.0
RUN_READY_STATES = ('LEFT', 'CENTER', 'RIGHT', 'JUMP', 'CROUCH')
WORLD_BACKGROUND_DEPTH = 200.0
WORLD_BACKGROUND_MARGIN = 1.01
UI_CALIBRATION_CAMERA_HEIGHT = 0.50
UI_CALIBRATION_CAMERA_MAX_WIDTH = 0.95
UI_CALIBRATION_CAMERA_POSITION = (-0.25, 0.02)
UI_CALIBRATION_CAMERA_HINT_POSITION = (-0.25, -0.28)
UI_CAMERA_BORDER_SIZE = 0.012
UI_COUNTDOWN_POSITION = (-0.25, 0.37)
UI_COUNTDOWN_SCALE = 4

UI_COUNTDOWN_BACKING_SIZE = (0.04, 0.04)
# Automatic camera acquisition; classification parameters remain unchanged.
CAMERA_SCAN_COUNT = 8
CAMERA_BACKEND_NAMES = ('CAP_DSHOW', 'CAP_MSMF', 'CAP_ANY')
CAMERA_WARMUP_READS = 12
CAMERA_WARMUP_DELAY = 0.05
CAMERA_RETRY_DELAY = 2.0
CAMERA_FAILED_READ_LIMIT = 15
CAMERA_FAILED_READ_DELAY = 0.02
# Sprite playback affects textures only, never lane/state/collider dimensions.
PLAYER_RUN_FPS = 11.0
PLAYER_RUN_FRAME_COUNT = 8
PLAYER_ACTION_FRAME_COUNT = 3
PLAYER_SPRITE_CANVAS = 512
PLAYER_SPRITE_ALPHA_THRESHOLD = 128
PLAYER_SPRITE_BODY_HEIGHT = 0.90
PLAYER_SPRITE_BASELINE = 0.96
PLAYER_SPRITE_MAX_WIDTH = 0.96
PLAYER_FRAME_OVERRIDES = {
    'female_run_04.png': 'assets/characters/female/female_run_04_single.png',
}
# Obstacle-only road projection, in units of screen height.
OBSTACLE_PERSPECTIVE_DEPTH = 14.0
OBSTACLE_PATH_HORIZON_Y = 0.10
OBSTACLE_PATH_NEAR_Y = -0.36
OBSTACLE_SCREEN_LANE_STEP = 0.22
OBSTACLE_VIEW_MIN_DEPTH = 1.0
OBSTACLE_ALPHA_THRESHOLD = 128
OBSTACLE_NEAR_HEIGHTS = {
    'piedra': 0.14,
    'vasija': 0.19,
    'bloque_ceremonial': 0.17,
    'muro_bajo': 0.15,
    'columna_caida': 0.14,
    'portico_alto': 0.37,
}

# Reaction-safe obstacle spacing and high-portal anticipation.
OBSTACLE_MIN_REACTION_SECONDS = 2.6
OBSTACLE_MIN_SPAWN_GAP = 52.0
PORTICO_SPAWN_DISTANCE = 84.0
# Posture-to-action bridge; MediaPipe and existing classifiers are untouched.
BODY_ACTION_MIN_CONFIDENCE = 0.5
BODY_ACTION_CONFIRM_SECONDS = 0.10
BODY_ACTION_COOLDOWN_SECONDS = 0.65
BODY_ACTION_HEAD_INDICES = (0, 1, 2, 3, 4, 5, 6)
BODY_ACTION_WRIST_INDICES = (15, 16)
BODY_ACTION_TORSO_INDICES = (11, 12, 23, 24)
BODY_ACTION_ARM_MARGIN = 0.04
BODY_ACTION_ARM_RELEASE_MARGIN = 0.08
BODY_ACTION_TORSO_RATIO = 0.70
BODY_ACTION_TORSO_RELEASE_RATIO = 0.85
BODY_ACTION_SHOULDER_DROP = 0.20
BODY_ACTION_SHOULDER_RELEASE_DROP = 0.10
BODY_ACTION_MIN_TORSO_HEIGHT = 0.1
BODY_ACTION_SLIDE_HOLD_FRAMES = 2
