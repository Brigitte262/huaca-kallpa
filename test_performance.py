"""
Performance Stress Test
Validate that visual upgrades (Octahedron, Trails, Glows) don't tank FPS.
"""

from ursina import *
import config
from entities.player import Player
from entities.obstacle import Obstacle
from entities.track import Track
import time as pytime

def run_stress_test():
    app = Ursina()
    
    # Setup Window
    window.title = "Temple Run Stress Test"
    window.color = config.COLOR_BACKGROUND
    window.fps_counter.enabled = True
    
    # 1. Create Player (tests Octahedron mesh + Trail particles)
    player = Player()
    
    # 2. Create Track (Standard)
    track = Track()
    
    # 3. Spawn MANY Obstacles (tests Glow transparency + Mesh load)
    # Normal game has maybe 5-10 active. We'll spawn 50.
    obstacles = []
    print("[TEST] Spawning 50 obstacles with Glow effects...")
    for i in range(50):
        # Random mix of types
        obs_type = random.choice(['low', 'high', 'moving'])
        lane = random.choice([0, 1, 2])
        z_pos = 10 + (i * 5) # Spaced out every 5 units
        
        obs = Obstacle(lane, z_pos, obs_type)
        obstacles.append(obs)
        
    # Text info
    info_text = Text(
        text="Stress Test Running...",
        position=(-0.6, 0.4),
        scale=1.5
    )
    
    # Test state
    start_time = pytime.time()
    duration = 10.0 # Run for 10 seconds
    frame_counts = []
    
    def update():
        # Spin player faster
        player.rotation_y += 100 * time.dt
        
        # Move obstacles to simulate flow
        speed = 30.0 # High speed
        for obs in obstacles:
            obs.z_position -= speed * time.dt
            obs.z = obs.z_position
            
            # Recycle
            if obs.z_position < -20:
                obs.z_position += 250
                obs.z = obs.z_position
        
        # Track Update
        track.update(speed)
        
        # Collect FPS
        if time.dt > 0:
            frame_counts.append(1.0 / time.dt)
            
        elapsed = pytime.time() - start_time
        remaining = duration - elapsed
        info_text.text = f"Stress Test: {remaining:.1f}s remaining\nCurrent FPS: {1.0/time.dt:.1f}"
        
        if elapsed >= duration:
            avg_fps = sum(frame_counts) / len(frame_counts)
            print(f"\n[TEST] COMPLETED")
            print(f"[TEST] Average FPS: {avg_fps:.1f}")
            print(f"[TEST] Min FPS: {min(frame_counts):.1f}")
            print(f"[TEST] Max FPS: {max(frame_counts):.1f}")
            
            if avg_fps > 55:
                print("[TEST] RESULT: PASS (Avg > 55)")
            else:
                print("[TEST] RESULT: FAIL (Avg < 55)")
                
            application.quit()

    app.run()

if __name__ == '__main__':
    run_stress_test()
