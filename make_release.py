"""배포용 zip 만들기: python make_release.py

버전은 ac8_common.py의 VERSION을 쓴다(새 버전을 낼 때는 그 값만 올린다).
개인 설정(config.json, language.txt)과 진단 스크립트는 넣지 않는다.
결과: dist/AC8_HOTAS_Bridge_v<버전>.zip (zip 안 최상위 폴더도 같은 이름)
"""
import os
import re
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = ["ac8_common.py", "ac8_bridge.py", "ac8_config.py", "ac8_i18n.py"]
EXTRA_DIR = os.path.join(HERE, "release_files")


def read_version():
    with open(os.path.join(HERE, "ac8_common.py"), encoding="utf-8") as f:
        return re.search(r'^VERSION = "([^"]+)"', f.read(), re.M).group(1)


def main():
    version = read_version()
    name = f"AC8_HOTAS_Bridge_v{version}"
    out_dir = os.path.join(HERE, "dist")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, name + ".zip")
    files = [(os.path.join(HERE, f), f) for f in CODE]
    files.append((os.path.join(HERE, "LICENSE"), "LICENSE.txt"))  # GitHub 인식용으로 루트에 둔 것을 zip에 함께
    files += [(os.path.join(EXTRA_DIR, f), f) for f in sorted(os.listdir(EXTRA_DIR))]
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for src, arc in files:
            if arc.endswith(".bat"):
                # cmd는 LF 줄바꿈 bat를 잘못 읽는 경우가 있어 CRLF로 맞춘다
                with open(src, "rb") as f:
                    data = f.read().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
                z.writestr(f"{name}/{arc}", data)
            else:
                z.write(src, f"{name}/{arc}")
            print("  +", arc)
    print(f"→ {out}")


if __name__ == "__main__":
    main()
