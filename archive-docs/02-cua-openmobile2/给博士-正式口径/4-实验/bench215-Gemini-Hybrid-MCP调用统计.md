# 正式 215 · Gemini Hybrid · App 工具（MCP）调用统计

一套总表，不拆 170 / 45。每道题只取一行：正式 215 里仍在 9/3 底表的 170 道用 `bench200-gemini31-207-reinst-20260903/hybrid`；另外 45 道用 9/4 对应补跑包（timewall / pack8 / secretary / pack2 / pack3）各一行。170 道没有被 recover 重跑。

点屏幕的 `mobile_use` 不算 MCP。下面的「工具」都是 `app__verb` 这类应用内函数。

## 合计

| 项 | 数 |
|---|---:|
| 题 | 215 |
| Hybrid 成功 | 147（68.4%） |
| `mobile_use` 次数 | 3995 |
| App 工具调用次数 | **406** |
| 调过的工具种类 | **110** |
| 至少调过 1 次工具的题 | 119 / 215 |
| 轨迹里出现过的候选工具 | 306 |
| 候选里一次没调过的 | 199 |

## 每种工具的调用频率

按次数降序。次数是 215 道 Hybrid 轨迹里该函数名出现的步数。

| 排名 | 次数 | 工具 |
|---:|---:|---|
| 1 | 44 | `broadcast__search_shows` |
| 2 | 32 | `notes__create_note` |
| 3 | 18 | `kapi__prepare_bill_draft` |
| 4 | 17 | `calendar__prepare_event_draft` |
| 5 | 16 | `broadcast__search_episodes` |
| 6 | 11 | `tencent_meeting__calculate_participation` |
| 7 | 10 | `wechat__search_contacts` |
| 8 | 10 | `wechat__send_text_message` |
| 9 | 9 | `ctrip__search_hotels` |
| 10 | 7 | `alipay__get_balance_summary` |
| 11 | 7 | `railway12306__open_train_for_booking` |
| 12 | 6 | `alipay__search_bills` |
| 13 | 6 | `mail__search_messages` |
| 14 | 6 | `slack__send_text_message` |
| 15 | 5 | `weather__search_cities` |
| 16 | 5 | `weather__get_daily_forecast` |
| 17 | 5 | `tencent_meeting__list_history` |
| 18 | 5 | `tbsg__add_item_to_cart` |
| 19 | 5 | `broadcast__add_to_queue` |
| 20 | 5 | `slack__list_conversations` |
| 21 | 5 | `kapi__search_bills` |
| 22 | 5 | `broadcast__open_show` |
| 23 | 4 | `ebay__search_products` |
| 24 | 4 | `redbook__prepare_text_post` |
| 25 | 4 | `tbsg__search_shops` |
| 26 | 4 | `tbsg__search_items` |
| 27 | 4 | `broadcast__list_up_next` |
| 28 | 4 | `jingdong__search_items` |
| 29 | 4 | `jingdong__get_cart` |
| 30 | 4 | `luckin__search_products` |
| 31 | 4 | `mail__prepare_draft` |
| 32 | 4 | `kapi__get_category_summary` |
| 33 | 4 | `dianping__search_shops` |
| 34 | 4 | `weibo__search_statuses` |
| 35 | 3 | `spotify__list_recent_plays` |
| 36 | 3 | `clock__create_alarm` |
| 37 | 3 | `jingdong__prepare_checkout` |
| 38 | 3 | `jingdong__list_orders` |
| 39 | 3 | `luckin__open_product` |
| 40 | 3 | `railway12306__open_query_results` |
| 41 | 3 | `slack__search_messages` |
| 42 | 3 | `ctrip__open_hotel` |
| 43 | 3 | `googledrive__search` |
| 44 | 3 | `googledrive__open_item` |
| 45 | 3 | `kapi__open_bill` |
| 46 | 2 | `alipay__summarize_bills` |
| 47 | 2 | `wechat__prepare_moment_draft` |
| 48 | 2 | `wechat_reading__get_hot_search` |
| 49 | 2 | `calendar__get_busy_intervals` |
| 50 | 2 | `tencent_meeting__prepare_schedule` |
| 51 | 2 | `file_manager__copy_file` |
| 52 | 2 | `tencent_meeting__get_meeting_summary` |
| 53 | 2 | `broadcast__open_episode` |
| 54 | 2 | `daysmatter__list_notebooks` |
| 55 | 2 | `jingdong__add_to_cart` |
| 56 | 2 | `luckin__add_to_cart` |
| 57 | 2 | `luckin__open_cart` |
| 58 | 2 | `railway12306__get_account_summary` |
| 59 | 2 | `tencent_meeting__search_meetings` |
| 60 | 2 | `kapi__get_budget_status` |
| 61 | 2 | `ctrip__search_trains` |
| 62 | 2 | `taobao__open_search_results` |
| 63 | 2 | `alipay__search_contacts` |
| 64 | 2 | `alipay__prepare_transfer` |
| 65 | 2 | `jingdong__get_order_summary` |
| 66 | 2 | `railway12306__list_passengers` |
| 67 | 1 | `bilibili__open_ranking` |
| 68 | 1 | `bilibili__get_ranking` |
| 69 | 1 | `bilibili__search_videos` |
| 70 | 1 | `bilibili__open_video` |
| 71 | 1 | `spotify__add_to_playlist` |
| 72 | 1 | `wechat_reading__get_reading_stats` |
| 73 | 1 | `calendar__open_date` |
| 74 | 1 | `file_manager__list_directory` |
| 75 | 1 | `tencent_meeting__open_meeting` |
| 76 | 1 | `daysmatter__prepare_event_draft` |
| 77 | 1 | `dida__search_tasks` |
| 78 | 1 | `dida__complete_task` |
| 79 | 1 | `jingdong__open_cart` |
| 80 | 1 | `luckin__list_coupons` |
| 81 | 1 | `mail__set_read` |
| 82 | 1 | `tbsg__get_shop_menu` |
| 83 | 1 | `tbsg__prepare_checkout` |
| 84 | 1 | `tbsg__open_cart` |
| 85 | 1 | `tbsg__list_orders` |
| 86 | 1 | `tbsg__open_order` |
| 87 | 1 | `tbsg__open_shop` |
| 88 | 1 | `daysmatter__list_upcoming_events` |
| 89 | 1 | `daysmatter__search_events` |
| 90 | 1 | `railway12306__open_query_form` |
| 91 | 1 | `railway12306__query_trains` |
| 92 | 1 | `luckin__get_cart` |
| 93 | 1 | `dianping__add_favorite_shop` |
| 94 | 1 | `xianyu__list_listings` |
| 95 | 1 | `dida__create_task` |
| 96 | 1 | `suning__search_products` |
| 97 | 1 | `dianping__list_shop_deals` |
| 98 | 1 | `dianping__open_voucher` |
| 99 | 1 | `youku__search_catalog` |
| 100 | 1 | `ctrip__list_orders` |
| 101 | 1 | `kapi__open_stats` |
| 102 | 1 | `kapi__open_category` |
| 103 | 1 | `broadcast__get_show_summary` |
| 104 | 1 | `redbook__search_notes` |
| 105 | 1 | `redbook__search_users` |
| 106 | 1 | `redbook__open_user` |
| 107 | 1 | `ctrip__open_orders` |
| 108 | 1 | `jingdong__compare_items` |
| 109 | 1 | `taobao__get_cart` |
| 110 | 1 | `taobao__get_item_summary` |

