"""슬루 스틱 정지 상태 흔들림 측정 (5초)."""
import time

from ac8_common import find_device, init_pygame, load_config, open_all, pygame

cfg = load_config()
init_pygame()
time.sleep(0.5)
pygame.event.pump()
devs = open_all()
axes = {k: cfg["axes"][k] for k in ("slew_x", "slew_y") if cfg["axes"].get(k)}
lo = {k: 9.0 for k in axes}
hi = {k: -9.0 for k in axes}
end = time.time() + 5
while time.time() < end:
    pygame.event.pump()
    for k, e in axes.items():
        d = find_device(devs, cfg["devices"][e["dev"]])
        v = d.get_axis(e["axis"])
        lo[k], hi[k] = min(lo[k], v), max(hi[k], v)
    time.sleep(0.005)
for k in axes:
    print(f"{k}: 최소 {lo[k]:+.3f} 최대 {hi[k]:+.3f} (데드존 {cfg['settings']['slew_deadzone']})")
pygame.quit()
