# Design

## Source of truth
- Status: Active
- Last refreshed: 2026-09-15
- Primary product surfaces: 로그인, 회원가입, 내 메모, 메모 작성/상세/수정, 관리자 회원 목록
- Evidence reviewed: `app.py`의 인라인 HTML, `README.md`; 별도 디자인 자산·CSS·스크린샷 없음

## Brand
- Personality: 차분하고 신뢰감 있으며 개인 기록에 집중하는 서비스
- Trust signals: 현재 로그인 상태, 일관된 버튼/폼, 읽기 쉬운 날짜와 권한 표기
- Avoid: 특정 포털의 로고·명칭·자산 또는 픽셀 단위 복제

## Product goals
- Goals: 로그인 사용자가 자신의 메모를 빠르게 읽고 작성·관리하도록 지원
- Non-goals: 검색 엔진, 뉴스 포털, 소셜 피드 구현
- Success signals: 주요 동작이 한 화면에 명확히 보이고, 모바일에서도 작성과 읽기가 편함

## Personas and jobs
- Primary personas: 개인 메모 사용자와 전체 회원을 확인하는 관리자
- User jobs: 메모 작성, 내 메모 탐색·수정·삭제, 관리자의 회원 확인
- Key contexts of use: 데스크톱과 모바일 브라우저의 짧은 기록·조회 작업

## Information architecture
- Primary navigation: 홈(내 메모), 새 메모 작성, 관리자 페이지(관리자만), 로그아웃
- Core routes/screens: `/`, `/memos/new`, `/memos/<id>`, `/memos/<id>/edit`, `/admin/users`, `/login`, `/register`
- Content hierarchy: 서비스 헤더 → 페이지 제목/주요 작업 → 메모·폼·표 데이터

## Design principles
- Principle 1: 검정 본문과 파란 포인트 컬러로 주요 행동을 빠르게 식별시킨다.
- Principle 2: 카드와 일정한 여백으로 메모·폼·관리 데이터를 분리한다.
- Tradeoffs: 포털풍의 친숙한 밀도는 차용하되, 실제 검색·뉴스 기능을 흉내 내지 않는다.

## Visual language
- Color: 검정 본문(`#111827`), 파란 포인트(`#1d4ed8`), 옅은 푸른 회색 배경과 경계
- Typography: 시스템 한글 산세리프, 제목은 굵고 본문은 여유 있는 줄간격
- Spacing/layout rhythm: 8px 기반 간격, 중앙 최대 폭 920px
- Shape/radius/elevation: 12px 둥근 카드, 약한 그림자
- Motion: 짧고 절제된 hover/focus 전환
- Imagery/iconography: 별도 브랜드 이미지 없이 문자·간단한 기호만 사용

## Components
- Existing components to reuse: Flask 인라인 템플릿의 표준 링크, 폼, 버튼
- New/changed components: 앱 헤더, 카드 컨테이너, 메모 목록 카드, 폼 필드, 알림, 데이터 표
- Variants and states: 기본/hover/focus 버튼, 빈 메모 목록, 성공·오류 알림
- Token/component ownership: `app.py`의 `BASE_HTML` CSS가 공통 스타일을 소유

## Accessibility
- Target standard: 실용적인 WCAG 2.1 AA 수준의 대비·포커스
- Keyboard/focus behavior: 모든 링크·입력·버튼에 눈에 보이는 focus 표시
- Contrast/readability: 본문과 보조 텍스트 대비, 최소 16px 본문
- Screen-reader semantics: 제목, label, table heading, 버튼의 기본 의미론 유지
- Reduced motion and sensory considerations: 비필수 애니메이션 없음

## Responsive behavior
- Supported breakpoints/devices: 360px 이상의 모바일 및 데스크톱
- Layout adaptations: 작은 화면에서는 헤더와 주요 작업을 세로로 정렬, 카드 여백 축소
- Touch/hover differences: 터치 가능한 요소의 충분한 높이와 hover 의존 없는 동작

## Interaction states
- Loading: 서버 렌더링 기반이므로 별도 로딩 UI 없음
- Empty: 메모가 없을 때 작성 유도 문구와 버튼 표시
- Error: Flask flash 메시지로 입력 오류 표시
- Success: 저장·수정·삭제 후 flash 메시지 표시
- Disabled: 현재 필요한 비활성 상태 없음
- Offline/slow network, if applicable: 브라우저 기본 제출 동작 사용

## Content voice
- Tone: 짧고 친절하며 행동 중심
- Terminology: 메모, 내 메모, 새 메모, 관리자 페이지
- Microcopy rules: 버튼은 동사 중심으로, 오류는 해결 방법을 함께 표시

## Implementation constraints
- Framework/styling system: Flask, 단일 `app.py`, 외부 CSS·JS·이미지 의존성 없음
- Design-token constraints: 공통 CSS 변수는 `BASE_HTML` 안에만 둠
- Performance constraints: 외부 폰트나 자산 요청 없음
- Compatibility constraints: 현대 브라우저의 표준 CSS 사용
- Test/screenshot expectations: 인증·권한·CRUD 회귀 테스트 후 데스크톱/모바일 폭에서 기본 렌더링 확인

## Open questions
- [ ] 나중에 메모 검색·태그 기능을 추가할지 결정 필요
