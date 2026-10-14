# session格式复现结果

## 8\.18\-8\.27新增：

1. 9B gui\-only RL @潘正源

![image\.png](图片和附件/image%202.png)

2. 3\.5\-27B SFT （性能下降，复述之前的会话中的输出、长thinking、更倾向于文本solo）

3. gui\+MCP数据构造（sft 1000条、RL\+verify 500条）

```Plain Text
"打开卡皮记账。找到备注为「冰美式」的那笔账单，确认收款商家名称，在笔记新建标题为「Manner账单核对」的笔记，写下商家名和金额。"
     "ht0825_kapi_manner_payee": _new_note_check(
        "Manner账单核对", ("Manner", "29"), ("瑞幸",)
    ),
    
    
 "打开卡皮记账。记一笔收入：类目选「兼职收入」，金额 280 元，备注写「口述翻译」，日期设为 2026 年 7 月 15 日，保存。"
     "ht0825_kapi_translate_income": _kapi_new_bill(
        type_="income", category_name="兼职收入", amount=280, note_contains="口述翻译",
        date_ymd=(2026, 7, 15),
        
        
 "打开Spotify。把周杰伦的「青花瓷」加入已点赞歌曲。"
       "assertions": [
        {
          "field": "已点赞青花瓷",
          "source": "apps",
          "path": "spotify.likedSongs",
          "op": "contains",
          "expected": {
            "title": "青花瓷",
            "artist": "周杰伦"
          }
```



TODO:

1. 任务相似度统计

2. 3\.5/6/8\-27B整体benchmark复现

3. mobilegym\-mock的session格式扩充

## 配置信息：

### 部署端：

##### 官方：

```Plain Text
# vllm
vllm serve Qwen/Qwen3.5-27B --port 8000 --tensor-parallel-size 8 --max-model-len 262144 --reasoning-parser qwen3 --enable-auto-tool-choice --tool-call-parser qwen3_coder

# sglang
python -m sglang.launch_server --model-path Qwen/Qwen3.5-27B --port 8000 --tp-size 8 --mem-fraction-static 0.8 --context-length 262144 --reasoning-parser qwen3 --tool-call-parser qwen3_coder

```

##### 复现：

```Plain Text
# sglang 0.5.10.post1
python -m sglang.launch_server \
  --model-path /mnt/afs/yanchenyang/code/saves/checkpoint-1573 \
  --host 0.0.0.0 \
  --port 8001 \
  --tp-size 1 \
  --mem-fraction-static 0.8 \
  --context-length 32768 \
  --trust-remote-code \
  --served-model-name Qwen3.5-9B \
  --reasoning-parser qwen3 \
  --tool-call-parser qwen3_coder
```

```Plain Text
# 采用上述sglang配置，模型经常出现点不准位置
# vllm 0.19.1

vllm serve /mnt/afs/models/Qwen3.5-27B \
  --host 0.0.0.0 \
  --port 8000 \
  --tensor-parallel-size 1 \
  --max-model-len 32768 \
  --gpu-memory-utilization 0.90 \
  --max-num-seqs 16 \
  --trust-remote-code \
  --served-model-name Qwen3.5-27B \
  --gdn-prefill-backend triton \
  --reasoning-parser qwen3 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_coder
```

### 推理端

enable\_thinking = true

tool通过传参的形式提供（而非写在system prompt里面）

#### GUI\-Only

