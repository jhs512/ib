---
name: setup-gcp
description: "Infinite Brain의 Google Sheets 미러에 필요한 재사용 가능한 Google Cloud 자격증명을 프로비저닝한다 — GCP 프로젝트(기본 `infinite-brain`), Sheets + Drive API 활성화, 서비스 계정, 다운로드한 JSON 키 — 그리고 모든 볼트에서 재사용하도록 `~/.config/ib/sheets-sync.env` 에 저장한다. 설계상 멱등: 기존 프로젝트 / 서비스 계정 / 키가 있으면 중복 생성하지 않고 재사용한다(이 스킬은 옛 설정이 실행할 때마다 두 번째 GCP 프로젝트를 만들던 문제 때문에 분리됐다). Google 계정당 1회만 실행하면 되고, 이후 `setup-sheets-sync` 가 저장된 자격증명을 재사용한다. 브라우저 자동화(예: Claude in Chrome)는 하드 전제다 — 스킬은 맨 처음 활성화 여부를 확인하고 꺼져 있으면 중간까지 진행하지 않고 즉시 중단한다. `gcloud` CLI는 설치돼 있으면 결정적 단계를 위한 선택적 가속기일 뿐이다."
disable-model-invocation: true
---

# ib Sheets 미러용 Google Cloud 자격증명 설정

이 스킬은 **Google 계정당 1회**, 모든 볼트의 Google Sheets 미러가 공유하는 자격증명을 프로비저닝한다:

- **GCP 프로젝트**(기본 이름/슬러그 `infinite-brain`),
- 그 프로젝트에 활성화된 **Google Sheets API** 와 **Google Drive API**,
- **서비스 계정**(기본 `ib-sheets-sync`),
- 그 서비스 계정의 **JSON 키**, 레포 밖에 저장.

그런 다음 모든 것을 `~/.config/ib/sheets-sync.env` 에 기록해 `setup-sheets-sync`(및 이후 볼트)가 재사용하게 한다.

## 단 하나의 규칙: 확인 후 생성 — 절대 중복 금지

아래 각 리소스는 **확인 후 생성** 방식이다. 이미 있으면 재사용한다. 이 스킬이 `setup-sheets-sync` 에서 분리된 이유 자체가, 옛 흐름이 볼트마다 "GCP 프로젝트 생성"을 실행해 사용자에게 중복 프로젝트가 두세 개씩 남았기 때문이다. 사용 가능한 프로젝트·서비스 계정·키가 이미 있으면 두 번째를 만들지 말 것. 새 키는 디스크에 키가 하나도 없거나, 사용자가 명시적으로 회전(rotate)을 요청할 때만 생성한다.

## 0. 이미 프로비저닝됐으면 단축 종료

`~/.config/ib/sheets-sync.env` 가 있으면 읽는다. `GCP_PROJECT_ID`, `SA_EMAIL`, 그리고 실제 파일을 가리키는 `SA_KEY_PATH` 가 이미 정의돼 있으면 계정은 이미 설정된 것 — 기존 값을 보고하고 중단한다(사용자가 명시적으로 재프로비저닝이나 키 회전을 원하는 경우는 예외). 여기엔 볼트별 항목이 없다. 이 스킬은 같은 계정에 대해 두 번 실행될 필요가 없다. (이것이 브라우저가 필요 없는 유일한 경로다 — 아래는 전부 브라우저가 필요하다.)

## 1. 브라우저 자동화는 켜져 있어야 한다 — 가장 먼저 확인 (하드 게이트)

이 스킬은 브라우저 사용을 전제한다. **무엇이든 프로비저닝하기 전에**, 브라우저 구동 도구가 실제로 사용 가능하고 활성화돼 있는지 확인한다 — `claude-in-chrome` 스킬 또는 Chrome/DevTools MCP. **클릭을 가정하거나 위조하지 말 것.**

