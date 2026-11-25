类型：记录 ｜ 归属：11-24 E31 验证门实跑 ｜ 状态：维护中

# zyy-e31-gen-v4p：假产物、真导出、题面数字对过一遍

命令只给了题包路径。评分用的是副本库 `_shared_tightened_1124_b`，PARAMS 里若有 `allowed` 会按它放行，没有这个键就和收紧库一样拒绝整张一种颜色。没有改题包，没有改 `_shared_tightened_1124`，没有改这份副本。没有开应用，没有 osascript，没有连生产机和集群。

可评分 46 道。L1 1 道，L2 45 道。L3 和 L4 这次没有，脚本也不会标到这两级。

真导出先看 `ps-2-14-ps-channel-manipulation`。成品 ps-2-14-ps-channel-manipulation.png 分数 0（flat、sample-dots、png-mismatch）

假产物 46 道都是 0 分。另有 28 道的对照夹具（selftest 里原来期望 1）在这份库下变成 0，这不记进假产物失败。

题面先看 `ps-2-11-clipping-mask`。路径 e31-newapps/ps-2-11-clipping-mask-seed.png 在题面里，PARAMS 的路径字段里没有；路径 out/ps-2-11-clipping-mask.psd 在题面里，PARAMS 的路径字段里没有；格式 PSD 在题面里，PARAMS 没有对应的 kind、后缀或文件头

## 各门题数

| 门 | 通过 | 失败 | 未覆盖 |
|---|---:|---:|---:|
| 假产物（期望 0 的夹具在副本库下仍是 0） | 46 | 0 | 0 |
| 真产物（本机已有导出重打仍是 1） | 1 | 1 | 44 |
| 题面（格式、路径、数字在 PARAMS 里有对应字段） | 9 | 37 | 0 |

手工题 63 道只标了 L0，上面三道门没有跑。

## 失败的前 10 道

### 假产物

没有失败。

### 真产物

失败 1 道，下面是前 1 道。

1. `ps-2-14-ps-channel-manipulation`：成品 ps-2-14-ps-channel-manipulation.png 分数 0（flat、sample-dots、png-mismatch）

### 题面

失败 37 道，下面是前 10 道。

1. `ps-2-11-clipping-mask`：路径 e31-newapps/ps-2-11-clipping-mask-seed.png 在题面里，PARAMS 的路径字段里没有；路径 out/ps-2-11-clipping-mask.psd 在题面里，PARAMS 的路径字段里没有；格式 PSD 在题面里，PARAMS 没有对应的 kind、后缀或文件头
2. `ps-2-11-layer-mask-add`：路径 e31-newapps/ps-2-11-layer-mask-add-seed.png 在题面里，PARAMS 的路径字段里没有
3. `ps-2-11-mask-disable-apply`：路径 e31-newapps/ps-2-11-mask-disable-apply-seed.png 在题面里，PARAMS 的路径字段里没有；路径 out/ps-2-11-mask-disable-apply.psd 在题面里，PARAMS 的路径字段里没有；格式 PSD 在题面里，PARAMS 没有对应的 kind、后缀或文件头
4. `ps-2-11-object-mask`：路径 seed/ps-2-11-object-mask-seed.png 在题面里，PARAMS 的路径字段里没有
5. `ps-2-11-vector-mask`：路径 e31-newapps/ps-2-11-vector-mask-seed.png 在题面里，PARAMS 的路径字段里没有；路径 out/ps-2-11-vector-mask.psd 在题面里，PARAMS 的路径字段里没有；格式 PSD 在题面里，PARAMS 没有对应的 kind、后缀或文件头
6. `ps-2-13-ps-repair-clone-stamp`：路径 e31-newapps/ps-2-13-ps-repair-clone-stamp-seed.png 在题面里，PARAMS 的路径字段里没有
7. `ps-2-13-ps-repair-content-aware-fill`：路径 seed/ps-2-13-ps-repair-content-aware-fill-seed.png 在题面里，PARAMS 的路径字段里没有
8. `ps-2-13-ps-repair-patch`：路径 seed/ps-2-13-ps-repair-patch-seed.png 在题面里，PARAMS 的路径字段里没有
9. `ps-2-13-ps-repair-red-eye`：路径 e31-newapps/ps-2-13-red-eye-seed.png 在题面里，PARAMS 的路径字段里没有
10. `ps-2-13-ps-repair-remove-tool`：路径 seed-ps-2-13.png 在题面里，PARAMS 的路径字段里没有

