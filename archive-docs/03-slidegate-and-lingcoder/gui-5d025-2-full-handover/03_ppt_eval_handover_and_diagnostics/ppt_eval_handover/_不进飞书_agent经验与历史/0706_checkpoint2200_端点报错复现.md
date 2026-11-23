# checkpoint-2200 端点报错复现（给模型侧）

> 端点：`http://10.210.9.14:111`（lightllm，`server: hypercorn-h11`，model id=`checkpoint-2200`，max_model_len=1048576）
> 复现时间：2026-07-06。复现者：评测侧。

## 结论（两个端点兼容问题）

端点未完整实现 Anthropic Messages 协议，有两处标准形态没支持，agent 真实请求必踩：

1. **content 为数组（block 格式 `[{"type":"text","text":...}]`）→ 崩**（问题一，下方复现 A/B）。content 为纯字符串时正常。这是标准格式，litellm 等框架默认都发数组。
2. **`tool_choice: {"type":"none"}` → 400**（问题二）。收尾阶段的合法参数。

老端点 `10.210.9.11:677`（step4k）两者都支持，所以老模型能跑通。

问题一表现：
- anthropic `/v1/messages`：返回 **500 Internal Server Error**
- openai `/v1/chat/completions`：返回 **400**，报文明确：
  `Failed to build prompt: sequence item 0: expected str instance, list found`
  → 端点内部把 content 当 str 直接拼 prompt，遇到 list 就崩。

排除项（均**不是**原因，单独或叠加都不崩）：max_tokens=128000、长 system prompt(16k字)、tools、cache_control、prompt-caching header。唯一变量就是 content 格式。

## 「为什么 content 是 list 不是 str」——litellm 转的，非调用方

有人会问：我们不是传 str 吗，怎么变 list？答：**agent 传给 litellm 的 content 是 str，litellm 的 anthropic provider 在实际发送时把每条 message 的 content 统一规范化成 Anthropic 官方标准的 block 数组** `[{"type":"text","text":...}]`（user、system 都转）。这是 litellm / Anthropic SDK 的标准行为，走 anthropic provider 就必然如此，传 str 也绕不过。

**wire 级铁证**：用 `litellm._turn_on_debug()` 抓到的、实际发到本端点的请求体（我们传进 litellm 的明明是 str content）：
```json
{"model":"checkpoint-2200",
 "messages":[{"role":"user","content":[{"type":"text","text":"制作一份《并购财务尽职调查》主题PPT..."}]}],
 "system":[{"type":"text","text":"Today: 2026-07-06 ... # Role 你是一个全能型智能体..."}],
 "max_tokens":64}
```
→ 端点返回 500。链路：`agent(str content)` → `litellm.completion(custom_llm_provider="anthropic")` → **litellm 转成 block 数组** → 端点 500。

---

## 复现 A：anthropic /v1/messages

**❌ 失败（content = 数组）→ HTTP 500**

```bash
curl -i http://10.210.9.14:111/v1/messages -H 'content-type: application/json' -H 'anthropic-version: 2023-06-01' -H 'x-api-key: dummy' -d '{"model":"checkpoint-2200","max_tokens":32,"messages":[{"role":"user","content":[{"type":"text","text":"say PONG"}]}]}'
```

响应：

```
HTTP/1.1 500
content-type: text/plain; charset=utf-8
server: hypercorn-h11

Internal Server Error
```

**✅ 对照成功（content = 字符串）→ HTTP 200**

```bash
curl -i http://10.210.9.14:111/v1/messages -H 'content-type: application/json' -H 'anthropic-version: 2023-06-01' -H 'x-api-key: dummy' -d '{"model":"checkpoint-2200","max_tokens":32,"messages":[{"role":"user","content":"say PONG"}]}'
```

---

## 复现 B：openai /v1/chat/completions（报文更明确）

**❌ 失败（content = 数组）→ HTTP 400**

```bash
curl -i http://10.210.9.14:111/v1/chat/completions -H 'content-type: application/json' -d '{"model":"checkpoint-2200","max_tokens":32,"messages":[{"role":"user","content":[{"type":"text","text":"say PONG"}]}]}'
```

响应：

```
HTTP/1.1 400
content-type: application/json

{"error":{"message":"Failed to build prompt: sequence item 0: expected str instance, list found","type":"BadRequestError","param":null,"code":400}}
```

**✅ 对照成功（content = 字符串）→ HTTP 200**

```bash
curl -i http://10.210.9.14:111/v1/chat/completions -H 'content-type: application/json' -d '{"model":"checkpoint-2200","max_tokens":32,"messages":[{"role":"user","content":"say PONG"}]}'
```

---

## 问题二：不支持 tool_choice = none（HTTP 400）

与问题一同类：另一个 Anthropic 协议的合法参数没实现。agent 在收尾阶段（禁止继续调工具、让模型直接总结）会发 `tool_choice: {"type":"none"}`，端点返回 400。

`tool_choice` 的合法取值有 auto / any / tool / none 四种；端点只实现了部分，`none` 没实现。

**❌ 失败（tool_choice = none）→ HTTP 400**

```bash
curl -i http://10.210.9.14:111/v1/messages -H 'content-type: application/json' -H 'anthropic-version: 2023-06-01' -H 'x-api-key: dummy' -d '{"model":"checkpoint-2200","max_tokens":32,"messages":[{"role":"user","content":"say hi"}],"tools":[{"name":"foo","description":"demo","input_schema":{"type":"object","properties":{}}}],"tool_choice":{"type":"none"}}'
```

响应：

```
HTTP/1.1 400
{"type":"error","error":{"type":"invalid_request_error","message":"Request translation failed: Incompatible tool choice param submitted - {'type': 'none'}"}}
```

**✅ 对照成功（tool_choice = auto，或不带该字段）→ HTTP 200**

```bash
curl -i http://10.210.9.14:111/v1/messages -H 'content-type: application/json' -H 'anthropic-version: 2023-06-01' -H 'x-api-key: dummy' -d '{"model":"checkpoint-2200","max_tokens":32,"messages":[{"role":"user","content":"say hi"}],"tools":[{"name":"foo","description":"demo","input_schema":{"type":"object","properties":{}}}],"tool_choice":{"type":"auto"}}'
```

影响：只在极端 case（子任务递归深度打满、进收尾）触发，不阻断主流程，已完成的稿子照常产出。但建议和问题一一起修。

---

## 请求修复

端点需完整实现 Anthropic Messages 协议的这两处，都是标准形态、老端点 `10.210.9.11:677`（flash-lite-v36-fp8-step4k）均支持：

1. **content block 数组格式**：`content: [{"type":"text","text":"..."}, ...]`（问题一）
2. **tool_choice = none**：`tool_choice: {"type":"none"}`（问题二）

修好后评测侧可直接接入生成链路（config + skill 脚本已配好新端点，只等端点修复）。
