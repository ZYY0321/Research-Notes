# 真跨 App：信息必须流动

2026-08-30。上一轮轨 B 多数是「查完发给微信」，第二 App 没有吃进第一 App 的事实。按 `67` 那不算覆盖微信，也不算真跨 App。

## 不要的

查完只转发 / 只通知，第二 App 没有用到金额、车次、场次、时间或地点。`S_travel_01` `S_travel_02` `S_local_01` `S_local_02` `S_work_01` `S_work_02` 整批不进。

## 要的

A 的终态事实必须写进 B 的业务记录。微信可以在后面当通知，但不能当唯一跨 App 动作。

| 新 ID | 流动 | 正式 suite id |
|---|---|---|
| `S_finance_01` | 支付宝转账 150 → 卡皮同金额 | `bench200_flow.HTV1FinanceTransferKapi` |
| `S_finance_bill` | 支付宝燃气费 36.2 → 卡皮同金额 | `bench200_flow.HTV1FinanceGasKapi` |
| `S_shop_01` | 京东 vivo 实付 → 卡皮购物 | `bench200_flow.HTV1ShopVivoKapi` |
| `S_shop_02` | 京东 ThinkBook 付完 → 卡皮购物 | `bench200_flow.HTV1ShopThinkbookKapi` |
| `S_travel_train_cal` | 携程沪杭填单车次 → 日历「杭州出发」 | `bench200_flow.HTV1TravelTrainCal` |
| `S_travel_hotel_kapi` | 携程云栖房价 → 卡皮住房 | `bench200_flow.HTV1TravelHotelKapi` |
| `S_travel_12306_cal` | 12306 王思雨沪杭车次 → 日历 | `bench200_flow.HTV1Travel12306Cal` |
| `S_local_movie_cal` | 猫眼功夫女足影院+开场 → 日历 | `bench200_flow.HTV1LocalMovieCal` |
| `S_local_coffee_kapi` | 瑞幸生椰拿铁实付 → 卡皮咖啡 | `bench200_flow.HTV1LocalCoffeeKapi` |
| `S_work_meet_cal` | Slack 下周三 14:00 3 楼 → 日历 | `bench200_flow.HTV1WorkMeetCal` |
| `S_work_launch_cal` | Slack 周五上线 → 日历 7/17 15:00 | `bench200_flow.HTV1WorkLaunchCal` |

时钟与 369 相同：`2026-07-12 09:00`。下周三 = 7 月 15 日，本周五 = 7 月 17 日。3 楼会议室在 Slack `#general` 原文里，不是发明的。

组合 / 新增仍要自己跑 GUI，不能拿 369 源题分顶替。
