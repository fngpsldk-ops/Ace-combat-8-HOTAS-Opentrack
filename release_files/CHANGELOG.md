# Changelog / 변경 내역 / 変更履歴

## v1.02 (2026-10-04)
- EN: README/Nexus: new section for devices that AC8 reads directly (e.g. Thrustmaster TCA/TWCS), which caused mixed inputs. Fix with HidHide (step-by-step guide).
- EN: Settings window shows a HidHide hint when no devices are found. The bridge warns when two configured devices resolve to the same physical device.
- KO: AC8이 직접 인식하는 장비(예: Thrustmaster TCA/TWCS) 때문에 입력이 섞이는 문제 → README·Nexus에 HidHide 설정 절 추가(단계별 안내).
- KO: 설정 창에서 장비가 0개일 때 HidHide 안내 표시. 두 설정 장비가 같은 실제 장비로 잡히면 브리지가 경고.
- JA: AC8 が直接認識するデバイス（例：Thrustmaster TCA/TWCS）で入力が混ざる問題 → README・Nexus に HidHide 設定の節を追加（手順付き）。
- JA: デバイスが0台のとき設定画面に HidHide の案内を表示。2つの設定デバイスが同じ実デバイスになった場合はブリッジが警告。

## v1.01 (2026-10-04)
- EN: Fixed install failure on Python 3.14 ("Failed to build 'pygame'"). Switched pygame 2.6.1 to the compatible pygame-ce 2.5.8. 0_Install.bat removes an old pygame first.
- EN: Device matching no longer breaks when the SDL version changes the device GUID.
- EN: Install notes for the ViGEmBus "Change / Repair / Remove" screen (click Cancel), manual install and uninstall steps in the READMEs.
- KO: Python 3.14에서 설치가 실패하던 문제 수정("Failed to build 'pygame'"). pygame 2.6.1 → 호환판 pygame-ce 2.5.8. 0_Install.bat이 예전 pygame을 먼저 제거합니다.
- KO: SDL 버전에 따라 장비 GUID가 바뀌어도 장비를 찾도록 개선.
- KO: README에 ViGEmBus "Change / Repair / Remove" 화면 대처(Cancel), 수동 설치, 제거 방법 추가.
- JA: Python 3.14 でインストールに失敗する問題を修正（「Failed to build 'pygame'」）。pygame 2.6.1 → 互換版 pygame-ce 2.5.8。0_Install.bat が以前の pygame を先に削除します。
- JA: SDL のバージョンでデバイス GUID が変わってもデバイスを見つけられるよう改善。
- JA: README に ViGEmBus「Change / Repair / Remove」画面の対処（Cancel）、手動インストール、アンインストール手順を追加。

## v1.00 (2026-10-04)
- First release / 첫 배포 / 初回リリース
