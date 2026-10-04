"""연결된 조이스틱 장비 목록 출력 (조작 불필요)."""
import os
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

pygame.init()
pygame.joystick.init()
for i in range(pygame.joystick.get_count()):
    d = pygame.joystick.Joystick(i)
    d.init()
    pygame.event.pump()
    axes = [round(d.get_axis(a), 3) for a in range(d.get_numaxes())]
    print(f"[{i}] {d.get_name()}")
    print(f"    GUID={d.get_guid()} axes={d.get_numaxes()} buttons={d.get_numbuttons()} hats={d.get_numhats()}")
    print(f"    axis values={axes}")
pygame.quit()
