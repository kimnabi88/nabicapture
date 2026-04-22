# ProfectF

가벼운 PC용 화면 캡쳐 + 편집 프로그램. ShareX/Greenshot 류 기능, 광고 없음, 포터블.

## 주요 기능

- **캡쳐 모드**: 직접지정(드래그) / 창 / 모니터 / 전체화면 / 크기지정 (+ 스크롤은 2단계 예정)
- **편집 도구**: 펜 / 형광펜 / 사각/원/선/화살표/말풍선 / 텍스트 / 자르기 / 모자이크(블록 사이즈 조절) / 지우개
- **앞으로/뒤로** (Ctrl+Z / Ctrl+Y)
- **우측 캡쳐 히스토리 패널** + 상태바에 이미지 **W × H px** 표시
- **전역 단축키** (PrintScreen 포함 가능)
- **트레이 아이콘** — X 버튼은 최소화 or 종료 선택 가능
- **설정**: 일반/캡쳐/저장/단축키 4탭 — 포맷(PNG/JPG/WebP/BMP), 품질, 저장 폴더, 파일명 패턴
- **자동 클립보드 복사** (옵션)

## 실행 (개발)

```bash
pip install -r requirements-dev.txt
python main.py
pytest -v              # 단위 테스트
```

## .exe 빌드

```bash
pyinstaller build.spec
# 결과: dist/ProfectF.exe (단일 파일, 콘솔 없음)
```

## 포터블 저장

실행 폴더에 자동 생성:
- `config.json` — 기본값과 다른 항목만 저장
- `captures/` — 기본 저장 위치
- `logs/profectf.log` — 실행 로그

설정을 완전히 초기화하려면 `config.json` 삭제.

## 기본 단축키

| 기능 | 기본값 |
|------|-------|
| 직접지정 | `Ctrl+Shift+A` (+ `PrintScreen` 옵션) |
| 창 | `Ctrl+Shift+W` |
| 단위영역 | `Ctrl+Shift+M` |
| 전체화면 | `Ctrl+Shift+F` |
| 크기지정 | `Ctrl+Shift+X` |
| 마지막 반복 | `Ctrl+Shift+R` |

전부 설정에서 재할당 가능.

## 폴더 구조

자세한 구조는 [`C:\Users\Administrator\.claude\plans\pc-federated-pascal.md`](C:\Users\Administrator\.claude\plans\pc-federated-pascal.md) 계획 문서 참고.