```SQL
You are a mobile GUI agent. Call the mobile_use tool to interact with the device touchscreen.

# Session interaction

- The task query is provided only once in the first user message, together with the initial screenshot(s).
- After each tool call, the environment returns a tool message containing the resulting screenshot(s).
- All previous assistant responses (including reasoning) remain in the conversation history.
- On each turn, inspect the currently provided screenshot(s) and history, then choose exactly one next action.
- Continue until the task is complete or cannot be completed, then call terminate with the appropriate status.

# Tool call format

The tool schema is provided through the function-calling interface. When calling a tool, emit exactly one Qwen XML tool call — not a JSON object such as {"name": "...", "arguments": {...}} or {"action": "click", "coordinate": [x, y]}.

<tool_call>
<function=mobile_use>
<parameter=action>
click
</parameter>
<parameter=coordinate>
[163, 718]
</parameter>
</function>
</tool_call>

Rules:
- Function calls MUST use <tool_call><function=...><parameter=...>...</parameter></function></tool_call>.
- Put each argument in its own <parameter=...>...</parameter> block.
- For array/object arguments, write valid JSON inside the parameter block.
- Do not output anything after </tool_call>.
- If finishing, use action=terminate in the tool call.

# Visual context

- Only the most recent screenshot(s) are kept as images (controlled by last_n); older screenshot slots are replaced with "This screenshot has been collapsed.", but the complete reasoning and response history is retained.
- Base each action on the currently available screenshots and prior turns.
- Do not assume access to screenshots that are not currently provided.

# Robustness rules

- If the response history suggests you are stuck repeating similar actions without progress, try a different action.
- Use the complete response history to avoid repeating actions that have already been performed.
- Base each action on the currently available screenshots; never assume that an earlier action succeeded without checking its result.
```

```SQL
{
    "id": "gym/task_0001",
    "messages": [
      {
        "role": "system",
        "content": system prompt
      },
      {
        "role": "user",
        "content": "The user query: {query}\n<image>"
      },
      {
        "role": "assistant",
        "content": "<think>...</think>\n<tool_call>...</tool_call>"
      },
      {
        "role": "tool",
        "content": "<image>"
      },
      { 
        "role": "assistant",
        "content": "<think>...</think>\n<tool_call>...</tool_call>"
      },
      ....
     ],
     "images": [
        "image1_path",
        "image2_path",
        ...
     ]
}
```

#### GUI\+MCP （每打开一个app，环境会提供该app的mcp tools，通过user来提供，且只在这一步提供一次；后续打开新的app会提供新的mcp tools）

```SQL
You are a mobile GUI agent. Call the mobile_use tool to interact with the device touchscreen.

# Session interaction

- The task query is provided only once in the first user message, together with the initial screenshot(s).
- After each tool call, the environment returns a tool message containing the resulting screenshot(s).
- All previous assistant responses (including reasoning) remain in the conversation history.
- On each turn, inspect the currently provided screenshot(s) and history, then choose exactly one next action.
- Continue until the task is complete or cannot be completed, then call terminate with the appropriate status.

# Tool call format

The tool schema is provided through the function-calling interface. When calling a tool, emit exactly one Qwen XML tool call — not a JSON object such as {"name": "...", "arguments": {...}} or {"action": "click", "coordinate": [x, y]}.

<tool_call>
<function=mobile_use>
<parameter=action>
click
</parameter>
<parameter=coordinate>
[163, 718]
</parameter>
</function>
</tool_call>

Rules:
- Function calls MUST use <tool_call><function=...><parameter=...>...</parameter></function></tool_call>.
- Put each argument in its own <parameter=...>...</parameter> block.
- For array/object arguments, write valid JSON inside the parameter block.
- Do not output anything after </tool_call>.
- If finishing, use action=terminate in the tool call.

# Visual context

- Only the most recent screenshot(s) are kept as images (controlled by last_n); older screenshot slots are replaced with "This screenshot has been collapsed.", but the complete reasoning and response history is retained.
- Base each action on the currently available screenshots and prior turns.
- Do not assume access to screenshots that are not currently provided.

# Robustness rules

- If the response history suggests you are stuck repeating similar actions without progress, try a different action.
- Use the complete response history to avoid repeating actions that have already been performed.
- Base each action on the currently available screenshots; never assume that an earlier action succeeded without checking its result.

# Extra app tools

The API `tools=` list is only `mobile_use` for the entire session; it does not change
when you open another app.
When the foreground app changes, that turn's tool observation lists extra tools for
the new app inside `<tools></tools>`, together with the new screenshot. Those extra
tools stay valid only while that app remains in the foreground. A later observation
with a new app's tools replaces them.
Never invent a tool from another app. On the launcher / recents / control center,
only `mobile_use` is available — open the app first (`mobile_use` action `open_app`
with its name or id, or click the icon).
Call extra app tools with the same `<tool_call>` XML as `mobile_use`.
After a non-`mobile_use` call: if the tool does not change the UI, the next tool
message is JSON only (no new screenshot); if it changes the UI, the next tool
message contains the JSON result and a new screenshot.
```

