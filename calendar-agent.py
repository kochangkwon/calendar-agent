#!/usr/bin/env python3
"""
Calendar Agent - MCP 서버 (Python)
"""

import sys
import json
import subprocess
from datetime import datetime, timedelta

def log(message):
    """stderr로 로그 출력"""
    print(f"[calendar-agent] {message}", file=sys.stderr, flush=True)

def get_events_simple(days_offset=0):
    """각 캘린더를 개별적으로 조회"""
    
    # 먼저 캘린더 목록 가져오기
    script_calendars = '''
tell application "Calendar"
    set calNames to {}
    repeat with cal in calendars
        set end of calNames to name of cal
    end repeat
    return calNames
end tell
'''
    
    try:
        result = subprocess.run(
            ['osascript', '-e', script_calendars],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return []
        
        calendar_names = [name.strip() for name in result.stdout.strip().split(', ')]
        
    except Exception as e:
        log(f"캘린더 목록 조회 오류: {e}")
        return []
    
    all_events = []
    
    # 각 캘린더에서 개별적으로 이벤트 조회
    for cal_name in calendar_names:
        script = f'''
set targetDate to (current date) + ({days_offset} * days)
set hours of targetDate to 0
set minutes of targetDate to 0
set seconds of targetDate to 0

set endDate to targetDate + (1 * days)

tell application "Calendar"
    try
        set targetCal to calendar "{cal_name}"
        set eventList to ""
        set dayEvents to (every event of targetCal whose start date ≥ targetDate and start date < endDate)
        
        repeat with evt in dayEvents
            set eventList to eventList & "EVENT_START" & return
            set eventList to eventList & (summary of evt) & return
            set eventList to eventList & (start date of evt as string) & return
            try
                set eventList to eventList & (location of evt) & return
            on error
                set eventList to eventList & return
            end try
            set eventList to eventList & "EVENT_END" & return
        end repeat
        
        return eventList
    on error
        return ""
    end try
end tell
'''
        
        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                # 파싱
                lines = result.stdout.strip().split('\n')
                i = 0
                while i < len(lines):
                    if lines[i] == 'EVENT_START':
                        if i + 3 < len(lines):
                            title = lines[i + 1]
                            start = lines[i + 2]
                            location = lines[i + 3] if lines[i + 3] else '미정'
                            
                            all_events.append({
                                'title': title,
                                'startDate': start,
                                'location': location,
                                'calendar': cal_name
                            })
                            i += 5  # EVENT_START, title, start, location, EVENT_END
                        else:
                            break
                    else:
                        i += 1
        
        except subprocess.TimeoutExpired:
            log(f"타임아웃: {cal_name}")
            continue
        except Exception as e:
            log(f"오류 ({cal_name}): {e}")
            continue
    
    return all_events

def format_events(events, date_label):
    """이벤트 포맷팅"""
    if not events:
        return f"📅 {date_label} 예정된 일정이 없습니다."
    
    output = f"📅 {date_label} 일정 (총 {len(events)}개):\n\n"
    
    for idx, evt in enumerate(events, 1):
        output += f"{idx}. 📌 {evt['title']}\n"
        output += f"   🕐 시간: {evt['startDate']}\n"
        
        if evt['location'] and evt['location'] != '미정':
            output += f"   📍 장소: {evt['location']}\n"
        
        output += f"   📂 캘린더: {evt['calendar']}\n\n"
    
    return output

def handle_request(request):
    """MCP 요청 처리"""
    method = request.get('method')
    request_id = request.get('id')
    
    if method == 'initialize':
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2025-06-18",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "calendar-agent",
                    "version": "1.0.0"
                }
            }
        }
    
    elif method == 'tools/list':
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": [
                    {
                        "name": "check_today_events",
                        "description": "오늘 예정된 캘린더 일정을 모두 확인합니다.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "check_tomorrow_events",
                        "description": "내일 예정된 캘린더 일정을 모두 확인합니다.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "check_events_by_offset",
                        "description": "특정 날짜의 일정을 확인합니다.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "daysOffset": {
                                    "type": "number",
                                    "description": "오늘 기준 일 수 (0: 오늘, 1: 내일, -1: 어제)"
                                }
                            },
                            "required": ["daysOffset"]
                        }
                    }
                ]
            }
        }
    
    elif method == 'tools/call':
        params = request.get('params', {})
        tool_name = params.get('name')
        arguments = params.get('arguments', {})
        
        if tool_name == 'check_today_events':
            events = get_events_simple(0)
            text = format_events(events, '오늘')
        
        elif tool_name == 'check_tomorrow_events':
            events = get_events_simple(1)
            text = format_events(events, '내일')
        
        elif tool_name == 'check_events_by_offset':
            offset = arguments.get('daysOffset', 1)
            events = get_events_simple(offset)
            
            if offset == 0:
                label = '오늘'
            elif offset == 1:
                label = '내일'
            elif offset == 2:
                label = '모레'
            elif offset == -1:
                label = '어제'
            elif offset > 0:
                label = f'{offset}일 후'
            else:
                label = f'{abs(offset)}일 전'
            
            text = format_events(events, label)
        else:
            text = f"알 수 없는 도구: {tool_name}"
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": text
                    }
                ]
            }
        }
    
    elif method == 'notifications/initialized':
        # initialized 알림은 응답 불필요
        return None
    
    else:
        log(f"알 수 없는 메서드: {method}")
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        }

def main():
    """메인 루프"""
    log("Calendar Agent Python MCP server starting...")
    
    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            
            try:
                request = json.loads(line)
                log(f"Received: {request.get('method')}")
                
                response = handle_request(request)
                
                if response:
                    print(json.dumps(response), flush=True)
                    log(f"Sent response for: {request.get('method')}")
            
            except json.JSONDecodeError as e:
                log(f"JSON 파싱 오류: {e}")
            except Exception as e:
                log(f"요청 처리 오류: {e}")
                if 'request' in locals() and request.get('id'):
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": request.get('id'),
                        "error": {
                            "code": -1,
                            "message": str(e)
                        }
                    }
                    print(json.dumps(error_response), flush=True)
    
    except KeyboardInterrupt:
        log("Server stopped by user")
    except Exception as e:
        log(f"Fatal error: {e}")

if __name__ == '__main__':
    main()