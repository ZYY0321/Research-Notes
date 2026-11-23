/**
 * 只用一条恒定关系重判存档里的模型框，不调模型、不连设备、不改交付代码。
 *
 * 恒定关系：被切内容 C 和切它的边 E（属于裁切者 K）之间，必须有能沿被切方向移动的视口；
 * 没有就是截断。布局树看不出来的情况按盲区分类，不硬判。
 *
 *   cd 验收/远端main/local/harmonyArena && npx tsx ../../../../scripts/截断检测/invariant_rejudge.mts <cases.json> <out.jsonl>
 *
 * cases.json: [{ id, label, layout, boxes: [{ issue_type, bbox(0~1000), truncated_edges?, slide_result?, final? }] }]
 */
import { readFileSync, writeFileSync } from "node:fs"
import path from "node:path"

const verifierDir = process.env.VERIFIER_DIR ?? path.resolve(process.cwd(), "src/text-trunc-verifier")
const L = await import(path.join(verifierDir, "layout.ts"))
type Rect = { left: number; top: number; right: number; bottom: number }
type Node = {
  index: number; parent_index: number | null; child_indices: number[]; depth: number; type: string
  text?: string; bounds?: Rect; orig_bounds?: Rect; visible: boolean; scrollable: boolean; clip: boolean
  attributes: Record<string, unknown>
}
type Side = "left" | "right" | "top" | "bottom"