- **활성화됨** → 계속 진행.
- **활성화 안 됨** → **즉시 중단.** 프로젝트·서비스 계정·키를 만들지 말 것. 사용자에게 브라우저 자동화를 켜라고 알린다(**Claude in Chrome** 확장 / Chrome MCP 권장) 그리고 이 스킬을 다시 실행하게 한다. GCP 콘솔 작업 — 특히 사람만 가능한 키 다운로드 — 에는 브라우저 사용이 필요하다는 점을 분명히 밝힌다. 수동으로 억지로 진행하거나 절반만 프로비저닝하고 실패하지 말 것.

이 게이트를 일부러 맨 앞에 둔 이유는, 실행이 중간까지 진행되는 것(이전에 중복/절반만 생성된 프로젝트를 남기던 실패 모드)을 막기 위해서다.

그런 다음 사용자에게 프로젝트 슬러그(기본 `infinite-brain`)와 서비스 계정 이름(기본 `ib-sheets-sync`)을 묻는다.

**선택적 가속기 — `gcloud`.** `gcloud` 가 설치되고 인증돼 있으면(`gcloud --version`, `gcloud auth list`), §2의 결정적 생성/확인 단계에 *사용해도 된다* — 멱등 확인이 정확해진다. 단, 브라우저 게이트를 대체하지는 않는다: JSON 키 처리와 콘솔 확인은 여전히 브라우저를 거친다. `gcloud` 가 없으면 모든 것을 브라우저 콘솔(§3)로 처리한다. 사용자가 설치를 원하면 <https://cloud.google.com/sdk/docs/install> 를 안내해도 된다.

## 2. gcloud 가속 경로 (선택, 멱등)

§1에 따라 `gcloud` 가 사용 가능할 때만 사용한다. `SLUG` 를 선택한 프로젝트 슬러그(기본 `infinite-brain`), `SA` 를 서비스 계정 이름(기본 `ib-sheets-sync`)이라 하자.

1. **프로젝트 — 재사용 또는 생성.**
   ```bash
   gcloud projects list --filter="name:$SLUG OR projectId:$SLUG" --format="value(projectId)"
   ```
   - 결과가 나오면 그 `projectId` 를 **재사용**한다(사용자에게 보여주고, 여러 개가 매칭되면 올바른 것인지 확인).
   - 비어 있으면 생성한다. GCP 프로젝트 ID는 전역적으로 고유하므로 맨 슬러그가 이미 쓰이고 있을 수 있다. 충돌 시에만 짧은 숫자 접미사를 붙인다:
     ```bash
     gcloud projects create "$SLUG" --name="$SLUG"   # 충돌 시 "$SLUG-NNNNNN" 으로 재시도
     ```
   결과 id를 `GCP_PROJECT_ID` 로 기록한다. 활성화: `gcloud config set project "$GCP_PROJECT_ID"`.

2. **API 활성화** (이미 활성화된 API를 다시 활성화하는 것은 no-op):
   ```bash
   gcloud services enable sheets.googleapis.com drive.googleapis.com --project="$GCP_PROJECT_ID"
   ```

3. **서비스 계정 — 재사용 또는 생성.**
   ```bash
   gcloud iam service-accounts list --project="$GCP_PROJECT_ID" --format="value(email)"
   ```
   - `$SA@$GCP_PROJECT_ID.iam.gserviceaccount.com` 와 일치하는 계정이 있으면 **재사용**한다.
   - 없으면 생성한다:
     ```bash
     gcloud iam service-accounts create "$SA" --display-name="ib sheets sync" --project="$GCP_PROJECT_ID"
     ```
   이메일을 `SA_EMAIL` 로 기록한다.

4. **JSON 키 — 디스크에 있으면 재사용, 없을 때만 생성.** 정규 위치는 `~/.config/ib/sa-key.json`.
   - 해당 파일이 이미 있으면 **재사용**한다 — 또 다른 키를 생성하지 말 것(새 키마다 관리해야 할 라이브 자격증명이 하나 더 늘어난다). `SA_KEY_PATH` 를 기록한다.
   - 없으면(또는 사용자가 명시적으로 회전을 원하면) 생성한다:
     ```bash
     mkdir -p ~/.config/ib
     gcloud iam service-accounts keys create ~/.config/ib/sa-key.json --iam-account="$SA_EMAIL"
     ```
   브라우저 경로와 달리 gcloud `keys create` 는 파일을 직접 써도 된다(사용자가 이 스킬을 호출하고 이 경로를 선택했으므로). 라이브 자격증명이 어디에 기록됐는지 사용자에게 알린다.