```SQL
{
  "id": "...",
  "messages": [
    { 
        "role": "system", 
        "content": "<上面整段 system>" 
    },
    { 
        "role": "user", 
        "content": "The user query: {instruction}\n<image>" 
    },
    { 
        "role": "assistant",     
        "content": "<think>...</think>\n<tool_call>...</tool_call>" 
    },
    { 
        "role": "tool", 
        "content": "Foreground app changed to calendar. ...\n<tools>...</tools>\n<image>" 
    },
    { 
        "role": "assistant", 
        "content": "...<function=calendar__prepare_event_draft>..." 
    },
    { 
        "role": "tool", 
        "content": "{\"ok\": true, ...}\n<image>" 
    },
    { 
        "role": "tool", 
        "content": "<image>" 
    },
    {    
        "role": "assistant", 
        "content": "...terminate success..." 
    }
  ],
  "images": ["screenshot_step0.png", "..."],
  "done": true
}
```

**mobileworld（官方）**：每个任务有配套的工具，mcp工具直接和任务配套写入system prompt中

```SQL
# Tools

You may call one or more functions to assist with the user query.

You are provided with function signatures within <tools></tools> XML tags:
<tools>
{"type": "function", "function": {"name": "mobile_use", "description": "Use a touchscreen to interact with a mobile device, and take screenshots.\n* This is an interface to a mobile device with touchscreen. You can perform actions like clicking, typing, swiping, etc.\n* Some applications may take time to start or process actions, so you may need to wait and take successive screenshots to see the results of your actions.\n* The screen's resolution is 999x999.\n* Make sure to click any buttons, links, icons, etc with the cursor tip in the center of the element. Don't click boxes on their edges unless asked.", "parameters": {"properties": {"action": {"description": "The action to perform. The available actions are:\n* `click`: Click the point on the screen with coordinate (x, y).\n* `long_press`: Press the point on the screen with coordinate (x, y) for specified seconds.\n* `swipe`: Swipe from the starting point with coordinate (x, y) to the end point with coordinates2 (x2, y2).\n* `type`: Input the specified text into the activated input box.\n* `answer`: Output the answer.\n* `system_button`: Press the system button.\n* `wait`: Wait specified seconds for the change to happen.\n* `terminate`: Terminate the current task and report its completion status.\n* `ask_user`: Ask user for clarification.", "enum": ["click", "long_press", "swipe", "type", "answer", "system_button", "wait", "ask_user", "terminate"], "type": "string"}, "coordinate": {"description": "(x, y): The x (pixels from the left edge) and y (pixels from the top edge) coordinates to move the mouse to. Required only by `action=click`, `action=long_press`, and `action=swipe`.", "type": "array"}, "coordinate2": {"description": "(x, y): The x (pixels from the left edge) and y (pixels from the top edge) coordinates to move the mouse to. Required only by `action=swipe`.", "type": "array"}, "text": {"description": "Required only by `action=type`, `action=ask_user` and `action=answer`.", "type": "string"}, "time": {"description": "The seconds to wait. Required only by `action=long_press` and `action=wait`.", "type": "number"}, "button": {"description": "Back means returning to the previous interface, Home means returning to the desktop, Menu means opening the application background menu, and Enter means pressing the enter. Required only by `action=system_button`", "enum": ["Back", "Home", "Menu", "Enter"], "type": "string"}, "status": {"description": "The status of the task. Required only by `action=terminate`.", "type": "string", "enum": ["success", "failure"]}}, "required": ["action"], "type": "object"}}}
<<< one json.dumps(mcp_tool) per line, e.g. amap_maps_distance >>>
</tools>

For each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags:
<tool_call>
{"name": <function-name>, "arguments": <args-json-object>}
</tool_call>

# Response format

Response format for every step:
1) Thought: one concise sentence explaining the next move (no multi-step reasoning).
2) Action: a short imperative describing what to do.
3) A single <tool_call>...</tool_call> block containing only the JSON: {"name": <function-name>, "arguments": <args-json-object>}.

Rules:
- Output exactly in the order: Thought, Action, <tool_call>.
- Be brief: one sentence for Thought, one for Action.
- Do not output anything else outside those three parts.
- If finishing, use mobile_use with action=terminate in the tool call.


```

