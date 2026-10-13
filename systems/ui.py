"""
HUD System – Huaca Kallpa (estética Moche premium v2)

Incluye:
  - HUD en partida con tipografía Moche cálida
  - Pantalla de selección de personaje (GUARDIANA / GUARDIÁN) premium
  - Pantalla de pausa
  - Pantalla de Game Over con borde terracota
  - Pantalla de Victoria dorada (META ALCANZADA)
  - Sistema de cosméticos (arquitectura, sin gameplay)

COSMÉTICOS – niveles:
  0  → base
  2  → bracelets
  3  → necklace
  4  → belt_mantle
  5  → ceremonial_headpiece
  6  → ceremonial_full_set (completar recorrido)
"""

from ursina import Entity, Text, camera, color, destroy
import config

# ── Paleta Moche ──────────────────────────────────────────────────────────────
_TERRACOTA  = color.rgb32(190, 80, 40)
_ORO        = color.rgb32(230, 175, 50)
_ORO_CLARO  = color.rgb32(255, 220, 100)
_CREMA      = color.rgb32(245, 230, 190)
_AZUL_OSC   = color.rgb32(10, 15, 40)
_NEGRO      = color.rgb32(10, 8, 15)
_OCRE       = color.rgb32(200, 150, 60)
_VERDE      = color.rgb32(60, 180, 80)
_PANEL_BG   = color.rgba32(8, 4, 18, 230)
_ADOBE      = color.rgb32(160, 100, 50)

# Módulo de selección de personaje (valor exportado)
chosen_gender: str = 'female'   # 'female' | 'male'

# Arquitectura de cosméticos (niveles de desbloqueo – sin efecto en gameplay)
COSMETIC_LEVELS = {
    0: None,
    1: None,
    2: 'assets/cosmetics/bracelets.png',
    3: 'assets/cosmetics/necklace.png',
    4: 'assets/cosmetics/belt_mantle.png',
    5: 'assets/cosmetics/ceremonial_headpiece.png',
    6: 'assets/cosmetics/ceremonial_full_set.png',
}


# ══════════════════════════════════════════════════════════════════════════════
#  PANTALLA DE SELECCIÓN DE PERSONAJE  (versión premium)
# ══════════════════════════════════════════════════════════════════════════════
class CharacterSelectScreen:
    """Own a single menu tree with two readable character cards."""

    def __init__(self, on_select):
        """Build the menu; on_select receives the confirmed gender."""
        from systems.ui_layout import ui_root, panel, label, asset_texture
        self._on_select = on_select
        self.root = ui_root()
        self._selected = 'female'
        base = panel(self.root, config.UI_CANVAS_SIZE, (0, 0), config.UI_INK, z=0.8)
        base.fill_screen = True
        texture = asset_texture(config.UI_MENU_BACKGROUND)
        if texture:
            backdrop = Entity(parent=self.root, model='quad', texture=texture,
                   color=color.white, scale=config.UI_CANVAS_SIZE, z=0.7)
            backdrop.fill_screen = True
        panel(self.root, (1.12, 1), (-0.19, 0), config.UI_MENU_SHADE, z=0.6)
        label(self.root, 'HUACA KALLPA', (-0.19, 0.37), 2.8, config.UI_GOLD)
        label(self.root, 'El poder del valle Moche', (-0.19, 0.285), 1.15)
        label(self.root, 'ELIGE A TU GUARDIÁN', (-0.19, 0.215), 0.9, config.UI_GOLD)
        self._cards = []
        for gender, x, name, subtitle in config.UI_CHARACTER_CARDS:
            frame = panel(self.root, (0.414, 0.422), (x, -0.045),
                          config.UI_GOLD, z=0.5)
            panel(self.root, (0.4, 0.408), (x, -0.045), config.UI_CARD, z=0.4)
            texture = asset_texture(f'assets/characters/{gender}/{gender}_base.png')
            sprite = None
            if texture:
                sprite = Entity(parent=self.root, model='quad', texture=texture,
                                scale=(0.28, 0.28), position=(x, 0.015, 0.3),
                                color=color.white)
            label(self.root, name, (x, -0.155), 1.35, config.UI_CREAM)
            label(self.root, subtitle, (x, -0.201), 0.8, config.UI_CREAM)
            badge = label(self.root, 'SELECCIONADA' if gender == 'female' else 'SELECCIONADO',
                          (x, -0.29), 0.75, config.UI_GOLD)
            self._cards.append(dict(gender=gender, frame=frame, badge=badge, sprite=sprite))
        label(self.root, 'A / D  ·  Elegir     ENTER  ·  Iniciar',
              (-0.19, -0.36), 1.05, config.UI_GOLD)
        label(self.root, 'Control corporal     C  ·  Cámara     ESC  ·  Salir',
              (-0.19, -0.413), 0.85)
        self._highlight(self._selected)

    def _highlight(self, gender):
        """Highlight one card without changing its dimensions; return None."""
        for card in self._cards:
            selected = card['gender'] == gender
            card['frame'].color = config.UI_GOLD if selected else config.UI_TERRACOTTA
            card['badge'].enabled = selected

    def input(self, key):
        """Handle menu navigation and confirmation; return None."""
        if key in ('left arrow', 'a', 'right arrow', 'd'):
            self._selected = 'female' if key in ('left arrow', 'a') else 'male'
            self._highlight(self._selected)
        elif key in ('enter', 'return'):
            self._confirm()

    def _confirm(self):
        """Publish the chosen character and remove the menu; return None."""
        global chosen_gender
        chosen_gender = self._selected
        self.destroy()
        self._on_select(self._selected)

    def destroy(self):
        """Disable immediately and destroy the complete menu tree; return None."""
        self.root.enabled = False
        destroy(self.root)


