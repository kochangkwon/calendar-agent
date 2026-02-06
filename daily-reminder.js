#!/usr/bin/env node

import schedule from 'node-schedule';
import notifier from 'node-notifier';
import { execSync } from 'child_process';

/**
 * 내일 일정을 확인하고 macOS 알림을 표시하는 함수
 */
async function checkAndNotifyTomorrowEvents() {
  console.log(`[${new Date().toLocaleString('ko-KR')}] 내일 일정 확인 중...`);
  
  const script = `
    set tomorrow to (current date) + (1 * days)
    set beginning of tomorrow to tomorrow
    set hours of beginning of tomorrow to 0
    set minutes of beginning of tomorrow to 0
    set seconds of beginning of tomorrow to 0
    
    set end of tomorrow to tomorrow
    set hours of end of tomorrow to 23
    set minutes of end of tomorrow to 59
    
    tell application "Calendar"
      set eventCount to 0
      set eventList to ""
      
      repeat with cal in calendars
        set calEvents to (every event of cal whose start date ≥ beginning of tomorrow and start date ≤ end of tomorrow)
        repeat with evt in calEvents
          set eventCount to eventCount + 1
          set eventList to eventList & "• " & (summary of evt) & "\\n"
        end repeat
      end repeat
      
      return {eventCount, eventList}
    end tell
  `;
  
  try {
    const result = execSync(`osascript -e '${script.replace(/'/g, "'\\''")}'`, {
      encoding: 'utf-8',
      timeout: 10000
    });
    
    // AppleScript 결과 파싱
    const match = result.match(/(\d+),\s*(.+)/s);
    
    if (!match) {
      console.log('내일 일정 없음');
      return;
    }
    
    const eventCount = parseInt(match[1]) || 0;
    const eventList = match[2]?.trim() || '';
    
    if (eventCount > 0) {
      // macOS 알림 표시
      notifier.notify({
        title: '📅 내일 일정 알림',
        message: `내일 ${eventCount}개의 일정이 있습니다.\n\nClaude에게 "내일 일정 알려줘"라고 물어보세요.`,
        sound: true,
        timeout: 15,
        wait: false
      });
      
      console.log(`✅ 알림 발송: 내일 ${eventCount}개 일정`);
      console.log(`일정 목록:\n${eventList}`);
    } else {
      console.log('내일 일정 없음');
    }
  } catch (error) {
    console.error('❌ 일정 확인 오류:', error.message);
    
    // 오류 알림
    notifier.notify({
      title: '⚠️ 캘린더 확인 오류',
      message: '일정 확인 중 문제가 발생했습니다.',
      sound: false,
      timeout: 10
    });
  }
}

/**
 * 스케줄 작업 설정
 * 기본: 매일 저녁 8시 (20:00)
 * Cron 형식: 분 시 일 월 요일
 */
const SCHEDULE_TIME = '0 20 * * *'; // 매일 저녁 8시

console.log('========================================');
console.log('📅 Calendar Agent - Daily Reminder');
console.log('========================================');
console.log(`⏰ 스케줄: 매일 저녁 8시`);
console.log(`🔔 알림: macOS Notification Center`);
console.log(`📱 연동: iCloud 캘린더`);
console.log('========================================\n');

// 스케줄 작업 등록
const job = schedule.scheduleJob(SCHEDULE_TIME, async function() {
  await checkAndNotifyTomorrowEvents();
});

console.log('✅ 일정 알림 서비스가 시작되었습니다.');
console.log(`   다음 실행 시간: ${job.nextInvocation()}\n`);

// 즉시 테스트 (선택사항)
// 서비스 시작 시 한 번 실행해보려면 주석 해제
// console.log('🧪 테스트 실행 중...\n');
// await checkAndNotifyTomorrowEvents();

// 프로세스 종료 시 정리
process.on('SIGINT', () => {
  console.log('\n\n⏹️  서비스를 종료합니다...');
  job.cancel();
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('\n\n⏹️  서비스를 종료합니다...');
  job.cancel();
  process.exit(0);
});

// 에러 핸들링
process.on('uncaughtException', (error) => {
  console.error('❌ Uncaught Exception:', error);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('❌ Unhandled Rejection at:', promise, 'reason:', reason);
});