## 3. 브라우저 콘솔 경로 (기본, 검사 기반 멱등)

기본 경로다(어느 쪽이든 브라우저 사용은 필수). Cloud Console을 구동하되 **생성 전에 매번 확인**한다:

1. **프로젝트 — 재사용 또는 생성.** 프로젝트 선택기(`console.cloud.google.com` → 프로젝트 드롭다운) 또는 `console.cloud.google.com/cloud-resource-manager` 를 연다. **먼저 목록에서 슬러그를 검색한다.** `infinite-brain` 이름의 프로젝트가 있으면 선택한다 — `projectcreate` 를 열지 **말 것**. 없을 때만 `console.cloud.google.com/projectcreate` 로 가서 생성한다. 프로젝트 id를 확보한다.
2. **API 활성화.** 활성 프로젝트에서 **Google Sheets API** 와 **Google Drive API** 를 활성화한다(`console.cloud.google.com/apis/library`). 라이브러리에 이미 "API Enabled" 가 보이면 건너뛴다.
3. **서비스 계정 — 재사용 또는 생성.** `console.cloud.google.com/iam-admin/serviceaccounts` 를 연다. `ib-sheets-sync@…` 가 목록에 있으면 재사용하고, 없으면 생성한다. `client_email` 을 기록한다.
4. **JSON 키 생성 — ★ 사람이 "만들기" 클릭.** 서비스 계정 → Keys → Add key → Create new key → **JSON(권장)을 선택한 채 "만들기"/Create 클릭**. 키 유형 다이얼로그(JSON / P12)가 뜨면 머뭇거리지 말고 **JSON으로 그대로 진행하라고 사용자에게 분명히 안내한다** — P12는 불필요. (자격증명 다운로드 클릭 자체는 사람이; 조용히 대신 수락하지 말 것.) 다운로드된 파일을 `~/.config/ib/sa-key.json` 로 저장한다(레포 밖, 필요하면 폴더 생성). **왜 안전한지 사용자에게 안내**: 이 키는 `.gitignore` 의 `*.json` 으로 **절대 커밋되지 않고**, GitHub Action용으로는 `gh secret set GOOGLE_SA_KEY` 로 **암호화 시크릿**으로만 들어간다(코드·로그 노출 없음). 콘솔 상단의 `iam.serviceAccountKeyExposureResponse` 배너는 키가 **공개 노출될 때**만 자동 비활성화하는 보호 장치라, 커밋하지 않는 한 무관함도 덧붙인다. 경로를 사용자와 확인한다.

## 4. 재사용을 위해 영속화

`~/.config/ib/sheets-sync.env` 를 작성한다(먼저 `~/.config/ib/` 생성) — 이후 스킬과 볼트가 이 작업을 반복하지 않게:

```sh
GCP_PROJECT_ID=<project id>
SA_EMAIL=<service-account email>
SA_KEY_PATH=<JSON 키의 절대 경로, 예: ~/.config/ib/sa-key.json>
```

파일이 이미 있으면 키를 중복으로 추가하지 말고 값을 제자리에서 갱신한다.

## 5. 완료

프로젝트 id, 서비스 계정 이메일, 키 경로를 보고하고, 키 파일은 **라이브 자격증명**임을 사용자에게 상기시킨다 — 어떤 레포에도 넣지 말고 필요하면 나중에 GCP에서 회전한다. 이것은 재사용 가능하다는 점을 알린다: 모든 볼트의 `/setup-sheets-sync` 가 이 값을 자동으로 가져오므로, 다른 프로젝트나 회전된 키가 필요하지 않은 한 `/setup-gcp` 를 다시 실행하지 않는다. 특정 볼트의 다음 단계: **`/setup-sheets-sync`**.