class HUD:
    """Gestiona todos los elementos de UI en pantalla durante la partida."""

    def __init__(self):
        """Build gameplay and result UI disabled until their state is active."""
        # ── Panel superior izquierdo (puntos + distancia) ─────────────────────
        self._panel_tl = Entity(
            model='quad', parent=camera.ui,
            scale=(0.42, 0.14), position=(-0.62, 0.44), z=0.8,
            color=_PANEL_BG,
        )
        # Borde del panel TL
        self._panel_tl_border = Entity(
            model='quad', parent=camera.ui,
            scale=(0.425, 0.145), position=(-0.62, 0.44), z=0.81,
            color=color.rgba32(230, 175, 50, 70),
        )

        self.score_text = Text(
            text='PUNTOS: 0',
            position=(-0.83, 0.47),
            scale=1.4,
            color=_ORO,
        )

        self.distance_text = Text(
            text='0 m',
            position=(-0.83, 0.42),
            scale=1.2,
            color=_CREMA,
        )

        # ── Récord (arriba derecha) ────────────────────────────────────────────
        self._panel_tr = Entity(
            model='quad', parent=camera.ui,
            scale=(0.32, 0.09), position=(0.70, 0.44), z=0.8,
            color=_PANEL_BG,
            enabled=False,
        )

        self.high_score_text = Text(
            text='RÉCORD: 0',
            position=(0.57, 0.44),
            scale=1.1,
            color=_TERRACOTA,
            enabled=False,
        )

        # ── Escudo activo ──────────────────────────────────────────────────────
        self.shield_text = Text(
            text='⚔ ESCUDO ACTIVO',
            position=(0, 0.37),
            scale=1.4,
            color=color.rgb32(60, 130, 200),
            origin=(0, 0),
            enabled=False,
        )

        # ── GAME OVER ─────────────────────────────────────────────────────────
        # Borde exterior terracota
        self._go_border2 = Entity(
            model='quad', parent=camera.ui,
            scale=(1.32, 0.87), position=(0, 0), z=0.87,
            color=color.rgba32(190, 80, 40, 80),
            enabled=False,
        )
        # Borde interior
        self._go_border = Entity(
            model='quad', parent=camera.ui,
            scale=(1.28, 0.83), position=(0, 0), z=0.86,
            color=color.rgba32(190, 80, 40, 130),
            enabled=False,
        )
        # Fondo
        self._go_bg = Entity(
            model='quad', parent=camera.ui,
            scale=(1.26, 0.81), position=(0, 0), z=0.85,
            color=color.rgba32(10, 5, 20, 240),
            enabled=False,
        )

        # Sombra del título de game over
        self._go_title_shadow = Text(
            text='FIN DEL CAMINO',
            position=(0.003, 0.215),
            scale=3.2,
            color=color.rgba32(80, 20, 5, 140),
            origin=(0, 0),
            enabled=False,
        )

        self.game_over_text = Text(
            text='FIN DEL CAMINO',
            position=(0, 0.22),
            scale=3.2,
            color=_TERRACOTA,
            origin=(0, 0),
            enabled=False,
        )

        # Separador
        self._go_sep = Text(
            text='- - - - - - - - - - - - - - - - - -',
            position=(0, 0.10),
            scale=1.2,
            color=color.rgba32(190, 80, 40, 160),
            origin=(0, 0),
            enabled=False,
        )

        self.game_over_stats = Text(
            text='',
            position=(0, -0.04),
            scale=1.5,
            color=_CREMA,
            origin=(0, 0),
            enabled=False,
        )

        self._go_sep2 = Text(
            text='- - - - - - - - - - - - - - - - - -',
            position=(0, -0.21),
            scale=1.2,
            color=color.rgba32(190, 80, 40, 100),
            origin=(0, 0),
            enabled=False,
        )

        self.game_over_hint = Text(
            text='R = Reiniciar     ·     ESC = Salir',
            position=(0, -0.285),
            scale=1.2,
            color=_OCRE,
            origin=(0, 0),
            enabled=False,
        )

        # ── PAUSA ─────────────────────────────────────────────────────────────
        self._pause_border = Entity(
            model='quad', parent=camera.ui,
            scale=(0.79, 0.32), position=(0, 0), z=0.86,
            color=color.rgba32(230, 175, 50, 80),
            enabled=False,
        )
        self._pause_bg = Entity(
            model='quad', parent=camera.ui,
            scale=(0.77, 0.30), position=(0, 0), z=0.85,
            color=_PANEL_BG,
            enabled=False,
        )

        self.pause_text = Text(
            text='PAUSA',
            position=(0, 0.04),
            scale=2.4,
            color=_ORO,
            origin=(0, 0),
            enabled=False,
        )

        self.pause_hint = Text(
            text='ESC para continuar',
            position=(0, -0.05),
            scale=1.2,
            color=_CREMA,
            origin=(0, 0),
            enabled=False,
        )

        # ── VICTORIA (META ALCANZADA) ──────────────────────────────────────────
        # Borde exterior dorado brillante
        self._victory_border2 = Entity(
            model='quad', parent=camera.ui,
            scale=(1.52, 0.97), position=(0, 0), z=0.87,
            color=color.rgba32(255, 220, 100, 90),
            enabled=False,
        )
        self._victory_border = Entity(
            model='quad', parent=camera.ui,
            scale=(1.48, 0.93), position=(0, 0), z=0.86,
            color=color.rgba32(230, 175, 50, 140),
            enabled=False,
        )
        self._victory_bg = Entity(
            model='quad', parent=camera.ui,
            scale=(1.46, 0.91), position=(0, 0), z=0.84,
            color=color.rgba32(8, 4, 18, 245),
            enabled=False,
        )

        # Sombra del título de victoria
        self._vic_title_shadow = Text(
            text='META ALCANZADA',
            position=(0.003, 0.235),
            scale=3.4,
            color=color.rgba32(100, 60, 5, 140),
            origin=(0, 0),
            enabled=False,
        )

        self.victory_title = Text(
            text='META ALCANZADA',
            position=(0, 0.24),
            scale=3.4,
            color=_ORO_CLARO,
            origin=(0, 0),
            enabled=False,
        )

        self.victory_subtitle = Text(
            text='¡Guardián del Templo Moche!',
            position=(0, 0.12),
            scale=1.45,
            color=_CREMA,
            origin=(0, 0),
            enabled=False,
        )

        self._vic_sep = Text(
            text='- - - - - - - - - - - - - - - - - - - - -',
            position=(0, 0.02),
            scale=1.2,
            color=color.rgba32(230, 175, 50, 160),
            origin=(0, 0),
            enabled=False,
        )

        self.victory_stats = Text(
            text='',
            position=(0, -0.10),
            scale=1.5,
            color=_CREMA,
            origin=(0, 0),
            enabled=False,
        )

        self._vic_sep2 = Text(
            text='- - - - - - - - - - - - - - - - - - - - -',
            position=(0, -0.245),
            scale=1.2,
            color=color.rgba32(230, 175, 50, 120),
            origin=(0, 0),
            enabled=False,
        )

        self.victory_hint = Text(
            text='R = Jugar de nuevo     ·     ESC = Salir',
            position=(0, -0.305),
            scale=1.15,
            color=_OCRE,
            origin=(0, 0),
            enabled=False,
        )

        from systems.ui_layout import ui_root
        self.root = ui_root()
        for element in self._all_elements:
            element.parent = self.root
            if isinstance(element, Text):
                element.font = config.UI_FONT
            element.enabled = False
        print("[HUD] Inicializado con estética Moche premium")

    # ── Lista de todos los elementos para ocultar rápido ──────────────────────
    @property
    def _all_elements(self):
        """Return the complete owned HUD element list for visibility changes."""
        return [
            self._panel_tl, self._panel_tl_border,
            self.score_text, self.distance_text,
            self._panel_tr, self.high_score_text,
            self.shield_text,
            self._go_bg, self._go_border, self._go_border2,
            self._go_title_shadow, self.game_over_text,
            self._go_sep, self.game_over_stats,
            self._go_sep2, self.game_over_hint,
            self._pause_bg, self._pause_border,
            self.pause_text, self.pause_hint,
            self._victory_bg, self._victory_border, self._victory_border2,
            self._vic_title_shadow, self.victory_title,
            self.victory_subtitle, self._vic_sep,
            self.victory_stats, self._vic_sep2, self.victory_hint,
        ]

    # ── Actualización ─────────────────────────────────────────────────────────
    def update(self, score, distance, shield_active, shield_timer,
               game_state, orbs_collected=0, high_score=0):
        """Display supplied score values for game_state; return None."""

        # Ocultar todo
        for e in self._all_elements:
            e.enabled = False

        if game_state == 'playing':
            self._panel_tl.enabled        = True
            self._panel_tl_border.enabled = True
            self.score_text.enabled       = True
            self.distance_text.enabled    = True
            self.score_text.text          = f'PUNTOS: {int(score)}'
            self.distance_text.text       = f'{int(distance)} m'

            if high_score > 0:
                self._panel_tr.enabled       = True
                self.high_score_text.enabled = True
                self.high_score_text.text    = f'RÉCORD: {int(high_score)}'

            if shield_active:
                self.shield_text.enabled = True
                self.shield_text.text    = f'⚔ ESCUDO ({shield_timer:.1f}s)'

        elif game_state == 'paused':
            self._panel_tl.enabled        = True
            self._panel_tl_border.enabled = True
            self.score_text.enabled       = True
            self.distance_text.enabled    = True
            self._pause_bg.enabled        = True
            self._pause_border.enabled    = True
            self.pause_text.enabled       = True
            self.pause_hint.enabled       = True

        elif game_state == 'game_over':
            self._go_bg.enabled           = True
            self._go_border.enabled       = True
            self._go_border2.enabled      = True
            self._go_title_shadow.enabled = True
            self.game_over_text.enabled   = True
            self._go_sep.enabled          = True
            self.game_over_stats.enabled  = True
            self._go_sep2.enabled         = True
            self.game_over_hint.enabled   = True
            self.game_over_stats.text = (
                f'Puntuación:  {int(score)}\n'
                f'Distancia:   {int(distance)} m\n'
                f'Huacos:      {orbs_collected}'
            )

        elif game_state == 'victory':
            self._victory_bg.enabled       = True
            self._victory_border.enabled   = True
            self._victory_border2.enabled  = True
            self._vic_title_shadow.enabled = True
            self.victory_title.enabled     = True
            self.victory_subtitle.enabled  = True
            self._vic_sep.enabled          = True
            self.victory_stats.enabled     = True
            self._vic_sep2.enabled         = True
            self.victory_hint.enabled      = True
            self.victory_stats.text = (
                f'Puntuación:   {int(score)}\n'
                f'Distancia:    {int(distance)} m\n'
                f'Huacos:       {orbs_collected}'
            )

    # ── Mostrar victoria (llamado desde main en el momento del trigger) ────────
    def show_victory(self, score, distance, orbs):
        """Display victory using supplied score, distance and orb count; return None."""
        self._victory_bg.enabled       = True
        self._victory_border.enabled   = True
        self._victory_border2.enabled  = True
        self._vic_title_shadow.enabled = True
        self.victory_title.enabled     = True
        self.victory_subtitle.enabled  = True
        self._vic_sep.enabled          = True
        self.victory_stats.enabled     = True
        self._vic_sep2.enabled         = True
        self.victory_hint.enabled      = True
        self.victory_stats.text = (
            f'Puntuación:   {int(score)}\n'
            f'Distancia:    {int(distance)} m\n'
            f'Huacos:       {orbs}'
        )