## 对照夹具

selftest 里期望 1 的那条叫对照，不算假产物。它变成 0，只说明旧的正例在副本库下过不了，不把这道题算进假产物失败。这样的有 28 道。

- `ps-2-11-mask-from-transparency`：对照夹具不再是 1（reference=0）
- `ps-2-11-object-mask`：对照夹具不再是 1（reference=0）
- `ps-2-13-ps-repair-clone-stamp`：对照夹具不再是 1（reference=0）
- `ps-2-13-ps-repair-content-aware-fill`：对照夹具不再是 1（reference=0）
- `ps-2-13-ps-repair-patch`：对照夹具不再是 1（reference=0）
- `ps-2-13-ps-repair-red-eye`：对照夹具不再是 1（reference=0）
- `ps-2-13-ps-repair-remove-tool`：对照夹具不再是 1（reference=0）
- `ps-2-14-ps-channel-manipulation`：对照夹具不再是 1（reference=0）
- `ps-2-14-ps-choose-color-apply`：对照夹具不再是 1（reference=0）
- `ps-2-14-ps-color-correction-neutral`：对照夹具不再是 1（reference=0）
- 其余 18 道同样是对照不再为 1，逐题表里的摘要写了。

## 逐题

| 题 | L | 假产物 | 真产物 | 题面 | 摘要 |
|---|---|---|---|---|---|
| `ps-2-11-clipping-mask` | L2 | 通过 | 未覆盖 | 失败 | 真产物未覆盖：成品 out/ps-2-11-clipping-mask.png 不在本机这几个目录里 题面失败：路径 e31-newapps/ps-2-11-clipping-mask-seed.png 在题面里，PARAMS 的路径字段里没有；路径 out/ps-2-11-clipping-mask.psd 在题面里，PARAMS 的路径字段里没有；格式 PSD 在题面里，PARAMS 没有对应的 kind、后缀或文件头 |
| `ps-2-11-layer-mask-add` | L2 | 通过 | 未覆盖 | 失败 | 真产物未覆盖：成品 out/ps-2-11-layer-mask-add.png 不在本机这几个目录里 题面失败：路径 e31-newapps/ps-2-11-layer-mask-add-seed.png 在题面里，PARAMS 的路径字段里没有 |
| `ps-2-11-mask-disable-apply` | L2 | 通过 | 通过 | 失败 | 题面失败：路径 e31-newapps/ps-2-11-mask-disable-apply-seed.png 在题面里，PARAMS 的路径字段里没有；路径 out/ps-2-11-mask-disable-apply.psd 在题面里，PARAMS 的路径字段里没有；格式 PSD 在题面里，PARAMS 没有对应的 kind、后缀或文件头 |
| `ps-2-11-mask-from-transparency` | L2 | 通过 | 未覆盖 | 通过 | 对照夹具不再是 1（reference=0） 真产物未覆盖：成品 out/ps-2-11-mask-from-transparency.png 不在本机这几个目录里 |
| `ps-2-11-object-mask` | L2 | 通过 | 未覆盖 | 失败 | 对照夹具不再是 1（reference=0） 真产物未覆盖：成品 out/ps-2-11-object-mask.psd 不在本机这几个目录里；成品 out/ps-2-11-object-mask.png 不在本机这几个目录里 题面失败：路径 seed/ps-2-11-object-mask-seed.png 在题面里，PARAMS 的路径字段里没有 |
| `ps-2-11-vector-mask` | L2 | 通过 | 未覆盖 | 失败 | 真产物未覆盖：成品 out/ps-2-11-vector-mask.png 不在本机这几个目录里 题面失败：路径 e31-newapps/ps-2-11-vector-mask-seed.png 在题面里，PARAMS 的路径字段里没有；路径 out/ps-2-11-vector-mask.psd 在题面里，PARAMS 的路径字段里没有；格式 PSD 在题面里，PARAMS 没有对应的 kind、后缀或文件头 |
| `ps-2-13-ps-repair-clone-stamp` | L2 | 通过 | 未覆盖 | 失败 | 对照夹具不再是 1（reference=0） 真产物未覆盖：成品 out/ps-2-13-ps-repair-clone-stamp.png 不在本机这几个目录里 题面失败：路径 e31-newapps/ps-2-13-ps-repair-clone-stamp-seed.png 在题面里，PARAMS 的路径字段里没有 |
| `ps-2-13-ps-repair-content-aware-fill` | L2 | 通过 | 未覆盖 | 失败 | 对照夹具不再是 1（reference=0） 真产物未覆盖：成品 out/ps-2-13-ps-repair-content-aware-fill.png 不在本机这几个目录里 题面失败：路径 seed/ps-2-13-ps-repair-content-aware-fill-seed.png 在题面里，PARAMS 的路径字段里没有 |
| `ps-2-13-ps-repair-patch` | L2 | 通过 | 未覆盖 | 失败 | 对照夹具不再是 1（reference=0） 真产物未覆盖：成品 out/ps-2-13-ps-repair-patch.png 不在本机这几个目录里 题面失败：路径 seed/ps-2-13-ps-repair-patch-seed.png 在题面里，PARAMS 的路径字段里没有 |
| `ps-2-13-ps-repair-red-eye` | L2 | 通过 | 未覆盖 | 失败 | 对照夹具不再是 1（reference=0） 真产物未覆盖：成品 out/ps-2-13-ps-repair-red-eye.png 不在本机这几个目录里 题面失败：路径 e31-newapps/ps-2-13-red-eye-seed.png 在题面里，PARAMS 的路径字段里没有 |
| `ps-2-13-ps-repair-remove-bg` | L2 | 通过 | 未覆盖 | 通过 | 真产物未覆盖：成品 out/ps-2-13-ps-repair-remove-bg.png 不在本机这几个目录里；配套 seed/ps-2-13-ps-repair-remove-bg.png 不在本机这几个目录里 |
| `ps-2-13-ps-repair-remove-tool` | L2 | 通过 | 未覆盖 | 失败 | 对照夹具不再是 1（reference=0） 真产物未覆盖：成品 out/ps-2-13-ps-repair-remove-tool.png 不在本机这几个目录里 题面失败：路径 seed-ps-2-13.png 在题面里，PARAMS 的路径字段里没有 |
| `ps-2-14-ps-channel-manipulation` | L2 | 通过 | 失败 | 失败 | 对照夹具不再是 1（reference=0） 真产物失败：成品 ps-2-14-ps-channel-manipulation.png 分数 0（flat、sample-dots、png-mismatch） 题面失败：路径 seed/ps-2-14-ps-channel-manipulation-instructions.txt 在题面里，PARAMS 的路径字段里没有；格式 TXT 在题面里，PARAMS 没有对应的 kind、后缀或文件头 |
| `ps-2-14-ps-choose-color-apply` | L2 | 通过 | 未覆盖 | 失败 | 对照夹具不再是 1（reference=0） 真产物未覆盖：成品 out/ps-2-14-ps-choose-color-apply.png 不在本机这几个目录里 题面失败：路径 seed/ps-2-14-instructions.txt 在题面里，PARAMS 的路径字段里没有；格式 TXT 在题面里，PARAMS 没有对应的 kind、后缀或文件头 |
| `ps-2-14-ps-color-correction-neutral` | L2 | 通过 | 未覆盖 | 失败 | 对照夹具不再是 1（reference=0） 真产物未覆盖：成品 out/ps-2-14-ps-color-correction-neutral.png 不在本机这几个目录里 题面失败：路径 seed/ps-2-14-ps-color-correction-neutral-seed.png 在题面里，PARAMS 的路径字段里没有；颜色 (128, 128, 178) 在题面里，PARAMS 的 rgb / flat_rgb 里没有 |
| `ps-2-14-ps-color-effect` | L2 | 通过 | 未覆盖 | 失败 | 对照夹具不再是 1（reference=0） 真产物未覆盖：成品 out/ps-2-14-ps-color-effect.png 不在本机这几个目录里 题面失败：路径 e31-newapps/ps-2-14-ps-color-effect 在题面里，PARAMS 的路径字段里没有；路径 seed.png 在题面里，PARAMS 的路径字段里没有；路径 reference.png 在题面里，PARAMS 的路径字段里没有；路径 README.txt 在题面里，PARAMS 的路径字段里没有；格式 TXT 在题面里，PARAMS 没有对应的 kind、后缀或文件头 |
| `ps-2-14-ps-color-profile-embed` | L2 | 通过 | 未覆盖 | 失败 | 对照夹具不再是 1（reference=0） 真产物未覆盖：成品 out/ps-2-14-ps-color-profile-embed.png 不在本机这几个目录里 题面失败：路径 e31-newapps/ps-2-14-ps-color-profile-embed-instructions.txt 在题面里，PARAMS 的路径字段里没有；格式 TXT 在题面里，PARAMS 没有对应的 kind、后缀或文件头 |
| `ps-2-14-ps-selective-color-adjust` | L2 | 通过 | 未覆盖 | 失败 | 真产物未覆盖：成品 out/ps-2-14-ps-selective-color-adjust.png 不在本机这几个目录里 题面失败：路径 seed/ps-2-14-ps-selective-color-adjust-seed.png 在题面里，PARAMS 的路径字段里没有；路径 seed/ps-2-14-ps-selective-color-adjust-notes.txt 在题面里，PARAMS 的路径字段里没有；格式 TXT 在题面里，PARAMS 没有对应的 kind、后缀或文件头 |
| `ps-2-15-ps-brushes-presets` | L2 | 通过 | 未覆盖 | 失败 | 真产物未覆盖：成品 out/ps-2-15-ps-brushes-presets.png 不在本机这几个目录里 题面失败：路径 e31-newapps/ps-2-15-seed.png 在题面里，PARAMS 的路径字段里没有 |
| `ps-2-15-ps-create-fill-patterns` | L2 | 通过 | 未覆盖 | 失败 | 真产物未覆盖：成品 out/ps-2-15-ps-create-fill-patterns.png 不在本机这几个目录里 题面失败：路径 seed/ps-2-15-ps-create-fill-patterns-seed.png 在题面里，PARAMS 的路径字段里没有；尺寸 16×16 在题面里，PARAMS 的 width/height 里没有这一对；尺寸 8×8 在题面里，PARAMS 的 width/height 里没有这一对 |
| `ps-2-15-ps-fill-objects-selections-layers` | L2 | 通过 | 未覆盖 | 失败 | 对照夹具不再是 1（reference=0） 真产物未覆盖：成品 out/ps-2-15-ps-fill-objects-selections-layers.png 不在本机这几个目录里 题面失败：路径 e31-newapps/seed-ps-2-15.png 在题面里，PARAMS 的路径字段里没有 |
| `ps-2-16-ps-draw-straight-line` | L2 | 通过 | 未覆盖 | 失败 | 真产物未覆盖：成品 out/ps-2-16-ps-draw-straight-line.png 不在本机这几个目录里 题面失败：路径 seeds/ps-2-16-instructions.txt 在题面里，PARAMS 的路径字段里没有；格式 TXT 在题面里，PARAMS 没有对应的 kind、后缀或文件头 |
| `ps-2-16-ps-pen-filled-shape` | L2 | 通过 | 未覆盖 | 失败 | 真产物未覆盖：成品 out/ps-2-16-ps-pen-filled-shape.png 不在本机这几个目录里 题面失败：路径 e31-newapps/ps-2-16-seed.png 在题面里，PARAMS 的路径字段里没有；路径 e31-newapps/ps-2-16-note.txt 在题面里，PARAMS 的路径字段里没有；格式 TXT 在题面里，PARAMS 没有对应的 kind、后缀或文件头 |
| `ps-2-16-ps-shape-rectangle` | L2 | 通过 | 未覆盖 | 失败 | 真产物未覆盖：成品 out/ps-2-16-ps-shape-rectangle.png 不在本机这几个目录里 题面失败：路径 seed/ps-2-16-ps-shape-rectangle-seed.png 在题面里，PARAMS 的路径字段里没有；路径 seed/ps-2-16-ps-shape-rectangle-notes.txt 在题面里，PARAMS 的路径字段里没有；格式 TXT 在题面里，PARAMS 没有对应的 kind、后缀或文件头 |
| `ps-2-16-ps-shape-star` | L2 | 通过 | 未覆盖 | 失败 | 真产物未覆盖：成品 out/ps-2-16-ps-shape-star.png 不在本机这几个目录里 题面失败：路径 e31-newapps/ps-2-16-ps-shape-star-instruction.txt 在题面里，PARAMS 的路径字段里没有；格式 TXT 在题面里，PARAMS 没有对应的 kind、后缀或文件头 |
| `ps-2-17-ps-text-font` | L2 | 通过 | 未覆盖 | 失败 | 真产物未覆盖：成品 out/ps-2-17-ps-text-font.png 不在本机这几个目录里；配套 seed/ps-2-17-ps-text-font-seed.png 不在本机这几个目录里 题面失败：数字 18（字号）在题面里，PARAMS 里没有这个数 |
| `ps-2-17-ps-text-on-path` | L2 | 通过 | 未覆盖 | 通过 | 对照夹具不再是 1（reference=0） 真产物未覆盖：成品 out/ps-2-17-ps-text-on-path.png 不在本机这几个目录里；配套 e31-newapps/ps-2-17-seed.png 不在本机这几个目录里 |
| `ps-2-18-blur` | L2 | 通过 | 未覆盖 | 失败 | 真产物未覆盖：成品 out/ps-2-18-blur.png 不在本机这几个目录里；配套 seeds/ps-2-18-blur-baseline.png 不在本机这几个目录里 题面失败：路径 seeds/ps-2-18-blur-seed.png 在题面里，PARAMS 的路径字段里没有 |
| `ps-2-18-quick-action` | L2 | 通过 | 未覆盖 | 通过 | 对照夹具不再是 1（reference=0） 真产物未覆盖：成品 out/ps-2-18-quick-action.png 不在本机这几个目录里；配套 e31-newapps/ps-2-18-quick-action-seed.png 不在本机这几个目录里 |
| `ps-2-18-sharpen` | L2 | 通过 | 未覆盖 | 通过 | 对照夹具不再是 1（reference=0） 真产物未覆盖：成品 out/ps-2-18-sharpen.png 不在本机这几个目录里；配套 seed/ps-2-18-sharpen-seed.png 不在本机这几个目录里 |
| `ps-2-18-stylize` | L2 | 通过 | 未覆盖 | 通过 | 对照夹具不再是 1（reference=0） 真产物未覆盖：成品 out/ps-2-18-stylize.png 不在本机这几个目录里；配套 e31-newapps/ps-2-18-stylize-seed.png 不在本机这几个目录里 |
| `ps-2-21-ps-action-play-on-image` | L2 | 通过 | 未覆盖 | 失败 | 对照夹具不再是 1（reference=0） 真产物未覆盖：成品 out/ps-2-21-ps-action-play-on-image.png 不在本机这几个目录里 题面失败：路径 in/ps-2-21-seed.png 在题面里，PARAMS 的路径字段里没有；路径 in/ps-2-21-instructions.txt 在题面里，PARAMS 的路径字段里没有；格式 TXT 在题面里，PARAMS 没有对应的 kind、后缀或文件头 |
| `ps-2-25-ps-export-transparent-png` | L2 | 通过 | 未覆盖 | 通过 | 真产物未覆盖：成品 out/ps-2-25-ps-export-transparent-png.png 不在本机这几个目录里 |
| `ps-2-25-ps-quick-export-png` | L2 | 通过 | 未覆盖 | 失败 | 对照夹具不再是 1（reference=0） 真产物未覆盖：成品 out/ps-2-25-ps-quick-export-png.png 不在本机这几个目录里 题面失败：路径 seed/ps-2-25-seed.png 在题面里，PARAMS 的路径字段里没有 |
| `ps-2-25-ps-save-as-format` | L1 | 通过 | 未覆盖 | 失败 | 对照夹具不再是 1（reference=0） 真产物未覆盖：成品 out/ps-2-25-ps-save-as-format.tif 不在本机这几个目录里 题面失败：路径 e31-newapps/ps-2-25-ps-save-as-format-seed.psd 在题面里，PARAMS 的路径字段里没有；格式 PSD 在题面里，PARAMS 没有对应的 kind、后缀或文件头 |
| `ps-2-25-ps-save-copy` | L2 | 通过 | 未覆盖 | 通过 | 对照夹具不再是 1（reference=0） 真产物未覆盖：成品 out/ps-2-25-ps-save-copy.png 不在本机这几个目录里；配套 seed/ps-2-25-ps-save-copy-seed.png 不在本机这几个目录里 |
| `ps-2-6-new-doc-custom` | L2 | 通过 | 未覆盖 | 通过 | 对照夹具不再是 1（reference=0） 真产物未覆盖：成品 out/ps-2-6-new-doc-custom.png 不在本机这几个目录里 |
| `ps-2-6-new-doc-preset` | L2 | 通过 | 未覆盖 | 失败 | 对照夹具不再是 1（reference=0） 真产物未覆盖：成品 out/ps-2-6-new-doc-preset.png 不在本机这几个目录里 题面失败：尺寸 1920×1080 在题面里，PARAMS 的 width/height 里没有这一对；数字 72（ppi）在题面里，PARAMS 里没有这个数 |
| `ps-2-8-artboard-new-doc` | L2 | 通过 | 未覆盖 | 失败 | 对照夹具不再是 1（reference=0） 真产物未覆盖：成品 out/ps-2-8-artboard-new-doc.png 不在本机这几个目录里 题面失败：路径 out/ps-2-8-artboard-new-doc.psd 在题面里，PARAMS 的路径字段里没有；格式 PSD 在题面里，PARAMS 没有对应的 kind、后缀或文件头 |
| `ps-2-8-frame-place-image` | L2 | 通过 | 未覆盖 | 失败 | 对照夹具不再是 1（reference=0） 真产物未覆盖：成品 out/ps-2-8-frame-place-image.png 不在本机这几个目录里 题面失败：路径 seed/ps-2-8-frame.psd 在题面里，PARAMS 的路径字段里没有；路径 seed/ps-2-8-photo.png 在题面里，PARAMS 的路径字段里没有；路径 out/ps-2-8-frame-place-image.psd 在题面里，PARAMS 的路径字段里没有；格式 PSD 在题面里，PARAMS 没有对应的 kind、后缀或文件头 |
| `ps-2-8-stroke-apply` | L2 | 通过 | 未覆盖 | 失败 | 真产物未覆盖：成品 out/ps-2-8-stroke-apply.png 不在本机这几个目录里 题面失败：路径 e31-newapps/e31-seed.png 在题面里，PARAMS 的路径字段里没有 |
| `ps-2-8-template-add-pattern` | L2 | 通过 | 未覆盖 | 失败 | 真产物未覆盖：成品 out/ps-2-8-template-add-pattern.png 不在本机这几个目录里 题面失败：路径 template.psd 在题面里，PARAMS 的路径字段里没有；格式 PSD 在题面里，PARAMS 没有对应的 kind、后缀或文件头 |
| `ps-2-9-crop-drag-edges` | L2 | 通过 | 未覆盖 | 失败 | 对照夹具不再是 1（reference=0） 真产物未覆盖：成品 out/ps-2-9-crop-drag-edges.png 不在本机这几个目录里 题面失败：路径 e31-newapps/seed-ps-2-9-crop-drag-edges.png 在题面里，PARAMS 的路径字段里没有；尺寸 64×48 在题面里，PARAMS 的 width/height 里没有这一对 |
| `ps-2-9-crop-nondestructive-restore` | L2 | 通过 | 未覆盖 | 失败 | 对照夹具不再是 1（reference=0） 真产物未覆盖：成品 out/ps-2-9-crop-nondestructive-restore-cropped.png 不在本机这几个目录里；成品 out/ps-2-9-crop-nondestructive-restore-restored.png 不在本机这几个目录里 题面失败：路径 e31-newapps/seed-ps-2-9.png 在题面里，PARAMS 的路径字段里没有 |
| `ps-2-9-crop-redraw-frame` | L2 | 通过 | 未覆盖 | 失败 | 对照夹具不再是 1（reference=0） 真产物未覆盖：成品 out/ps-2-9-crop-redraw-frame.png 不在本机这几个目录里 题面失败：路径 seed/ps-2-9-crop-redraw-frame-instruction.txt 在题面里，PARAMS 的路径字段里没有；格式 TXT 在题面里，PARAMS 没有对应的 kind、后缀或文件头 |
| `ps-2-9-crop-rotate-straighten` | L2 | 通过 | 未覆盖 | 失败 | 真产物未覆盖：成品 out/ps-2-9-crop-rotate-straighten.png 不在本机这几个目录里 题面失败：路径 e31-newapps/ps-2-9-crop-rotate-straighten-seed.png 在题面里，PARAMS 的路径字段里没有 |