## 按 App 汇总

| App | 调用次数 | 调过的种类 |
|---|---:|---:|
| broadcast | 77 | 7 |
| kapi | 34 | 7 |
| notes | 32 | 1 |
| tencent_meeting | 23 | 6 |
| wechat | 22 | 3 |
| calendar | 20 | 3 |
| jingdong | 20 | 8 |
| alipay | 19 | 5 |
| tbsg | 19 | 9 |
| railway12306 | 16 | 6 |
| ctrip | 16 | 5 |
| slack | 14 | 3 |
| luckin | 13 | 6 |
| mail | 11 | 3 |
| weather | 10 | 2 |
| redbook | 7 | 4 |
| dianping | 7 | 4 |
| googledrive | 6 | 2 |
| daysmatter | 5 | 4 |
| ebay | 4 | 1 |
| bilibili | 4 | 4 |
| spotify | 4 | 2 |
| taobao | 4 | 3 |
| weibo | 4 | 1 |
| wechat_reading | 3 | 2 |
| clock | 3 | 1 |
| file_manager | 3 | 2 |
| dida | 3 | 3 |
| xianyu | 1 | 1 |
| suning | 1 | 1 |
| youku | 1 | 1 |

机器可读：`artifacts/bench215-gemini-hybrid-tool-freq.json`
