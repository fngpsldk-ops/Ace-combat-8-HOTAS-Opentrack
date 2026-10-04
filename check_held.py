"""지금 눌린 채로 있는 버튼 확인 (토글 스위치 점검용)."""
import time

from ac8_common import init_pygame, load_config, open_all, pygame

cfg = load_config()
init_pygame()
time.sleep(0.5)
pygame.event.pump()
devs = open_all()
for d in devs:
    held = [b for b in range(d.get_numbuttons()) if d.get_button(b)]
    print(f"{d.get_name()}: 눌린 버튼 {held}")
names = {d.get_guid(): d for d in devs}
for action, b in cfg["buttons"].items():
    d = names.get(cfg["devices"][b["dev"]]["guid"])
    if d and d.get_button(b["button"]):
        print(f"  ⚠ '{action}' 버튼({b['dev']} {b['button']})이 지금 눌린 상태입니다")
pygame.quit()