## 这次实际跑了什么

- 题包：`/Users/zhangyingying/CUA/评测集建设/maccua-tasks/zyy-e31-gen-v4p`
- 目录里 109 道，可评分 46 道，手工 63 道。
- 评分库：`/Users/zhangyingying/CUA/评测集建设/maccua-tasks/_shared_tightened_1124_b`
- `e31_grade.py` SHA-256 前 12 位 `d59fa9c6649a`，`e31_grade_ext.py` `36a0cda51bd7`，`fixturelib.py` `2061119ad50c`。
- 真导出目录：
  - `/Users/zhangyingying/CUA/评测集建设/实验/E31_新应用Mail_PS_飞书_Figma刷数据/raw/figma导出图_1124`
  - `/Users/zhangyingying/CUA/评测集建设/实验/E31_新应用Mail_PS_飞书_Figma刷数据/raw/假阴性回归_1124/prod`
  - `/Users/zhangyingying/CUA/评测集建设/实验/E31_新应用Mail_PS_飞书_Figma刷数据/raw/假阴性回归_1124/seed`
  - `/Users/zhangyingying/CUA/评测集建设/实验/E31_新应用Mail_PS_飞书_Figma刷数据/raw/psd真文件_1124`
- 这四个目录里索引到 46 个文件，含种子和别的题包的导出。文件名以「结束截图」开头的没有拿来打分。
- 拦住的 osascript 次数：0。没有启动 osascript 进程。
- 假产物来自各题 `selftest.py` 里期望分数为 0 的用例，夹具函数是副本库里的 `fixturelib`。临时目录由夹具自己建。
- 题面门只做了机械对照：路径、格式词（PNG / JPEG / TIFF / PSD / PDF / SVG / TXT）、宽×高、括号里或 RGB 字样后面的三个颜色数、#RRGGBB、字号、点数、ppi、质量、单独写出的宽或高。同一个数只记一次。年份、1/30 这种分数、菜单名、字体名、「纯黑」这种没有数字的话，这次不抽。
- L0 是手工。L1 是只有魔数、后缀或署名。L2 是 PARAMS 里有尺寸、抽样、正文或图层这类书面条件。写了基线路径也停在 L2。

## 这次没跑

- G0 规格门：要人先写产物和判据，脚本不代写。
- G1 装配门：`tasks validate` 这次没跑。
- G2 自洽门的五项期望没有按旧库再对一遍。假产物门只要求期望 0 的用例在副本库下是 0。
- G4 归属门：`write_draft_baseline` 和 `write_flag_seal` 没有真跑，那要在生产机上写基线。
- 题面门没有调模型。11-24 那份模型对照是另一份结果，不在这次里。
- G7 真机冒烟、G8 停机保全、G9 人工金标准：没有生产机，也没有新的人工判定。
- 手工题的三道门没有跑。
