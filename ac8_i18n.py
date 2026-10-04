"""화면 표시 문자열 (한국어 / English / 日本語).

언어는 language.txt에 저장한다. 없으면 Windows 표시 언어로 고른다.
"""
import ctypes
import os

HERE = os.path.dirname(os.path.abspath(__file__))
LANG_PATH = os.path.join(HERE, "language.txt")
LANGS = [("ko", "한국어"), ("en", "English"), ("ja", "日本語")]

S = {
    # ---- 공통 / 동작 이름 ----
    "act_gun": ("기관포 / 확인", "Gun / Confirm", "機銃 / 決定"),
    "act_missile": ("미사일 / 취소", "Missile / Cancel", "ミサイル / キャンセル"),
    "act_weapon": ("무기 전환", "Switch weapon", "武装切替"),
    "act_target": ("타겟 전환", "Switch target", "ターゲット切替"),
    "act_boresight": ("보어사이트", "Boresight", "ボアサイト"),
    "act_camera": ("카메라 모드", "Camera mode", "カメラモード"),
    "act_map": ("레이더 / 맵", "Radar / Map", "レーダー / マップ"),
    "act_pause": ("일시정지", "Pause", "ポーズ"),
    "act_autopilot": ("오토파일럿", "Autopilot", "オートパイロット"),
    "act_flare": ("플레어", "Flare", "フレア"),
    "act_highg": ("고G 선회", "High-G turn", "高G旋回"),
    "act_throttle_up": ("가속 (버튼)", "Accelerate (button)", "加速（ボタン）"),
    "act_throttle_down": ("감속 (버튼)", "Decelerate (button)", "減速（ボタン）"),
    "throttle_btn_note": ("↑ 가속/감속 버튼은 스로틀이 없을 때 쓰세요. 스로틀이 있으면 [스로틀] 탭에서 설정하세요.",
                          "↑ Use the accelerate/decelerate buttons only if you have no throttle. "
                          "With a throttle, set it up on the [Throttle] tab.",
                          "↑ 加速/減速ボタンはスロットルが無い場合に使います。スロットルがある場合は[スロットル]タブで設定してください。"),
    "act_head_toggle": ("헤드트래킹 켜기/끄기", "Head tracking on/off", "ヘッドトラッキング オン/オフ"),
    "act_hat": ("무전 / 윙맨 (POV 햇)", "Comms / Wingman (POV hat)", "無線 / 僚機（POVハット）"),
    "xbox_ls": ("LS 클릭", "LS click", "LSクリック"),
    "xbox_rs": ("RS 클릭", "RS click", "RSクリック"),
    "xbox_bridge": ("(브리지 기능)", "(bridge)", "（ブリッジ機能）"),
    "xbox_dpad": ("D-패드", "D-pad", "十字キー"),
    "axis_roll": ("롤", "Roll", "ロール"),
    "axis_pitch": ("피치", "Pitch", "ピッチ"),
    "axis_yaw": ("요 (트위스트)", "Yaw (twist)", "ヨー（ツイスト）"),
    "axis_slew_x": ("카메라 좌우 (슬루)", "Camera left/right (slew)", "カメラ左右（スルー）"),
    "axis_slew_y": ("카메라 상하 (슬루)", "Camera up/down (slew)", "カメラ上下（スルー）"),
    "xbox_lx": ("왼쪽 스틱 X", "Left stick X", "左スティック X"),
    "xbox_ly": ("왼쪽 스틱 Y", "Left stick Y", "左スティック Y"),
    "xbox_rx": ("오른쪽 스틱 X", "Right stick X", "右スティック X"),
    "xbox_ry": ("오른쪽 스틱 Y", "Right stick Y", "右スティック Y"),
    "hint_roll": ("스틱을 오른쪽 끝까지 기울이세요", "Tilt the stick fully RIGHT", "スティックを右いっぱいに倒してください"),
    "hint_pitch": ("스틱을 앞으로 끝까지 미세요", "Push the stick fully FORWARD", "スティックを前いっぱいに倒してください"),
    "hint_yaw": ("손잡이를 오른쪽으로 끝까지 비트세요", "Twist the grip fully RIGHT", "グリップを右いっぱいにひねってください"),
    "hint_slew_x": ("슬루 스틱을 오른쪽으로 미세요", "Push the slew stick RIGHT", "スルースティックを右に倒してください"),
    "hint_slew_y": ("슬루 스틱을 위(앞)로 미세요", "Push the slew stick UP", "スルースティックを上に倒してください"),

    # ---- 설정 창 ----
    "title": ("AC8 HOTAS 설정", "AC8 HOTAS Settings", "AC8 HOTAS 設定"),
    "language": ("언어", "Language", "言語"),
    "tab_buttons": ("버튼", "Buttons", "ボタン"),
    "tab_axes": ("비행 축", "Flight axes", "飛行軸"),
    "tab_throttle": ("스로틀", "Throttle", "スロットル"),
    "tab_head": ("헤드트래킹 · 감도", "Head tracking · Sensitivity", "ヘッドトラッキング・感度"),
    "save": ("저장", "Save", "保存"),
    "rescan": ("장비 다시 찾기", "Rescan devices", "デバイス再検索"),
    "col_xbox": ("Xbox 패드", "Xbox pad", "Xboxパッド"),
    "col_action": ("게임 동작", "Game action", "ゲーム操作"),
    "col_input": ("지정된 물리 입력", "Assigned input", "割り当て入力"),
    "col_axis": ("지정된 물리 축", "Assigned axis", "割り当て軸"),
    "col_value": ("현재 값", "Live value", "現在値"),
    "col_invert": ("반전", "Invert", "反転"),
    "col_lever": ("레버", "Lever", "レバー"),
    "assign": ("입력", "Assign", "割当"),
    "clear": ("해제", "Clear", "解除"),
    "devices_found": ("장비 {n}개 인식: {names}", "{n} device(s) found: {names}", "デバイス{n}台を認識: {names}"),
    "no_devices": ("⚠ 인식된 장비가 없습니다. 장비를 연결하고 [장비 다시 찾기]를 누르세요. "
                   "HidHide를 쓰고 있다면 HidHide의 Applications 목록에 python.exe를 추가하세요.",
                   "⚠ No devices found. Connect them and click [Rescan devices]. "
                   "If you use HidHide, add python.exe to HidHide's Applications list.",
                   "⚠ デバイスが見つかりません。接続して[デバイス再検索]を押してください。"
                   "HidHide を使っている場合は、HidHide の Applications に python.exe を追加してください。"),
    "br_same_device": ("⚠ 설정 장비 '{a}', '{b}' 두 개가 같은 실제 장비({name})로 잡혔습니다. 설정 창에서 다시 지정하세요.",
                       "⚠ '{a}' and '{b}' resolved to the same device ({name}). Reassign them in Settings.",
                       "⚠ '{a}' と '{b}' が同じデバイス（{name}）になっています。設定画面で割り当て直してください。"),
    "start_hint": ("[입력]을 누르고 쓸 버튼/축을 조작하세요.", "Click [Assign], then press/move the control you want.",
                   "[割当]を押してから、使いたいボタン/軸を操作してください。"),
    "cap_button": ("▶ 버튼을 누르세요", "▶ Press a button", "▶ ボタンを押してください"),
    "cap_hat": ("▶ 햇을 아무 방향으로 누르세요", "▶ Push the hat in any direction", "▶ ハットを任意の方向に押してください"),
    "cap_lever": ("▶ 레버를 앞으로 끝까지 미세요", "▶ Push the lever fully forward", "▶ レバーを一番前まで押してください"),
    "esc_cancel": ("(Esc 취소)", "(Esc to cancel)", "（Escでキャンセル）"),
    "cancelled": ("입력 취소", "Cancelled", "キャンセルしました"),
    "assigned": ("지정: {what}", "Assigned: {what}", "割り当て: {what}"),
    "dup_warn": ("  (⚠ '{other}'에도 지정됨)", "  (⚠ also assigned to '{other}')", "  （⚠ '{other}'にも割り当て済み）"),
    "invert_state": ("반전 {state}", "invert {state}", "反転 {state}"),
    "on": ("켬", "on", "オン"),
    "off": ("끔", "off", "オフ"),
    "press_save": (" — [저장]을 누르면 반영됩니다.", " — click [Save] to apply.", " — [保存]で反映されます。"),
    "dirty": ("변경됨 — [저장]을 누르면 브리지에 반영됩니다.", "Changed — click [Save] to apply to the bridge.",
              "変更あり — [保存]でブリッジに反映されます。"),
    "saved": ("저장됨 — 실행 중인 브리지에 1초 안에 반영됩니다.", "Saved — a running bridge picks it up within 1 second.",
              "保存しました — 実行中のブリッジに1秒以内に反映されます。"),
    "save_fail": ("저장 실패", "Save failed", "保存失敗"),
    "bad_number": ("숫자 칸에 잘못된 값이 있습니다.", "One of the number fields is invalid.", "数値欄に不正な値があります。"),
    "missing": ("필수 항목이 지정되지 않았습니다: {items}", "Required items are not assigned: {items}",
                "必須項目が未割り当てです: {items}"),
    "close": ("닫기", "Close", "閉じる"),
    "close_unsaved": ("저장하지 않은 변경이 있습니다. 그냥 닫을까요?", "You have unsaved changes. Close anyway?",
                      "保存していない変更があります。閉じますか？"),
    "axes_hint": ("※ [입력]을 누른 뒤 안내된 방향으로 끝까지 움직이면 그 방향이 +로 저장됩니다.",
                  "※ After [Assign], move fully in the shown direction; that direction becomes +.",
                  "※ [割当]の後、表示された方向に最後まで動かすと、その方向が＋になります。"),
    "lever_0": ("왼쪽 레버", "Left lever", "左レバー"),
    "lever_1": ("오른쪽 레버", "Right lever", "右レバー"),
    "lever_hint": ("※ 레버를 맨 뒤에 둔 채 [입력] → 앞으로 끝까지 미세요. 두 레버를 지정하면 평균값을 씁니다.\n"
                   "   스로틀이 없으면 비워 두고, 버튼 탭의 '가속/감속 (버튼)'을 쓰세요.",
                   "※ With the lever fully aft, click [Assign] and push it fully forward. Two levers are averaged.\n"
                   "   No throttle? Leave this empty and use 'Accelerate/Decelerate (button)' on the Buttons tab.",
                   "※ レバーを一番後ろにした状態で[割当] → 一番前まで押してください。2本割り当てると平均値を使います。\n"
                   "   スロットルが無い場合は空欄のままにし、ボタンタブの「加速/減速（ボタン）」を使ってください。"),
    "cal_frame": ("보정 (레버를 해당 위치에 두고 버튼을 누르세요)", "Calibration (put the lever there, then click)",
                  "キャリブレーション（レバーをその位置に置いてクリック）"),
    "cal_aft": ("지금 위치 = 맨 뒤 (최대 감속)", "Current = full aft (max decel)", "現在位置 = 最後方（最大減速）"),
    "cal_fwd": ("지금 위치 = 맨 앞 (최대 가속)", "Current = full forward (max accel)", "現在位置 = 最前方（最大加速）"),
    "cal_neutral": ("지금 위치 = 중립 (순항)", "Current = neutral (cruise)", "現在位置 = ニュートラル（巡航）"),
    "cal_center": ("중립 = 정중앙", "Neutral = exact middle", "ニュートラル = 中央"),
    "cal_values": ("맨 뒤 {aft}   중립 {neutral}   맨 앞 {fwd}", "Aft {aft}   Neutral {neutral}   Forward {fwd}",
                   "最後方 {aft}   ニュートラル {neutral}   最前方 {fwd}"),
    "neutral_width": ("중립 구간 폭 (전체의 ±%)", "Neutral band (± % of travel)", "ニュートラル幅（全体の±%）"),
    "output_frame": ("현재 출력", "Current output", "現在の出力"),
    "lever_none": ("레버 미지정", "No lever assigned", "レバー未割り当て"),
    "lever_out": ("레버 값 {raw}  →  LT {lt}%   RT {rt}%", "Lever {raw}  →  LT {lt}%   RT {rt}%",
                  "レバー値 {raw}  →  LT {lt}%   RT {rt}%"),
    "lt_label": ("LT 감속", "LT decel", "LT 減速"),
    "rt_label": ("RT 가속", "RT accel", "RT 加速"),
    "lever_first": ("먼저 레버 축을 지정하세요.", "Assign a lever axis first.", "先にレバー軸を割り当ててください。"),
    "ht_enable": ("헤드트래킹 사용 (OpenTrack freetrack 2.0 출력)", "Use head tracking (OpenTrack freetrack 2.0 output)",
                  "ヘッドトラッキングを使用（OpenTrack freetrack 2.0 出力）"),
    "inv_x": ("좌우 반전", "Invert left/right", "左右反転"),
    "inv_y": ("상하 반전", "Invert up/down", "上下反転"),
    "ht_note": ("※ 헤드트래킹 켜기/끄기는 브리지를 다시 실행해야 적용됩니다. 나머지는 저장 즉시 반영.",
                "※ Turning head tracking on/off needs a bridge restart. Everything else applies on save.",
                "※ ヘッドトラッキングのオン/オフはブリッジの再起動が必要です。その他は保存時に即反映。"),
    "desc_button": ("{dev}  버튼 {n}", "{dev}  button {n}", "{dev}  ボタン {n}"),
    "desc_axis": ("{dev}  축 {n}", "{dev}  axis {n}", "{dev}  軸 {n}"),
    "desc_hat": ("{dev}  햇 {n}", "{dev}  hat {n}", "{dev}  ハット {n}"),
    "n_roll_dz": ("롤 데드존", "Roll deadzone", "ロール デッドゾーン"),
    "n_pitch_dz": ("피치 데드존", "Pitch deadzone", "ピッチ デッドゾーン"),
    "n_yaw_th": ("요 작동 기준 (트위스트 비율)", "Yaw trigger point (twist ratio)", "ヨー作動しきい値（ツイスト比率）"),
    "n_slew_dz": ("슬루 데드존", "Slew deadzone", "スルー デッドゾーン"),
    "n_yaw_fs": ("헤드 좌우 최대 각도 (°, 작을수록 민감)", "Head yaw full-scale angle (°, smaller = more sensitive)",
                 "頭の左右 最大角度（°、小さいほど敏感）"),
    "n_pitch_fs": ("헤드 상하 최대 각도 (°, 작을수록 민감)", "Head pitch full-scale angle (°, smaller = more sensitive)",
                   "頭の上下 最大角度（°、小さいほど敏感）"),
    "n_head_dz": ("헤드 데드존 (°)", "Head deadzone (°)", "ヘッド デッドゾーン（°）"),
    "n_head_adz": ("헤드 안티 데드존 (첫 출력 크기)", "Head anti-deadzone (initial output)", "ヘッド アンチデッドゾーン（初期出力）"),
    "n_head_exp": ("헤드 커브 (1=직선, 클수록 중앙 둔함)", "Head curve (1 = linear, higher = softer center)",
                   "ヘッドカーブ（1=直線、大きいほど中央が鈍い）"),
    "n_lead": ("선행 입력 (초)", "Lead (seconds)", "先行入力（秒）"),
    "n_lead_min": ("선행 입력 시작 속도 (°/s)", "Lead start speed (°/s)", "先行入力の開始速度（°/s）"),
    "n_smooth": ("스무딩 (초, 클수록 부드럽고 느림)", "Smoothing (s, higher = smoother but slower)",
                 "スムージング（秒、大きいほど滑らかで遅い）"),

    # ---- 설치 ----
    "inst_done": ("설치 완료. 'ViGEm Bus Driver' 새 설치 창이 떴다면 끝까지 진행하세요 (재부팅 요청 시 재부팅).\n"
                  "다음: 장비를 연결하고 1_Settings.bat 실행",
                  "Install complete. If a 'ViGEm Bus Driver' setup window appeared, finish it (reboot if asked).\n"
                  "Next: connect your devices and run 1_Settings.bat",
                  "インストール完了。「ViGEm Bus Driver」のセットアップ画面が出た場合は最後まで進めてください（再起動を求められたら再起動）。\n"
                  "次へ: デバイスを接続して 1_Settings.bat を実行"),

    # ---- 브리지 콘솔 ----
    "br_title": ("=== AC8 HOTAS 브리지 ===", "=== AC8 HOTAS Bridge ===", "=== AC8 HOTAS ブリッジ ==="),
    "br_no_config": ("config.json이 없습니다. 먼저 1_Settings.bat으로 설정하세요.",
                     "config.json not found. Run 1_Settings.bat first.",
                     "config.json がありません。先に 1_Settings.bat で設定してください。"),
    "br_no_vigem": ("가상 Xbox 패드를 만들 수 없습니다. ViGEmBus 드라이버를 설치하세요:\n  {url}",
                    "Cannot create the virtual Xbox pad. Install the ViGEmBus driver:\n  {url}",
                    "仮想Xboxパッドを作成できません。ViGEmBusドライバーをインストールしてください:\n  {url}"),
    "br_wait_ft": ("OpenTrack 수신 대기 (freetrack 2.0 공유 메모리)", "Waiting for OpenTrack (freetrack 2.0 shared memory)",
                   "OpenTrack 待機中（freetrack 2.0 共有メモリ）"),
    "br_wait_udp": ("OpenTrack 수신 대기 (UDP): 127.0.0.1:{port}", "Waiting for OpenTrack (UDP): 127.0.0.1:{port}",
                    "OpenTrack 待機中（UDP）: 127.0.0.1:{port}"),
    "br_running": ("실행 중. 종료: Ctrl+C  (설정 창에서 저장하면 바로 반영)",
                   "Running. Quit: Ctrl+C  (changes saved in Settings apply immediately)",
                   "実行中。終了: Ctrl+C（設定画面で保存すると即反映）"),
    "br_not_connected": ("(연결 안 됨)", "(not connected)", "（未接続）"),
    "br_lost": ("장비 연결이 끊겼습니다. 입력을 중립으로 돌렸습니다.", "A device was disconnected. Outputs set to neutral.",
                "デバイスが切断されました。入力をニュートラルに戻しました。"),
    "br_searching": ("장비 다시 찾는 중...", "Searching for devices...", "デバイスを再検索中..."),
    "br_connected": ("장비 연결됨.", "Devices connected.", "デバイス接続済み。"),
    "br_reloaded": ("설정 다시 읽음.", "Settings reloaded.", "設定を再読み込みしました。"),
    "br_reload_fail": ("설정 읽기 실패(다음에 재시도): {e}", "Failed to read settings (will retry): {e}",
                       "設定の読み込みに失敗（再試行します）: {e}"),
    "br_head_on": ("헤드트래킹 켜짐", "Head tracking ON", "ヘッドトラッキング オン"),
    "br_head_off": ("헤드트래킹 꺼짐", "Head tracking OFF", "ヘッドトラッキング オフ"),
    "br_exit": ("종료: 가상 패드를 중립으로 돌리고 제거했습니다.", "Exited: virtual pad neutralized and removed.",
                "終了: 仮想パッドをニュートラルに戻して削除しました。"),
    "st_head_none": ("헤드없음", "noHead", "ヘッド無し"),
    "st_drops": ("끊김", "drops", "途切れ"),
    "st_rx": ("수신", "rx", "受信"),
    "st_angle": ("각도", "ang", "角度"),
}

_IDX = {code: i for i, (code, _) in enumerate(LANGS)}


def _detect():
    try:
        lid = ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF
        return {0x12: "ko", 0x11: "ja"}.get(lid, "en")
    except Exception:
        return "en"


def get_lang():
    try:
        with open(LANG_PATH, encoding="utf-8") as f:
            code = f.read().strip()
        if code in _IDX:
            return code
    except OSError:
        pass
    return _detect()


def set_lang(code):
    with open(LANG_PATH, "w", encoding="utf-8") as f:
        f.write(code)
    global _lang
    _lang = code


_lang = get_lang()


def T(key, **kw):
    text = S[key][_IDX[_lang]] if key in S else key
    return text.format(**kw) if kw else text
