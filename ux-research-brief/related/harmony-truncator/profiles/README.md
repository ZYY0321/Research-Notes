# 配置目录：先按类型，再按应用

这里保存运行输入；生成的计划、HAP、截图、审核和导出数据写入命令指定的运行目录。配置与产物分开，避免覆盖配置或混淆批次。

```text
profiles/
  apps/                  应用源码、工具链、构建和启动配置
  recipes/<应用>/        该应用各页面的操作路径
  campaigns/             一次批量任务，可同时引用多个应用
```

|类型|主要字段|谁读取|
|---|---|---|
|应用配置 profile|source、studio、sdk、bundle、hap|campaign中的profile，或命令的--profile|
|页面路径 recipe|actions、checks、settle_seconds|campaign页面的recipe，或命令的--recipe|
|批量任务 campaign|applications、pages、预算和算子选择|campaign --spec|

一个campaign引用多个profile；每个应用可以引用多份recipe。recipe负责到达页面，页面中的候选组件仍由扫描、运行节点绑定与规划得到。

## 路径怎样解析

`campaign --spec`通过`source.configuration.load_campaign()`读取任务文件。里面的`profile`、`recipe`、`baseline_run`相对路径，以**这个campaign JSON所在目录**为起点；绝对路径保持其含义。因此把任务放在`profiles/campaigns/`时，应写：

```json
{
  "applications": [
    {
      "profile": "../apps/ohbill.json",
      "max_total": 2,
      "pages": [
        {
          "name": "home",
          "recipe": "../recipes/ohbill/home.json"
        }
      ]
    }
  ]
}
```

从任何工作目录运行，只需正确指定`--spec`和输出位置。命令行直接传入的`--profile`、`--recipe`等路径仍相对于执行命令的目录；Python直接调用`campaign(dict, ...)`时也不会自动猜测这个字典来自哪个文件，应先调用`load_campaign()`或自行提供绝对路径。页面的`file`是源码路径筛选条件，不是配置文件路径，保持原样。

应用profile里的源码、SDK与DevEco等字段仍使用显式本机路径；换机器需按实际安装位置修改。

## 全部22份JSON

### 应用构建配置（5份）

|文件|内容|
|---|---|
|[apps/cloudmusic.json](apps/cloudmusic.json)|启动包 `cc.chenlvin.cloudmusic`|
|[apps/healthy_life.json](apps/healthy_life.json)|启动包 `com.example.healthy_life`|
|[apps/multishopping.json](apps/multishopping.json)|启动包 `com.example.multishopping`|
|[apps/ohbill.json](apps/ohbill.json)|启动包 `com.ericple.ohbill`|
|[apps/wechat_harmonyos.json](apps/wechat_harmonyos.json)|启动包 `cn.icheny.wechat`|

### 页面路径（13份）

|文件|内容|
|---|---|
|[recipes/cloudmusic/cache.json](recipes/cloudmusic/cache.json)|动作5步；到页检查：`[{"equals": "文件沙箱目录为空"}]`|
|[recipes/cloudmusic/me.json](recipes/cloudmusic/me.json)|动作4步；到页检查：`[{"equals": "缓存"}]`|
|[recipes/cloudmusic/settings.json](recipes/cloudmusic/settings.json)|动作5步；到页检查：`[{"equals": "默认首页"}]`|
|[recipes/healthy_life/home.json](recipes/healthy_life/home.json)|动作2步；到页检查：`[{"equals": "健康生活"}]`|
|[recipes/multishopping/detail-roundtrip.json](recipes/multishopping/detail-roundtrip.json)|动作5步；到页检查：`[{"field": "id", "equals": "truncator_probe_45340e3aca84b49df248"}]`|
|[recipes/multishopping/detail.json](recipes/multishopping/detail.json)|动作1步；到页检查：`[{"equals": "立即购买"}]`|
|[recipes/multishopping/home.json](recipes/multishopping/home.json)|动作0步；到页检查：`[{"equals": "分类"}]`|
|[recipes/multishopping/newproducts-roundtrip.json](recipes/multishopping/newproducts-roundtrip.json)|动作4步；到页检查：`[{"selector": {"id": "truncator_probe_31cd5ba8ecf6ae62976e", "text": "新品"}}, {"field": "id", "equals": "truncator_probe_9912cfeb3439872dbe29_0"}]`|
|[recipes/multishopping/newproducts.json](recipes/multishopping/newproducts.json)|动作1步；到页检查：`[{"selector": {"id": "truncator_probe_31cd5ba8ecf6ae62976e", "text": "新品"}}]`|
|[recipes/multishopping/reviews.json](recipes/multishopping/reviews.json)|动作2步；到页检查：`[{"equals": "立即购买"}]`|
|[recipes/multishopping/specification.json](recipes/multishopping/specification.json)|动作2步；到页检查：`[{"field": "id", "equals": "truncator_probe_45340e3aca84b49df248"}]`|
|[recipes/ohbill/home.json](recipes/ohbill/home.json)|动作0步；到页检查：`[{"equals": "易记账"}]`|
|[recipes/wechat_harmonyos/me.json](recipes/wechat_harmonyos/me.json)|动作1步；到页检查：`[{"equals": "亚瑟王"}]`|

### 批量任务（4份）

|文件|内容|
|---|---|
|[campaigns/cloudmusic-combined.json](campaigns/cloudmusic-combined.json)|1款应用，3条页面配置|
|[campaigns/commerce-combined.json](campaigns/commerce-combined.json)|1款应用，5条页面配置|
|[campaigns/cross-app.json](campaigns/cross-app.json)|4款应用，4条页面配置|
|[campaigns/one-pass.json](campaigns/one-pass.json)|4款应用，4条页面配置|

## 使用说明

- `recipes/ohbill/home.json`只用于OhBill；同名home分别保存在各应用目录，避免混淆。
- CloudMusic的`cache.json`是应用缓存页面，与`cache-viewport-width`算子无关。
- 商城roundtrip文件记录往返路径；部分商城路径使用历史插桩ID，应配合对应源码版本和基线。
- 历史组合任务保留指定的`baseline_run`或已插桩工程profile，便于复查原实验；不会因为整理目录改成另一来源。开始新实验时，使用自己的profile和路径配置，按需要重新采集基线。
- 算子默认池位于`truncator/mutation/operators.json`；这里的`operators`仅覆盖具体任务的选择，不存储API密钥。

推荐阅读顺序：[OhBill构建配置](apps/ohbill.json) → [首页路径](recipes/ohbill/home.json) → [跨应用任务](campaigns/cross-app.json)。
