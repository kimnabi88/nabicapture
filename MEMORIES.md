# 기억해야 할 항목 — NabiCapture

## 앱 런칭 플로우 (0.1.1 이후)

- `AppController.start()` 는 **MainWindow 를 먼저 show 하지 않음**. 대신 `QTimer.singleShot(100, ...)` 로 곧바로 region 캡쳐 오버레이를 띄움.
- 사용자가 ESC 로 취소하면 `_on_capture_cancelled` → `_show_main()` 이 메뉴를 처음으로 노출.
- **주의**: 이 순서를 바꾸면 "프로그램 켜자마자 바로 캡쳐" UX 가 깨짐. 메뉴부터 보고 싶으면 설정 플래그를 추가해 분기할 것.

## 메인 메뉴 라이트 테마 오버라이드

- 기본 `main.qss` 는 다크. 메뉴만 라이트로 보이게 하려고 `MainWindow.setObjectName("MainMenu")` + `#MainMenu`, `#MenuAction`, `#MenuSettings` 등 objectName 셀렉터로 스타일 오버라이드.
- 에디터는 그대로 다크 유지. 새 라이트 위젯 추가 시 반드시 objectName 부여 후 QSS 에 셀렉터를 추가.

## OptionsBar — 두 번째 툴바 행 (0.1.2~)

- `src/editor/options_bar.py`: `QToolBar` 하위 클래스, 내부에 `QStackedWidget` 4개 페이지.
- **페이지 매핑**: 0=드로잉(펜/형광펜/도형/지우개), 1=텍스트, 2=모자이크, 3=자르기.
- `set_tool(tool_id)` 호출 시 스택 페이지 전환. `EditorWindow._on_tool_selected` 에서 호출.
- `EditorToolbar` 는 이제 도구 버튼 + undo/redo/save/copy 만. 색상/굵기/폰트 관련 시그널 없음.
- 새 도구 추가 시 `_TOOL_PAGE` 딕셔너리에 매핑 추가하고 필요하면 새 페이지 `addWidget` 할 것.

## 텍스트 도구 — 인라인 편집 (중요)

- `QGraphicsTextItem` + `TextInteractionFlag.TextEditorInteraction` 으로 씬 위에서 직접 타이핑.
- 확정 시점은 세 가지: (1) Ctrl+Enter, (2) 포커스 아웃, (3) 툴바 "입력" 버튼.
- 확정될 때 `_commit_active()` 가 씬에서 아이템을 잠시 제거한 뒤 `AddItemCommand` 로 push → Undo/Redo 스택에 올라감. **편집 중 상태는 undo 스택에 남기지 않는다** (취소/이탈 시 깔끔히 사라짐).
- 다른 도구로 전환하면 `deactivate()` → `commit_current()` 로 자동 확정. 빈 텍스트면 그냥 제거.

## 모자이크 방어 코드 (크래시 이력)

- `mosaic_tool.py:release` 에서 드래그가 씬 밖이거나 너무 작은 영역을 지나갈 때 `QPixmap.copy()` / `scaled()` 가 null 픽스맵 → `QGraphicsPixmapItem` 생성 과정에서 C++ 크래시 → 앱 강제 종료하던 이슈 있었음.
- 현재는 `clamped.width()<2` / `region.isNull()` / `tiny.isNull()` / `mosaic.isNull()` 체크 + 전체 try/except + `logger.exception()` 로 방어. 신규 변경 시 이 가드들을 제거하지 말 것.

## 전역 예외 훅

- `main._install_exception_hook()` 가 `sys.excepthook` 교체. Qt 슬롯 안의 미처리 예외도 로그 + `QMessageBox.critical` 로 사용자에게 보임.
- 디버깅 시 **예외가 조용히 삼켜지지 않도록** 이 훅을 우회하지 말 것 (특히 테스트 러너에서).

---
(이전 ProfectF 메모리)



> 세션 간 버그 원인, 라이브러리 선택 이유, 주의 코드 영역을 기록.

---

## 라이브러리 선택 이유

- **PyQt6 (vs PySide6)** — 동일 API, 라이선스 차이. PyQt6는 GPL/상용이지만 개인/사내 배포에 충분.
- **mss (vs Pillow.ImageGrab)** — mss가 2-3배 빠르고 멀티 모니터 좌표가 단순. Pillow는 이미지 저장용으로만.
- **keyboard (vs pynput / Win32 RegisterHotKey)** — 단축키 문자열 포맷이 가장 이식성 있고 등록 실패시 예외 처리가 명확.
- **pywin32** — 창 목록(EnumWindows), 클립보드 DIB 접근용. 표준 라이브러리로는 대체 불가.

