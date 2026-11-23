# Demo 点击清单 · 数据绑定三段（先练这个）

载体：淘宝已有任务 `AddItemToCart`（「把某商品加入购物车」）。  
目的：证明判定看的是 **store 真变**，不是前端假高亮。

## 准备

1. 开环境，reset。  
2. 控制台或脚本读：`__SIM__.getState().apps.taobao.cart.length` → 记为 `n0`。  
## 多数据（已 smoke 过 store）

先注入空车再演示更戏剧：

```bash
# simulator 已在 :3000
python -m bench_env.scenarios.smoke_test --scenario taobao/empty_cart
# 期望：before cart len=5 → after [] → PASS
```

会上也可控制台：`__SIM__.setState({apps:{taobao:{cart:[]}}})` 后打开购物车页看空态文案（中/英随 `setLocale`）。

## 操作

4. 打开目标商品详情 → 点加购。  
5. 再读 `cart.length` → 应为 `n0+1`（或空车注入后为 `1`）。  
6. 跑任务 judge / 口述：`check_cart_added` 读的就是这份 JSON。

## 会上金句

> 有人做的 app 前端写死列表、点了只变样式——那种 **getState 不变，任务判定会红**。我们交付的验证挂在后台真值上；RL 的成功信号也是同一份 state，外加轨迹里的截图和动作。

## 咔皮备选

报销开关：前后读同一 `bill.reimburse`；可先 `apply_scenario(..., "kapi/reimburse_mix")`。