例子：

```SQL
{
  "id": "hybrid_tools_0825_explore.HTV1Ht0825CalendarDental",
  "runtime": "qwen35_session",
  "backend": "gemini",
  "goal": "打开日历。在 2026 年 7 月 20 日下午 2 点到 3 点安排一个叫「口腔复诊」的日程，提醒设为提前 15 分钟。",
  "messages": [
    {
      "role": "system",
      "content": "# Tools\n\nYou may call one or more functions to assist with the user query.\n\nYou are provided with function signatures within <tools></tools> XML tags:\n<tools>\n{\"type\": \"function\", \"function\": {\"name\": \"mobile_use\", \"description\": \"Use a touchscreen to interact with a mobile device, and take screenshots.\\n* This is an interface to a mobile device with touchscreen. You can perform actions like clicking, typing, swiping, etc.\\n* Some applications may take time to start or process actions, so you may need to wait and take successive screenshots to see the results of your actions.\\n* The screen's resolution is 999x999.\\n* Make sure to click any buttons, links, icons, etc with the cursor tip in the center of the element. Don't click boxes on their edges unless asked.\", \"parameters\": {\"properties\": {\"action\": {\"description\": \"The action to perform. The available actions are:\\n* `click`: Click the point on the screen with coordinate (x, y).\\n* `long_press`: Press the point on the screen with coordinate (x, y) for specified seconds.\\n* `swipe`: Swipe from the starting point with coordinate (x, y) to the end point with coordinates2 (x2, y2).\\n* `type`: Input the specified text into the activated input box.\\n* `answer`: Output the answer.\\n* `system_button`: Press the system button.\\n* `wait`: Wait specified seconds for the change to happen.\\n* `terminate`: Terminate the current task and report its completion status.\", \"enum\": [\"click\", \"long_press\", \"swipe\", \"type\", \"answer\", \"system_button\", \"wait\", \"terminate\"], \"type\": \"string\"}, \"coordinate\": {\"description\": \"(x, y): The x (pixels from the left edge) and y (pixels from the top edge) coordinates to move the mouse to. The coordinates should be values from 0 to 999. Required only by `action=click`, `action=long_press`, and `action=swipe`.\", \"type\": \"array\"}, \"coordinate2\": {\"description\": \"(x, y): The x (pixels from the left edge) and y (pixels from the top edge) coordinates to move the mouse to. Required only by `action=swipe`.\", \"type\": \"array\"}, \"text\": {\"description\": \"Required only by `action=type` and `action=answer`.\", \"type\": \"string\"}, \"time\": {\"description\": \"The seconds to wait. Required only by `action=long_press` and `action=wait`.\", \"type\": \"number\"}, \"button\": {\"description\": \"Back means returning to the previous interface, Home means returning to the desktop, Menu means opening the application background menu, and Enter means pressing the enter. Required only by `action=system_button`\", \"enum\": [\"Back\", \"Home\", \"Menu\", \"Enter\"], \"type\": \"string\"}, \"status\": {\"description\": \"The status of the task. Required only by `action=terminate`.\", \"type\": \"string\", \"enum\": [\"success\", \"failure\"]}}, \"required\": [\"action\"], \"type\": \"object\"}}}\n</tools>\n\nFor each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags:\n<tool_call>\n{\"name\": <function-name>, \"arguments\": <args-json-object>}\n</tool_call>\n\n# Session interaction\n\n- The task query is provided only once in the first user message, together with the initial screenshot(s).\n- After each tool call, the next user message contains only the resulting screenshot(s).\n- All previous assistant responses remain available as the response history.\n- On each turn, inspect the currently provided screenshot(s) and the complete response history, then choose exactly one next action.\n- Do not invent screenshot placeholders; they are inserted by the caller.\n- Continue until the task is complete or cannot be completed, then call terminate with the appropriate status.\n\n# Response format\n\nResponse format for every assistant turn:\n- A single <tool_call>...</tool_call> block containing only the JSON: {\"name\": <function-name>, \"arguments\": <args-json-object>}.\n\nRules:\n- Output exactly one <tool_call> per turn.\n- Do not output anything after </tool_call>.\n- If finishing, use action=terminate in the tool call.\n\n# Visual context\n\n- Only the most recent screenshot(s) are kept as images (controlled by last_n); older screenshot slots are replaced with \"This screenshot has been collapsed.\", but the complete textual response history is still retained.\n- Always base the next action on the currently available screenshots and the response history.\n- Do not assume access to screenshots that are not currently provided.\n\n# Robustness rules\n\n- If the response history suggests you are stuck repeating similar actions without progress, try a different action.\n- Use the complete response history to avoid repeating actions that have already been performed.\n- Base each action on the currently available screenshots; never assume that an earlier action succeeded without checking its result.\n\n# Extra app tools\n\nThe API `tools=` list is only `mobile_use` for the entire session; it does not change\nwhen you open another app.\nWhen the foreground app changes, that turn's tool observation lists extra tools for\nthe new app inside `<tools></tools>`, together with the new screenshot. Those extra\ntools stay valid only while that app remains in the foreground. A later observation\nwith a new app's tools replaces them.\nNever invent a tool from another app. On the launcher / recents / control center,\nonly `mobile_use` is available — open the app first (`mobile_use` action `open_app`\nwith its name or id, or click the icon).\nCall extra app tools with the same `<tool_call>` XML as `mobile_use`.\nAfter a non-`mobile_use` call: if the tool does not change the UI, the next tool\nmessage is JSON only (no new screenshot); if it changes the UI, the next tool\nmessage contains the JSON result and a new screenshot."
    },
    {
      "role": "user",
      "content": "The user query: 打开日历。在 2026 年 7 月 20 日下午 2 点到 3 点安排一个叫「口腔复诊」的日程，提醒设为提前 15 分钟。\n<image>"
    },
    {
      "role": "assistant",
      "content": "<think>\n**My Thought Process for Scheduling a Dental Follow-up**\n\nMy objective here is quite clear: I need to use the Calendar application to set up a specific appointment. The appointment is for a \"dental follow-up,\" which translates to \"口腔复诊\" in Chinese. The date is set for July 20, 2026, and the time slot is from 2:00 PM to 3:00 PM. Crucially, I need to ensure a reminder is configured to trigger 15 minutes prior to the event.\n\nTo begin this process, my immediate priority is to access the Calendar app itself. I'm scanning my environment, specifically the home screen, for the familiar icon representing the Calendar. Ah, there it is. I've pinpointed its approximate location, which appears to be around coordinates (615, 690). My next logical step, therefore, is to initiate an interaction with this icon by clicking on it to launch the application.\n</think>\n<tool_call>\n<function=mobile_use>\n<parameter=action>\nclick\n</parameter>\n<parameter=coordinate>\n[615, 690]\n</parameter>\n</function>\n</tool_call>"
    },
    {
      "role": "tool",
      "content": "Foreground app changed to calendar. Extra app tools for this app are listed below. They are valid only while this app stays in the foreground. Do not call tools from a previous app. The API `tools=` list remains only `mobile_use`; call these extra tools with the same `<tool_call>` XML format.\n<tools>\n{\"type\": \"function\", \"function\": {\"name\": \"calendar__search_events\", \"description\": \"Search calendar event titles and notes. Returns compact candidates, not private event details. This tool does not promise to change the current UI.\", \"parameters\": {\"type\": \"object\", \"properties\": {\"query\": {\"type\": \"string\", \"description\": \"Non-empty text to match in event titles or notes.\"}, \"date_from\": {\"type\": \"string\", \"description\": \"Optional inclusive local date in YYYY-MM-DD format.\"}, \"date_to\": {\"type\": \"string\", \"description\": \"Optional inclusive local date in YYYY-MM-DD format.\"}, \"limit\": {\"type\": \"integer\", \"minimum\": 1, \"maximum\": 20, \"default\": 10}}, \"required\": [\"query\"], \"additionalProperties\": false}}}\n{\"type\": \"function\", \"function\": {\"name\": \"calendar__open_event\", \"description\": \"Open an existing calendar event detail page by an event_id returned from search. When this call returns, its target UI is rendered. Inspect the next screenshot before continuing with GUI actions.\", \"parameters\": {\"type\": \"object\", \"properties\": {\"event_id\": {\"type\": \"string\", \"description\": \"Opaque calendar event identifier.\"}}, \"required\": [\"event_id\"], \"additionalProperties\": false}}}\n{\"type\": \"function\", \"function\": {\"name\": \"calendar__open_date\", \"description\": \"Open Calendar on a specific local date. Event contents remain visible only in the GUI. When this call returns, its target UI is rendered. Inspect the next screenshot before continuing with GUI actions.\", \"parameters\": {\"type\": \"object\", \"properties\": {\"date\": {\"type\": \"string\", \"description\": \"Local date in YYYY-MM-DD format.\"}}, \"required\": [\"date\"], \"additionalProperties\": false}}}\n{\"type\": \"function\", \"function\": {\"name\": \"calendar__get_busy_intervals\", \"description\": \"Return merged busy intervals in a time range without exposing event titles or notes. This tool does not promise to change the current UI.\", \"parameters\": {\"type\": \"object\", \"properties\": {\"start\": {\"type\": \"string\", \"description\": \"Range start as an ISO 8601 date-time.\"}, \"end\": {\"type\": \"string\", \"description\": \"Exclusive range end as an ISO 8601 date-time.\"}}, \"required\": [\"start\", \"end\"], \"additionalProperties\": false}}}\n{\"type\": \"function\", \"function\": {\"name\": \"calendar__prepare_event_draft\", \"description\": \"Open a prefilled new-event form. This does not save an event; use the GUI to review and submit it. When this call returns, its target UI is rendered. Inspect the next screenshot before continuing with GUI actions.\", \"parameters\": {\"type\": \"object\", \"properties\": {\"title\": {\"type\": \"string\", \"maxLength\": 200}, \"date\": {\"type\": \"string\", \"description\": \"Local event date in YYYY-MM-DD format.\"}, \"start_time\": {\"type\": \"string\", \"description\": \"HH:mm; required unless all_day is true.\"}, \"end_time\": {\"type\": \"string\", \"description\": \"HH:mm; required unless all_day is true.\"}, \"all_day\": {\"type\": \"boolean\", \"default\": false}, \"description\": {\"type\": \"string\", \"maxLength\": 2000}}, \"required\": [\"title\", \"date\"], \"additionalProperties\": false}}}\n</tools>\n<image>"
    },
    {
      "role": "assistant",
      "content": "<think>\nThe user wants to schedule a calendar event.\nEvent details:\n- Title: 口腔复诊\n- Date: 2026-07-20\n- Time: 14:00 to 15:00 (下午 2 点到 3 点)\n- Reminder: 15 minutes before (提前 15 分钟)\n\nI can use the `calendar__prepare_event_draft` tool to open the new event form with the prefilled details.\nTitle: 口腔复诊\nDate: 2026-07-20\nStart time: 14:00\nEnd time: 15:00\n\nLet's call `calendar__prepare_event_draft`.\n</think>\n<tool_call>\n<function=calendar__prepare_event_draft>\n<parameter=date>\n2026-07-20\n</parameter>\n<parameter=end_time>\n15:00\n</parameter>\n<parameter=start_time>\n14:00\n</parameter>\n<parameter=title>\n口腔复诊\n</parameter>\n</function>\n</tool_call>"
    },
    {
      "role": "tool",
      "content": "{\"call_id\": \"tool_call_1\", \"name\": \"calendar__prepare_event_draft\", \"ok\": true, \"output\": {\"route\": \"/new-event?source=tool&title=%E5%8F%A3%E8%85%94%E5%A4%8D%E8%AF%8A&date=2026-07-20&allDay=false&startTime=14%3A00&endTime=15%3A00\", \"persisted\": false}}\n<image>"
    },
    {
      "role": "assistant",
      "content": "<think>\nThe event draft is open.\nTitle: 口腔复诊\nStart time: 2026年7月20日 14:00\nEnd time: 2026年7月20日 15:00\nReminder (提醒): 提前15分钟 (15 minutes before)\n\nEverything looks correct. I just need to click the checkmark at the top right to save the event.\nThe checkmark is at [900, 75].\n</think>\n<tool_call>\n<function=mobile_use>\n<parameter=action>\nclick\n</parameter>\n<parameter=coordinate>\n[900, 75]\n</parameter>\n</function>\n</tool_call>"
    },
    {
      "role": "tool",
      "content": "<image>"
    },
    {
      "role": "assistant",
      "content": "<think>\nThe event has been successfully created.\nI can see \"口腔复诊\" at 14:00 on July 20th.\nThe task is complete.\n</think>\n<tool_call>\n<function=mobile_use>\n<parameter=action>\nterminate\n</parameter>\n<parameter=status>\nsuccess\n</parameter>\n</function>\n</tool_call>"
    }
```

