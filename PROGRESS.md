# 진행 상황 — NabiCapture (구 ProfectF)

> 세션 간 공유되는 작업 기록. **현재 버전: 0.1.3 (ESC 동작 설정 + 캡쳐 속도 개선)**
> 마지막 업데이트: 2026-04-22

## 4차 피드백 반영 (0.1.3)

- **캡쳐 속도 개선** (`src/app.py`): 단축키 트리거 시 메인 윈도우가 이미 숨겨진 상태면 딜레이 0ms로 즉시 오버레이 표시 (기존 150ms → 0ms). 윈도우가 보이는 상태였을 때만 80ms 대기 (기존 150ms).
- **ESC 동작 설정 추가**:
  - `config/default_config.json` `capture.esc_behavior`: `"tray"` (기본) | `"quit"`
  - `src/app.py` `_on_capture_cancelled()`: config 값에 따라 트레이 잔류 또는 앱 종료
  - `src/ui/settings_dialog.py` 일반 설정 탭에 "캡쳐 중 ESC 동작" 드롭다운 추가

## 3차 피드백 반영 (0.1.2)

- **OptionsBar 신설** (`src/editor/options_bar.py`): 툴 선택 시 두 번째 툴바 행이 해당 도구의 옵션으로 전환
  - 드로잉 도구(펜/형광펜/도형/지우개): ColorPicker + SizeSlider
  - 텍스트: ColorPicker + **QFontComboBox(설치 폰트 전체)** + 크기 SpinBox + 굵게 체크박스 + "입력 ✓" 버튼
  - 모자이크: 블록 크기 콤보
  - 자르기: 안내 텍스트
- **EditorToolbar 슬림화** (`src/editor/toolbar.py`): 도구 버튼 + 실행취소/재실행/저장/복사만 남김
- **`EditorWindow`**: 두 번째 툴바 행 `addToolBarBreak` + OptionsBar 마운트, 시그널 재연결
- **라이트 테마** 에디터 창 + `#OptionsBar` QSS 추가
- **모자이크 `QPoint→QPointF` 타입에러** 최종 수정 (`item.setPos(QPointF(clamped.topLeft()))`)

## 2차 피드백 반영 (0.1.1)

- 프로그램명 **NabiCapture** 로 통일 (`__app_name__`, `build.spec`, 파일명 패턴 `nabi_*`, 에디터 타이틀)
- **실행 즉시 "직접지정" 모드**로 진입. ESC 취소 시 메뉴 윈도우 표시
- **메인 메뉴 라이트 테마** + 단일 행 버튼 바 (직접지정/창/단위영역/전체화면/크기지정/스크롤)
- **트레이 아이콘**: 파란 사각 → 돋보기 모양 (QPainter로 직접 그림)
- **에디터 색상 팔렛트**: 현재 색을 큰 32×32 스와치로 표시 + 선택된 팔레트 버튼에 진한 테두리
- **텍스트 도구 전면 재작성**: 모달 다이얼로그 제거, 캔버스 직접 클릭 → 인라인 `QGraphicsTextItem` 편집. 툴바에 폰트 사이즈 SpinBox / "굵게" 체크박스 / "입력" 확정 버튼 추가 (텍스트 도구 선택 시에만 보임). Ctrl+Enter / 포커스 아웃 / "입력" 버튼 중 어느 것으로도 확정
- **모자이크 크래시 수정**: `release()` 에서 bounds/null 방어 + try/except + 로깅 (`src/editor/tools/mosaic_tool.py`)
- **전역 예외 훅** (`main.py`): 알 수 없는 슬롯 예외가 앱을 죽이지 않고 QMessageBox로 표시

## 완료된 작업 (MVP — 0.1.0)

- **Phase 1 — 부트스트랩**: `main.py`, `paths`, `config_manager`, `default_config.json`, `MainWindow` 셸
- **Phase 2 — 전체화면 캡쳐 + 저장**: `screen_capture.grab*`, `image_io.save_image`
- **Phase 3 — 클립보드/히스토리/편집기**: `clipboard_manager`, `history_manager`, 기본 이미지 표시
- **Phase 4 — 편집기 골조**: `canvas`, `toolbar`, `history_panel`, `status_bar` (W×H)
- **Phase 5 — 펜 도구 + Undo/Redo**: `PenTool`, `QUndoStack` 래퍼
- **Phase 6 — 나머지 편집 도구**: 형광펜, 지우개, 사각/원/화살표/선/말풍선, 텍스트, 자르기, 모자이크
- **Phase 7 — 영역 선택 오버레이**: `RegionSelector` (반투명 + 가이드라인 + 사이즈 라벨)
- **Phase 8 — 전역 단축키**: `HotkeyManager` (`keyboard` 라이브러리 + Qt 시그널 브리지)
- **Phase 9 — 트레이 아이콘**: 트레이 메뉴 + 종료/최소화 옵션
- **Phase 10 — 창/크기지정 캡쳐**: `WindowPicker` (Win32 EnumWindows), `FixedSizeSelector`
- **Phase 11 — 설정 다이얼로그**: 4탭 (일반/캡쳐/저장/단축키) + `HotkeyInput` 녹음 위젯
- **Phase 12 — PyInstaller 스펙**: `build.spec` (one-file, windowed)
- **테스트**: 18개 pytest 전부 통과

## 다음 단계 (Next Step)

### 즉시 실행 가능한 검증
```bash
pip install -r requirements-dev.txt
pytest -v             # 18개 통과 확인
python main.py        # 실제 구동 (Windows 세션)
```

### 2단계 (MVP 이후)
1. **스크롤 캡쳐** — 창 내부 스크롤 자동 감지 + 프레임 스티칭 (가장 어려운 기능, 따로 설계 필요)
2. **확대경(Loupe)**: `RegionSelector` 드래그 중 픽셀 확대 미리보기
3. **아이콘 세트**: `resources/icons/`에 PNG/SVG 추가 + 트레이/툴바에 적용
4. **OCR 기능** (선택): 캡쳐 이미지에서 텍스트 추출
5. **Windows 시작 시 자동 실행** 실제 구현 — 현재 설정만 있음, 레지스트리 Run 키 추가 필요
6. **드래그 & 드롭 저장** — 히스토리 패널 항목을 탐색기로 드래그

### 알려진 미완성 영역
- 트레이 아이콘이 PNG 없이 런타임에 그려지는 플레이스홀더 — 제대로 된 아이콘 파일 추가 필요
- `use_printscreen` 설정은 `ctrl+shift+a` 같은 일반 바인딩과 함께 Region 액션에 중복 등록됨 — 실제로는 둘 다 동작하지만 UX 확인 필요
- 창 캡쳐가 DWM 합성 윈도우(크롬 등)의 보이는 영역만 가져옴. 숨겨진 자식 윈도우 포함은 `PrintWindow` API로 해결 가능
