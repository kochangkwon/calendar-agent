# Calendar Agent 📅

iPhone/iCloud 캘린더와 연동하여 일정을 확인하고 자동으로 알림을 제공하는 MCP(Model Context Protocol) 서버입니다.

## 주요 기능

- ✅ **내일 일정 자동 확인**: 매일 저녁 8시 자동으로 내일 일정 체크
- 📱 **iCloud 캘린더 연동**: iPhone과 동기화된 모든 캘린더 지원
- 🔔 **macOS 알림**: 일정이 있을 경우 알림 센터로 통보
- 🤖 **Claude 통합**: Claude Desktop에서 대화로 일정 조회

## 시스템 요구사항

- macOS (Apple Silicon 또는 Intel)
- Node.js 18 이상
- iCloud 캘린더 활성화
- Claude Desktop (선택사항, MCP 기능 사용 시)

## 설치 방법

### 1. 저장소 클론

```bash
git clone https://github.com/YOUR_USERNAME/calendar-agent.git
cd calendar-agent
```

### 2. 의존성 설치

```bash
npm install
```

### 3. 권한 설정

처음 실행 시 다음 권한이 필요합니다:

1. **시스템 설정 > 개인정보 보호 > 캘린더**
   - Terminal (또는 iTerm) 허용
   - Node 허용

2. **시스템 설정 > 개인정보 보호 > 자동화**
   - Terminal이 Calendar 앱 제어 허용

## 사용 방법

### Claude Desktop과 연동 (MCP 서버)

#### 1. Claude Desktop 설정 파일 수정

```bash
# 설정 파일 위치
code ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

#### 2. 다음 내용 추가

```json
{
  "mcpServers": {
    "calendar-agent": {
      "command": "node",
      "args": ["/절대/경로/calendar-agent/index.js"]
    }
  }
}
```

⚠️ **주의**: `/절대/경로/`를 실제 프로젝트 경로로 변경하세요.

```bash
# 현재 경로 확인
pwd
```

#### 3. Claude Desktop 재시작

#### 4. Claude와 대화로 일정 확인

```
"내일 일정 알려줘"
"오늘 일정 확인해줘"
"모레 뭐 있어?"
```

### 독립 실행 모드

#### MCP 서버 실행

```bash
npm start
```

#### 자동 알림 서비스 실행

```bash
npm run reminder
```

매일 저녁 8시에 자동으로 내일 일정을 확인하고 알림을 표시합니다.

### 백그라운드 서비스로 등록 (launchd)

#### 1. launchd plist 파일 생성

```bash
cat > ~/Library/LaunchAgents/com.calendar.agent.reminder.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" 
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.calendar.agent.reminder</string>
  
  <key>ProgramArguments</key>
  <array>
    <string>/usr/local/bin/node</string>
    <string>/절대/경로/calendar-agent/daily-reminder.js</string>
  </array>
  
  <key>RunAtLoad</key>
  <true/>
  
  <key>KeepAlive</key>
  <true/>
  
  <key>StandardOutPath</key>
  <string>/tmp/calendar-agent.log</string>
  
  <key>StandardErrorPath</key>
  <string>/tmp/calendar-agent.error.log</string>
</dict>
</plist>
EOF
```

#### 2. Node.js 경로 확인 및 수정

```bash
# Node.js 경로 확인
which node

# plist 파일에서 Node.js 경로 수정 필요 시
# /usr/local/bin/node → 실제 경로로 변경
```

#### 3. launchd 등록 및 시작

```bash
# 서비스 등록
launchctl load ~/Library/LaunchAgents/com.calendar.agent.reminder.plist

# 실행 확인
launchctl list | grep calendar

# 로그 확인
tail -f /tmp/calendar-agent.log
```

#### 4. 서비스 관리

```bash
# 서비스 중지
launchctl unload ~/Library/LaunchAgents/com.calendar.agent.reminder.plist

# 서비스 재시작
launchctl unload ~/Library/LaunchAgents/com.calendar.agent.reminder.plist
launchctl load ~/Library/LaunchAgents/com.calendar.agent.reminder.plist
```

## MCP 도구 목록

### 1. `check_tomorrow_events`
내일 예정된 모든 일정 조회

### 2. `check_today_events`
오늘 예정된 모든 일정 조회

### 3. `check_events_by_offset`
특정 날짜의 일정 조회
- `daysOffset`: 오늘 기준 일 수 (0: 오늘, 1: 내일, -1: 어제)

## 알림 시간 변경

`daily-reminder.js` 파일에서 스케줄 시간 수정:

```javascript
// 매일 저녁 8시 (기본값)
const SCHEDULE_TIME = '0 20 * * *';

// 매일 아침 7시로 변경하려면
const SCHEDULE_TIME = '0 7 * * *';

// Cron 형식: 분 시 일 월 요일
```

## 트러블슈팅

### 캘린더 접근 권한 오류

```bash
# 권한 재설정
tccutil reset Calendar
```

그 후 앱을 다시 실행하여 권한 요청 승인

### MCP 서버가 Claude에 표시되지 않음

1. Claude Desktop 완전 종료 후 재시작
2. `claude_desktop_config.json` 경로 확인
3. JSON 문법 오류 확인

### launchd 서비스가 시작되지 않음

```bash
# 로그 확인
cat /tmp/calendar-agent.error.log

# Node.js 경로 확인
which node

# plist 파일 문법 검사
plutil -lint ~/Library/LaunchAgents/com.calendar.agent.reminder.plist
```

## 라이선스

MIT License

## 작성자

intent69@gmail.com

## 기여하기

이슈와 PR을 환영합니다!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request
