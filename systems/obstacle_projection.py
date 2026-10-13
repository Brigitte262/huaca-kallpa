"""Deterministic visual projection onto the Moche road, separate from collisions."""
import config


def project_obstacle(lane, z_position, near_size):
    """Return screen x, floor y, width, height and view depth for an obstacle.

    Args:
        lane: Logical integer lane, unchanged by projection.
        z_position: Logical depth scrolling toward and then behind the player.
        near_size: Width/height at the player's ground plane, in screen-height units.
    Returns:
        tuple: x, bottom_y, width, height, depth; bottom_y is the floor anchor.
    """
    depth = max(config.OBSTACLE_VIEW_MIN_DEPTH,
                config.OBSTACLE_PERSPECTIVE_DEPTH + z_position)
    factor = config.OBSTACLE_PERSPECTIVE_DEPTH / depth
    x = (lane - config.PLAYER_START_LANE) * config.OBSTACLE_SCREEN_LANE_STEP * factor
    y = config.OBSTACLE_PATH_HORIZON_Y + (
        config.OBSTACLE_PATH_NEAR_Y - config.OBSTACLE_PATH_HORIZON_Y) * factor
    return x, y, near_size[0] * factor, near_size[1] * factor, depth