function decodeEntities(value: string): string {
  return value
    .replace(/&#x([0-9a-f]+);/gi, (_, hex: string) => String.fromCodePoint(parseInt(hex, 16)))
    .replace(/&#(\d+);/g, (_, dec: string) => String.fromCodePoint(Number(dec)))
    .replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, "\"").replace(/&apos;/g, "'").replace(/&amp;/g, "&")
}
type DumpNode = { attributes: Record<string, string>; children: DumpNode[] }
function xmlToDump(xml: string): string {
  const root: DumpNode = { attributes: {}, children: [] }
  const stack: DumpNode[] = [root]
  const tag = /<(\/?)node\b((?:[^>"']|"[^"]*"|'[^']*')*?)(\/?)>/g
  const attr = /([\w:.-]+)\s*=\s*(?:"([^"]*)"|'([^']*)')/g
  for (let m = tag.exec(xml); m; m = tag.exec(xml)) {
    if (m[1]) { if (stack.length > 1) stack.pop(); continue }
    const node: DumpNode = { attributes: {}, children: [] }
    for (let a = attr.exec(m[2]); a; a = attr.exec(m[2])) node.attributes[a[1]] = decodeEntities(a[2] ?? a[3] ?? "")
    stack[stack.length - 1].children.push(node)
    if (!m[3]) stack.push(node)
  }
  return JSON.stringify(root.children.length === 1 ? root.children[0] : root)
}

const area = (r: Rect) => Math.max(0, r.right - r.left) * Math.max(0, r.bottom - r.top)
const inter = (a: Rect, b: Rect) => {
  const r = { left: Math.max(a.left, b.left), top: Math.max(a.top, b.top), right: Math.min(a.right, b.right), bottom: Math.min(a.bottom, b.bottom) }
  return r.right > r.left && r.bottom > r.top ? area(r) : 0
}
const SCROLL_TYPES = new Set(["Scroll", "List", "Grid", "WaterFlow", "Swiper", "Tabs", "TabContent"])
const PAGER_TYPES = new Set(["Swiper", "Tabs", "TabContent"])
const axisOf = (s: Side) => (s === "left" || s === "right" ? "horizontal" : "vertical")

function overflow(n: Node): Record<Side, number> {
  const b = n.bounds!, o = n.orig_bounds ?? n.bounds!
  return { left: b.left - o.left, right: o.right - b.right, top: b.top - o.top, bottom: o.bottom - b.bottom }
}

function findContent(nodes: Node[], box: Rect, issueType: string): Node | undefined {
  const boxArea = Math.max(1, area(box))
  let best: Node | undefined, bestScore = 0
  for (const n of nodes) {
    if (!n.visible || !n.bounds || area(n.bounds) <= 0) continue
    const isText = Boolean(n.text) || /Text|Span/.test(n.type)
    const isLeafish = n.child_indices.length === 0 || /Image|Button|Symbol/.test(n.type)
    if (issueType.includes("文字") ? !isText : !(isText || isLeafish)) continue
    const i = inter(n.bounds, box)
    if (i <= 0) continue
    const score = (i / boxArea) * (i / Math.max(1, area(n.bounds)))
    if (score > bestScore) { bestScore = score; best = n }
  }
  return bestScore >= 0.05 ? best : undefined
}

function isScrollContainer(n: Node) { return n.scrollable || SCROLL_TYPES.has(n.type) }

function axisMatches(n: Node, nodes: Node[], axis: string) {
  // 滚动方向常常不导出；宽扁的条按横向、细长的按竖向（同 B 版滑动代码的做法）
  if (n.bounds) {
    const w = n.bounds.right - n.bounds.left, h = n.bounds.bottom - n.bounds.top
    if (w >= 4 * h) return axis === "horizontal"
    if (h >= 4 * w) return axis === "vertical"
  }
  const info = L.inferScrollAxis(n, nodes)
  return info.axis === axis || info.axis === "unknown"
}

function hasCapacity(n: Node, nodes: Node[], side: Side, content: Node): boolean {
  const lim = (L.scrollContentLimit(n, nodes) as Rect | undefined) ?? content.orig_bounds ?? content.bounds!
  const vp = n.bounds!
  switch (side) {
    case "right": return lim.right > vp.right + 1
    case "left": return lim.left < vp.left - 1
    case "bottom": return lim.bottom > vp.bottom + 1
    case "top": return lim.top < vp.top - 1
  }
}

function occluders(nodes: Node[], c: Node, screen: Rect): Node[] {
  const cb = c.bounds!, ca = Math.max(1, area(cb))
  const out: Node[] = []
  for (const n of nodes) {
    if (n.index <= c.index || !n.visible || !n.bounds) continue
    if (L.isRelatedNode(n, c, nodes)) continue
    if (area(n.bounds) > 0.5 * area(screen)) continue
    if (inter(n.bounds, cb) / ca >= 0.2) out.push(n)
  }
  return out
}

type Verdict = { pred: "truncation" | "not_truncation" | "undecided"; cls: string; detail: Record<string, unknown> }

function judge(nodes: Node[], screen: Rect, box: { issue_type: string; bbox: number[]; truncated_edges?: string[] }): Verdict {
  const b = L.norm1000ToLayout(box.bbox as [number, number, number, number], screen) as Rect
  const c = findContent(nodes, b, box.issue_type)
  if (!c) return { pred: "undecided", cls: "盲区:内容不在树里（自绘或框对不上节点）", detail: {} }
  const ov = overflow(c)
  const want = (box.truncated_edges ?? []).filter((s): s is Side => ["left", "right", "top", "bottom"].includes(s))
  const sides = (["left", "right", "top", "bottom"] as Side[]).filter((s) => ov[s] > 1)
  const side = want.find((s) => ov[s] > 1) ?? sides.sort((x, y) => ov[y] - ov[x])[0]
  const base = { node: c.index, type: c.type, text: c.text?.slice(0, 40), overflow: ov }
  if (!side) {
    const occ = occluders(nodes, c, screen)
    if (occ.length) return { pred: "undecided", cls: "盲区:被兄弟组件盖住（树上无裁切）", detail: { ...base, occluder: occ.slice(0, 3).map((n) => `${n.index}:${n.type}`) } }
    return { pred: "undecided", cls: "盲区:树上看不出被切（自裁切/省略号/模型误标）", detail: base }
  }
  const o = c.orig_bounds ?? c.bounds!
  const size = axisOf(side) === "horizontal" ? o.right - o.left : o.bottom - o.top
  const ratio = ov[side] / Math.max(1, size)
  if (ratio < 0.15) return { pred: "undecided", cls: "盲区:只裁掉行框边缘（<15%）", detail: { ...base, side, ratio } }

  const anc = L.ancestorsOf(c, nodes) as Node[]
  const cutEdge = side === "right" ? c.bounds!.right : side === "left" ? c.bounds!.left : side === "bottom" ? c.bounds!.bottom : c.bounds!.top
  let k = -1
  for (let i = 0; i < anc.length; i++) {
    const a = anc[i]
    if (!a.bounds) continue
    const e = side === "right" ? a.bounds.right : side === "left" ? a.bounds.left : side === "bottom" ? a.bounds.bottom : a.bounds.top
    // 自己也在这一侧被切的祖先只是跟着一起被切的包装层，不是裁切者
    if (Math.abs(e - cutEdge) <= 3 && overflow(a)[side] <= 1) { k = i; break }
  }
  const atScreen = Math.abs(cutEdge - (side === "right" ? screen.right : side === "left" ? screen.left : side === "bottom" ? screen.bottom : screen.top)) <= 3
  const axis = axisOf(side)
  const between = k >= 0 ? anc.slice(0, k) : anc
  const K = k >= 0 ? anc[k] : undefined
  const detail = { ...base, side, ratio, clipper: K ? `${K.index}:${K.type}` : atScreen ? "屏幕边" : "找不到" }

  if (!K && !atScreen) return { pred: "undecided", cls: "盲区:找不到裁切者", detail }

  if (K && isScrollContainer(K) && axisMatches(K, nodes, axis)) {
    if (PAGER_TYPES.has(K.type) || L.scrollBehavior(K) === "page_switch") {
      const vis = inter(c.orig_bounds ?? c.bounds!, K.bounds!) / Math.max(1, area(c.orig_bounds ?? c.bounds!))
      return vis < 0.5
        ? { pred: "not_truncation", cls: "成立:翻页容器露出邻页", detail: { ...detail, visible: vis } }
        : { pred: "undecided", cls: "盲区:翻页容器当前页不明", detail: { ...detail, visible: vis } }
    }
    return hasCapacity(K, nodes, side, c)
      ? { pred: "not_truncation", cls: "成立:切口是可滚视口的边", detail }
      : { pred: "truncation", cls: "违反:可滚视口已到头", detail }
  }
  const movers = (K ? between : anc).filter((a) => a.bounds && isScrollContainer(a) && axisMatches(a, nodes, axis))
  if (K) {
    const inner = movers.find((a) => hasCapacity(a, nodes, side, c))
    if (inner) return { pred: "not_truncation", cls: "成立:裁切者里面有可滚视口", detail: { ...detail, mover: `${inner.index}:${inner.type}` } }
    return { pred: "truncation", cls: "违反:裁切者跟着内容动（中间没有可动视口）", detail }
  }
  const outer = movers.find((a) => hasCapacity(a, nodes, side, c))
  if (outer) return { pred: "not_truncation", cls: "成立:被屏幕边切、外层可滚", detail: { ...detail, mover: `${outer.index}:${outer.type}` } }
  return { pred: "truncation", cls: "违反:被屏幕边切、没有可滚视口", detail }
}

const [casesPath, outPath] = process.argv.slice(2)
const cases = JSON.parse(readFileSync(casesPath, "utf8"))
const lines: string[] = []
for (const cs of cases) {
  let parsed
  try {
    const raw = readFileSync(cs.layout, "utf8")
    parsed = L.parseLayout(path.extname(cs.layout).toLowerCase() === ".xml" ? xmlToDump(raw) : raw)
  } catch (error) {
    lines.push(JSON.stringify({ id: cs.id, error: String(error) }))
    continue
  }
  cs.boxes.forEach((box: any, i: number) => {
    const v = judge(parsed.nodes, parsed.screen, box)
    lines.push(JSON.stringify({ id: cs.id, label: cs.label, box_index: i, issue_type: box.issue_type, bbox: box.bbox, edges: box.truncated_edges, slide_result: box.slide_result, final: box.final, truth: box.truth, ...v }))
  })
}
writeFileSync(outPath, lines.join("\n") + "\n")
console.log(`写出 ${lines.length} 条 → ${outPath}`)