## 좌표계 주의 (고DPI)

- **mss는 항상 물리 픽셀 좌표**를 씀
- **Qt 위젯 좌표는 논리 픽셀** (devicePixelRatio 적용 후)
- `RegionSelector` / `FixedSizeSelector` / `WindowPicker`는 모두 이 변환을 명시적으로 처리하고 있음. 새 오버레이 추가 시 `QGuiApplication.primaryScreen().devicePixelRatio()`로 변환 로직 꼭 포함할 것.
- 멀티 모니터에서 모니터마다 DPR이 다를 수 있음 — 현재는 primary DPR만 쓰는 한계. 이상 동작 시 `QScreen::devicePixelRatio()`를 위젯이 속한 스크린 기준으로 다시 계산해야 함.

## QImage ↔ mss 바이트 순서

- mss는 BGRA 바이트 순서로 리턴
- **little-endian Windows에서 `QImage.Format_ARGB32`는 메모리상 BGRA** 이므로 **swap 없이** 그대로 해석하면 색상이 정확함
- 과거에 `rgbSwapped()`를 호출했더니 R/B가 뒤집혔던 버그가 있었음. 다시 추가하지 말 것. (`src/capture/screen_capture.py:grab`)

## PyQt6 enum 인자는 정수 리터럴 금지

- PyQt6는 PyQt5와 달리 enum 타입을 엄격히 체크함 → `QImage.scaled(w, h, aspectRatioMode=1, transformMode=1)` 같은 호출은 **런타임 TypeError**
- 반드시 `Qt.AspectRatioMode.KeepAspectRatio`, `Qt.TransformationMode.SmoothTransformation` 형태로 명시
- 이전에 `history_manager.py:thumbnail`에서 첫 캡쳐 시 TypeError로 트레이스백 나왔음. 새 enum 인자 추가 시 항상 full-qualified 이름 사용.

## QShortcut (PyQt6)

- PyQt5의 `QShortcut(keys, parent, activated=slot)` 생성자 스타일은 PyQt6에서 안정적이지 않음 → **반드시 두 줄로 나눠서** `shortcut.activated.connect(slot)` 호출할 것.

## QSystemTrayIcon 가용성

- 오프스크린(Qt `offscreen` platform) 환경에서는 `QSystemTrayIcon.isSystemTrayAvailable()`이 False → 우리 코드는 이 경우 `self.tray = None`으로 그레이스풀하게 처리. 트레이 관련 코드 추가 시 반드시 None 체크 유지.

## 편집기 단일 이미지 설계

- 현재 `EditorWindow`는 하나의 `Canvas` + 하나의 `QUndoStack`을 공유. 히스토리에서 항목을 바꾸면 scene이 통째로 교체됨 → **이전 이미지의 편집 상태는 유지되지 않음**.
- 다음 리팩토링: `CaptureItem`별로 `QUndoStack`을 보관하고 전환 시 스왑. 당장 필요하면 여기에 이슈 추가.

## 하드코딩 금지 — config 경로 일관성

- 색상 팔레트, 펜 굵기 옵션, 모자이크 블록 사이즈 등은 전부 `config/default_config.json`의 `editor` 섹션에서 온다. 하드코딩된 리스트를 보면 즉시 config로 빼낼 것 (CLAUDE.md 규칙).
- 단 CSS/QSS 색상값은 스타일시트(`resources/styles/main.qss`)에 둠 — 이건 테마 파일이라 config와 분리.

## 포터블 모드 가정

- 실행 폴더에 `config.json`, `captures/`, `logs/`가 생성됨 (`src/utils/paths.py`)
- PyInstaller onefile일 때 `sys._MEIPASS`는 임시 추출 폴더, `sys.executable`의 부모가 진짜 실행 폴더 — `paths.app_root()` 와 `paths.resource_root()`가 이 둘을 분리해서 처리하고 있으니 섞지 말 것.

## keyboard 라이브러리 권한

- Windows에서 PrintScreen 후킹/억제는 **관리자 권한이 없으면 실패**할 수 있음 → `HotkeyManager._register`에서 예외 잡고 `error` 시그널로 전달. 설정 UI에서 안내 예정.
