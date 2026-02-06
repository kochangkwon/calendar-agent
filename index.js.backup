#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { execSync } from 'child_process';

const server = new Server(
  {
    name: 'calendar-agent',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

/**
 * 캘린더 이벤트 조회 함수 (macOS AppleScript 사용)
 * @param {number} daysOffset - 0: 오늘, 1: 내일, -1: 어제
 * @returns {Array} 이벤트 배열
 */
function getEvents(daysOffset = 1) {
  const script = `
    set targetDate to (current date) + (${daysOffset} * days)
    set beginning of targetDate to targetDate
    set hours of beginning of targetDate to 0
    set minutes of beginning of targetDate to 0
    set seconds of beginning of targetDate to 0
    
    set end of targetDate to targetDate
    set hours of end of targetDate to 23
    set minutes of end of targetDate to 59
    set seconds of end of targetDate to 59
    
    tell application "Calendar"
      set eventList to {}
      repeat with cal in calendars
        set calEvents to (every event of cal whose start date ≥ beginning of targetDate and start date ≤ end of targetDate)
        repeat with evt in calEvents
          set eventInfo to {|title|:(summary of evt), |startDate|:(start date of evt as string), |endDate|:(end date of evt as string), |location|:(location of evt), |calendar|:(name of cal)}
          set end of eventList to eventInfo
        end repeat
      end repeat
      return eventList
    end tell
  `;
  
  try {
    const result = execSync(`osascript -e '${script.replace(/'/g, "'\\''")}'`, {
      encoding: 'utf-8',
      timeout: 10000
    });
    return parseAppleScriptResult(result);
  } catch (error) {
    return { error: error.message };
  }
}

/**
 * AppleScript 결과를 JSON 형태로 파싱
 * @param {string} result - AppleScript 실행 결과
 * @returns {Array} 파싱된 이벤트 배열
 */
function parseAppleScriptResult(result) {
  if (!result || result.trim() === '' || result.trim() === '{}') {
    return [];
  }
  
  try {
    // AppleScript는 record를 "title:xxx, startDate:yyy" 형식으로 반환
    const events = [];
    const recordPattern = /title:([^,]+),\s*startDate:([^,]+),\s*endDate:([^,]+),\s*location:([^,]*),\s*calendar:([^,}]+)/g;
    
    let match;
    while ((match = recordPattern.exec(result)) !== null) {
      events.push({
        title: match[1].trim(),
        startDate: match[2].trim(),
        endDate: match[3].trim(),
        location: match[4].trim() || '미정',
        calendar: match[5].trim()
      });
    }
    
    return events;
  } catch (error) {
    console.error('Parsing error:', error);
    return [];
  }
}

/**
 * 이벤트 목록을 보기 좋은 텍스트로 포맷팅
 * @param {Array} events - 이벤트 배열
 * @param {string} dateLabel - 날짜 라벨 (예: "내일", "오늘")
 * @returns {string} 포맷팅된 텍스트
 */
function formatEvents(events, dateLabel = '내일') {
  if (events.error) {
    return `❌ 일정 조회 중 오류 발생: ${events.error}`;
  }
  
  if (events.length === 0) {
    return `📅 ${dateLabel} 예정된 일정이 없습니다.`;
  }
  
  const eventSummary = events.map((evt, idx) => {
    const lines = [
      `${idx + 1}. 📌 ${evt.title}`,
      `   🕐 시간: ${evt.startDate}`,
    ];
    
    if (evt.location && evt.location !== '미정') {
      lines.push(`   📍 장소: ${evt.location}`);
    }
    
    lines.push(`   📂 캘린더: ${evt.calendar}`);
    
    return lines.join('\n');
  }).join('\n\n');
  
  return `📅 ${dateLabel} 일정 (총 ${events.length}개):\n\n${eventSummary}`;
}

// 도구 목록 등록
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: 'check_tomorrow_events',
      description: '내일 예정된 캘린더 일정을 모두 확인합니다. iCloud 캘린더와 동기화된 모든 일정을 조회합니다.',
      inputSchema: {
        type: 'object',
        properties: {},
      },
    },
    {
      name: 'check_today_events',
      description: '오늘 예정된 캘린더 일정을 모두 확인합니다. 현재 진행 중이거나 예정된 일정을 조회합니다.',
      inputSchema: {
        type: 'object',
        properties: {},
      },
    },
    {
      name: 'check_events_by_offset',
      description: '특정 날짜의 일정을 확인합니다. offset을 사용하여 원하는 날짜의 일정을 조회할 수 있습니다.',
      inputSchema: {
        type: 'object',
        properties: {
          daysOffset: {
            type: 'number',
            description: '오늘 기준 일 수 (0: 오늘, 1: 내일, 2: 모레, -1: 어제)',
            default: 1
          }
        },
        required: ['daysOffset']
      },
    },
  ],
}));

// 도구 실행 핸들러
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  
  switch (name) {
    case 'check_tomorrow_events': {
      const events = getEvents(1);
      const formattedText = formatEvents(events, '내일');
      
      return {
        content: [
          {
            type: 'text',
            text: formattedText,
          },
        ],
      };
    }
    
    case 'check_today_events': {
      const events = getEvents(0);
      const formattedText = formatEvents(events, '오늘');
      
      return {
        content: [
          {
            type: 'text',
            text: formattedText,
          },
        ],
      };
    }
    
    case 'check_events_by_offset': {
      const offset = args.daysOffset || 1;
      const events = getEvents(offset);
      
      let dateLabel = '해당 날짜';
      if (offset === 0) dateLabel = '오늘';
      else if (offset === 1) dateLabel = '내일';
      else if (offset === 2) dateLabel = '모레';
      else if (offset === -1) dateLabel = '어제';
      else if (offset > 0) dateLabel = `${offset}일 후`;
      else dateLabel = `${Math.abs(offset)}일 전`;
      
      const formattedText = formatEvents(events, dateLabel);
      
      return {
        content: [
          {
            type: 'text',
            text: formattedText,
          },
        ],
      };
    }
    
    default:
      throw new Error(`Unknown tool: ${name}`);
  }
});

// 서버 시작
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Calendar Agent MCP server running on stdio');
}

main().catch((error) => {
  console.error('Server error:', error);
  process.exit(1);
});