### 

## 训练数据

![image\.png](图片和附件/image%206.png)

![image\.png](图片和附件/image.png)

![image\.png](图片和附件/image%205.png)

![image\.png](图片和附件/image%204.png)



## 复现结果

|模型|备注||AndroidWorld||MobileWorld |||Mobilgym ||Mobilegym\-mock（0815\-218题）||
|---|---|---|---|---|---|---|---|---|---|---|---|
||||pass@1|pass@3|GUI\-only|MCP|user\-Instruction|SR（Success Rate）|PR（Progress Rate）|GUI\-only|MCP|
|base\(官方/复现\)||||||||||||
|Qwen3\.5\-9B|||57\.8 / 57\.3|\-|\-  / 13|\- / 13\.2|\-|\-  / 13\.4|\-|30\.3<br>（21\.8 steps）||
|Qwen3\.5\-27B|||64\.2 / 60\.3|\-|\- / |||\-  / 28\.9|42\.6|||
|Qwen3\.6\-27B|||70\.3 / 65\.9|||||\- / 18\.4|32\.5|||
|Qwen3\.8\-27B|||81\.9 / 80\.2|||\- / 26\.3||\- / 48\.3|56\.4|66\.1|66\.9<br>30次工具调用|
|SFT||||||||||||
|3\.5\-9b\-815\-8k\-ep3|8月15号8k条成功的轨迹sft 3轮（数据只简单做了轨迹级别的简单过滤）<br>三个平台的数据混训|GUI\-Only|71\.3 ± 2\.8|80\.2|29\.9|\-|\-<br>|38\.7|52\.0|||
|3\.5\-9b\-825\-12k\-ep3|8月25号总量12k条成功轨迹进行sft 3轮<br>（在之前的基础上加了2k条mobileworld数据和2k条openmobile数据）<br>三平台数据混训||73\.6 ± 1\.8|81\.9|39\.3|\-|\-|37\.9|51\.0|61\.5<br>（20\.1 steps）|60\.4<br>（20\.7 steps）<br>没有任何工具调用|
|3\.5\-27b\-0825\-12k\-ep3|同上||52\.2 ± 4\.7|65\.5||||||||
|3\.6\-27b\-0825\-12k\-ep3|同上|||||||||||
|9b\-||GUI\+MCP||||||||59\.2|61\.5<br>\(19\.9 steps\)<br>75次mcp工具调用，成功59次|
|||||||||||||
|||||||||||||
|||||||||||||



## benchmark

### MobileWorld

![image\.png](图片和附件/image%203.png)

### MobileGym



![image\.png](图片和附件/image%201.png)





Todo

1. 根据yingying那边搭建gui\+tools sft数据集（大概3000左右）这周五完成构造

2. 



