# 算法手撕 35 题 · 极简背诵版（C++）

> **极简原则**：每道题严格只留 **「标题 + 题目描述 + 一段核心思路（含复杂度）+ 一段标准代码」**，零废话冗余。涵盖全部 2025–2026 大厂 Agent/大模型面经出现过的真题及你去年 `刷题.docx` / `Hot100` 的高频精华。

```cpp
// 通用头文件与节点定义（白板默认前置）
#include <bits/stdc++.h>
using namespace std;
struct ListNode { int val; ListNode *next; ListNode(int x) : val(x), next(nullptr) {} };
struct TreeNode { int val; TreeNode *left, *right; TreeNode(int x) : val(x), left(nullptr), right(nullptr) {} };
```

---

## 一、哈希与滑动窗口

### 1. 两数之和（LC 1）
**题目描述**：给定整数数组 `nums` 和整数 `target`，返回和为 `target` 的两个元素的数组下标。
**核心思路**：遍历数组，用哈希表记录已访问过的 `数值 -> 下标`；每到一个数 `x` 先查 `target - x` 是否在表中，命中即返回，否则存入当前数。时间 $O(n)$，空间 $O(n)$。
```cpp
class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        unordered_map<int, int> mp;
        for (int i = 0; i < (int)nums.size(); ++i) {
            auto it = mp.find(target - nums[i]);
            if (it != mp.end()) return {it->second, i};
            mp[nums[i]] = i;
        }
        return {};
    }
};
```

### 2. 字母异位词分组（LC 49 · 阿里国际真题）
**题目描述**：给你一个字符串数组 `strs`，请你将字母异位词组合在一起返回。
**核心思路**：异位词排序后完全相同。将每个字符串拷贝并升序排序作为哈希表 `key`，原串归入对应 `vector`，最后导出全部桶即可。时间 $O(nk\log k)$，空间 $O(nk)$。
```cpp
class Solution {
public:
    vector<vector<string>> groupAnagrams(vector<string>& strs) {
        unordered_map<string, vector<string>> mp;
        for (const string& s : strs) {
            string key = s;
            sort(key.begin(), key.end());
            mp[key].push_back(s);
        }
        vector<vector<string>> res;
        for (auto& [k, v] : mp) res.push_back(std::move(v));
        return res;
    }
};
```

### 3. 最长连续序列（LC 128）
**题目描述**：给定未排序整数数组 `nums`，找出数字连续的最长序列长度，要求时间复杂度 $O(n)$。
**核心思路**：将所有数放入 `unordered_set` 去重；只对集合中不存在前驱 `x - 1` 的“序列起点”向后枚举 `x + 1, x + 2...` 统计长度，保证每个元素最多被内层循环访问一次。时间 $O(n)$，空间 $O(n)$。
```cpp
class Solution {
public:
    int longestConsecutive(vector<int>& nums) {
        unordered_set<int> st(nums.begin(), nums.end());
        int ans = 0;
        for (int x : st) {
            if (!st.count(x - 1)) {
                int cur = x;
                while (st.count(cur + 1)) ++cur;
                ans = max(ans, cur - x + 1);
            }
        }
        return ans;
    }
};
```

### 4. 无重复字符的最长子串（LC 3 · 淘天/阿里国际真题）
**题目描述**：给定字符串 `s`，请你找出其中不含有重复字符的最长连续子串的长度。
**核心思路**：滑动窗口维护无重复区间 `[left, r]`，用大小为 256 的数组 `last` 记录每个字符上次出现的下标；若 `last[c] >= left` 说明窗口内重复，将 `left` 直接跳到 `last[c] + 1`，更新最大窗口长度。时间 $O(n)$，空间 $O(1)$。
```cpp
class Solution {
public:
    int lengthOfLongestSubstring(string s) {
        vector<int> last(256, -1);
        int ans = 0, left = 0;
        for (int r = 0; r < (int)s.size(); ++r) {
            unsigned char c = s[r];
            if (last[c] >= left) left = last[c] + 1;
            last[c] = r;
            ans = max(ans, r - left + 1);
        }
        return ans;
    }
};
```

### 5. 最小覆盖子串（LC 76）
**题目描述**：给你字符串 `s` 和 `t`，返回 `s` 中涵盖 `t` 所有字符（含频次）的最短子串；不存在则返回空串。
**核心思路**：滑动窗口统计需求差值 `need[c]` 与剩余欠缺字符总数 `missing`。右指针右移补齐字符直至 `missing == 0`，随后尽量右移左指针收缩冗余字符并更新最短起点与长度。时间 $O(|s|+|t|)$，空间 $O(1)$。
```cpp
class Solution {
public:
    string minWindow(string s, string t) {
        int need[256] = {0}, missing = t.size();
        for (unsigned char c : t) ++need[c];
        int l = 0, bestL = 0, minLen = INT_MAX;
        for (int r = 0; r < (int)s.size(); ++r) {
            if (need[(unsigned char)s[r]]-- > 0) --missing;
            while (missing == 0) {
                if (r - l + 1 < minLen) { minLen = r - l + 1; bestL = l; }
                if (++need[(unsigned char)s[l++]] > 0) ++missing;
            }
        }
        return minLen == INT_MAX ? "" : s.substr(bestL, minLen);
    }
};
```

### 6. 和为 K 的子数组（LC 560）
**题目描述**：给你一个整数数组 `nums` 和一个整数 `k`，统计并返回该数组中和为 `k` 的连续子数组的个数。
**核心思路**：数组含负数不能滑窗，用前缀和 + 哈希表记录历史前缀和出现的次数（初始 `cnt[0] = 1`）；走到当前前缀和 `sum` 时，`cnt[sum - k]` 即以当前位置结尾且和为 `k` 的子数组数。时间 $O(n)$，空间 $O(n)$。
```cpp
class Solution {
public:
    int subarraySum(vector<int>& nums, int k) {
        unordered_map<long long, int> cnt;
        cnt[0] = 1;
        long long sum = 0;
        int ans = 0;
        for (int x : nums) {
            sum += x;
            if (cnt.count(sum - k)) ans += cnt[sum - k];
            ++cnt[sum];
        }
        return ans;
    }
};
```

---

## 二、双指针、区间与单调结构

### 7. 三数之和（LC 15）
**题目描述**：给你整数数组 `nums`，返回所有和为 `0` 且不重复的三元组 `[nums[i], nums[j], nums[k]]`。
**核心思路**：先升序排序，外层枚举第一个数 `nums[i]`（跳过重复值），内层用左右双指针 `l, r` 在 `[i+1, n-1]` 夹逼寻找和为 `-nums[i]` 的组合，命中后同步跳过左右重复元素。时间 $O(n^2)$，空间 $O(\log n)$。
```cpp
class Solution {
public:
    vector<vector<int>> threeSum(vector<int>& nums) {
        sort(nums.begin(), nums.end());
        vector<vector<int>> res;
        int n = nums.size();
        for (int i = 0; i < n - 2; ++i) {
            if (nums[i] > 0) break;
            if (i > 0 && nums[i] == nums[i - 1]) continue;
            int l = i + 1, r = n - 1;
            while (l < r) {
                int s = nums[i] + nums[l] + nums[r];
                if (s < 0) ++l;
                else if (s > 0) --r;
                else {
                    res.push_back({nums[i], nums[l++], nums[r--]});
                    while (l < r && nums[l] == nums[l - 1]) ++l;
                    while (l < r && nums[r] == nums[r + 1]) --r;
                }
            }
        }
        return res;
    }
};
```

### 8. 盛最多水的容器（LC 11）
**题目描述**：给定高度数组 `height`，找出两条垂线与 x 轴构成的容器所能容纳的最大水量。
**核心思路**：左右双指针从两端向内收缩，当前水量为 `min(h[l], h[r]) * (r - l)`；每次移动较矮一侧的指针（移动较高侧宽度变小且受限于矮侧，容量必不可能变大）。时间 $O(n)$，空间 $O(1)$。
```cpp
class Solution {
public:
    int maxArea(vector<int>& height) {
        int l = 0, r = (int)height.size() - 1, ans = 0;
        while (l < r) {
            ans = max(ans, min(height[l], height[r]) * (r - l));
            if (height[l] < height[r]) ++l;
            else --r;
        }
        return ans;
    }
};
```

### 9. 接雨水（LC 42 · 阿里 Offer 场真题）
**题目描述**：给定 `n` 个非负整数表示柱子高度图，计算下雨之后能接多少雨水。
**核心思路**：双指针维护前缀最高 `lmax` 和后缀最高 `rmax`。每次处理较矮一侧：若 `height[l] < height[r]`，右侧必有更高墙兜底，当前格水位完全由 `lmax` 决定，累加 `lmax - height[l]` 后右移 `l`；反之同理。时间 $O(n)$，空间 $O(1)$。
```cpp
class Solution {
public:
    int trap(vector<int>& height) {
        int l = 0, r = (int)height.size() - 1, lmax = 0, rmax = 0, ans = 0;
        while (l < r) {
            if (height[l] < height[r]) {
                lmax = max(lmax, height[l]);
                ans += lmax - height[l++];
            } else {
                rmax = max(rmax, height[r]);
                ans += rmax - height[r--];
            }
        }
        return ans;
    }
};
```

### 10. 滑动窗口最大值（LC 239）
**题目描述**：给你整数数组 `nums` 和大小为 `k` 的滑动窗口，返回窗口每次右移一位时的最大值数组。
**核心思路**：用双端队列 `deque` 存下标，维持对应元素单调递减。新元素入队前从队尾弹出所有小于等于它的下标；队首若滑出窗口左界 `i - k` 则从队首弹出；当 `i >= k - 1` 时队首即当前窗口最大值。时间 $O(n)$，空间 $O(k)$。
```cpp
class Solution {
public:
    vector<int> maxSlidingWindow(vector<int>& nums, int k) {
        deque<int> dq;
        vector<int> res;
        for (int i = 0; i < (int)nums.size(); ++i) {
            while (!dq.empty() && nums[dq.back()] <= nums[i]) dq.pop_back();
            dq.push_back(i);
            if (dq.front() <= i - k) dq.pop_front();
            if (i >= k - 1) res.push_back(nums[dq.front()]);
        }
        return res;
    }
};
```

### 11. 合并区间（LC 56）
**题目描述**：以数组 `intervals` 表示若干区间，合并所有重叠的区间并返回不重叠区间数组。
**核心思路**：按区间左端点升序排序，顺序遍历：若结果集为空或当前左端点大于结果末尾右端点则直接追加，否则更新末尾右端点为两者较大值。时间 $O(n\log n)$，空间 $O(\log n)$。
```cpp
class Solution {
public:
    vector<vector<int>> merge(vector<vector<int>>& intervals) {
        sort(intervals.begin(), intervals.end());
        vector<vector<int>> res;
        for (auto& in : intervals) {
            if (res.empty() || res.back()[1] < in[0]) res.push_back(in);
            else res.back()[1] = max(res.back()[1], in[1]);
        }
        return res;
    }
};
```

### 12. 每日温度（LC 739）
**题目描述**：给定每日气温数组 `temperatures`，返回每天需要等多少天才会遇到更高温度（没有则填 0）。
**核心思路**：维护存下标的单调递减栈。遍历到第 `i` 天，只要当前温度高于栈顶那天的温度，就弹出栈顶 `idx` 并填答案 `i - idx`，最后将 `i` 压栈。时间 $O(n)$，空间 $O(n)$。
```cpp
class Solution {
public:
    vector<int> dailyTemperatures(vector<int>& temperatures) {
        int n = temperatures.size();
        vector<int> ans(n, 0);
        stack<int> st;
        for (int i = 0; i < n; ++i) {
            while (!st.empty() && temperatures[i] > temperatures[st.top()]) {
                int idx = st.top(); st.pop();
                ans[idx] = i - idx;
            }
            st.push(i);
        }
        return ans;
    }
};
```

---

## 三、链表与经典数据结构设计

### 13. 反转链表 & K 个一组翻转链表（LC 206 & LC 25）
**题目描述**：给你链表头节点 `head`，每 `k` 个节点一组进行翻转，剩余不足 `k` 个保持原序，返回修改后的头节点。
**核心思路**：设哨兵头 `dummy`，每次先探路确认剩余够 `k` 个节点，再用标准三指针原地翻转这 `k` 个节点并重新接回前后驱。时间 $O(n)$，空间 $O(1)$。
```cpp
class Solution {
public:
    ListNode* reverseKGroup(ListNode* head, int k) {
        ListNode dummy(0); dummy.next = head;
        ListNode* pre = &dummy;
        while (true) {
            ListNode* tail = pre;
            for (int i = 0; i < k && tail; ++i) tail = tail->next;
            if (!tail) break;
            ListNode *nxtGroup = tail->next, *cur = pre->next, *prev = nxtGroup;
            while (cur != nxtGroup) {
                ListNode* tmp = cur->next;
                cur->next = prev;
                prev = cur;
                cur = tmp;
            }
            ListNode* newTail = pre->next;
            pre->next = tail;
            pre = newTail;
        }
        return dummy.next;
    }
};
```

### 14. 环形链表 II —— 找入环第一个节点（LC 142 · 阿里 P1 真题）
**题目描述**：给定链表 `head`，若存在环则返回入环的第一个节点，无环返回 `nullptr`。
**核心思路**：快慢指针（快 2 步慢 1 步）判环；相遇时设头到入口为 $a$、入口到相遇点为 $b$、环长为 $c$，由 $2(a+b)=a+b+kc$ 得 $a=kc-b$，故令新指针从 `head` 与 `slow` 同步每次走 1 步，必在入口相遇。时间 $O(n)$，空间 $O(1)$。
```cpp
class Solution {
public:
    ListNode* detectCycle(ListNode* head) {
        ListNode *slow = head, *fast = head;
        while (fast && fast->next) {
            slow = slow->next;
            fast = fast->next->next;
            if (slow == fast) {
                ListNode* p = head;
                while (p != slow) { p = p->next; slow = slow->next; }
                return p;
            }
        }
        return nullptr;
    }
};
```

### 15. 相交链表（LC 160 · 阿里 P1 真题）
**题目描述**：给你两个单链表的头节点 `headA` 和 `headB`，找出并返回两个单链表相交的起始节点（不相交返回 `nullptr`）。
**核心思路**：双指针 `a, b` 分别从两头出发，走到空指针时切换到另一条链表的头节点继续走；两指针总路程同为 `lenA + lenB`，必在交点或末尾 `nullptr` 同时相遇。时间 $O(m+n)$，空间 $O(1)$。
```cpp
class Solution {
public:
    ListNode* getIntersectionNode(ListNode* headA, ListNode* headB) {
        ListNode *a = headA, *b = headB;
        while (a != b) {
            a = a ? a->next : headB;
            b = b ? b->next : headA;
        }
        return a;
    }
};
```

### 16. 排序链表（LC 148 · 阿里二面真题）
**题目描述**：给你链表的头结点 `head`，请将其按升序排列并返回（要求 $O(n\log n)$ 时间）。
**核心思路**：链表归并排序。快慢指针（`fast` 从 `head->next` 起步使 `slow` 停在左半尾）找中点断链，左右递归排好序后用哨兵节点合并两条有序链表。时间 $O(n\log n)$，空间 $O(\log n)$。
```cpp
class Solution {
    ListNode* merge(ListNode* a, ListNode* b) {
        ListNode dummy(0), *t = &dummy;
        while (a && b) {
            if (a->val <= b->val) { t->next = a; a = a->next; }
            else { t->next = b; b = b->next; }
            t = t->next;
        }
        t->next = a ? a : b;
        return dummy.next;
    }
public:
    ListNode* sortList(ListNode* head) {
        if (!head || !head->next) return head;
        ListNode *slow = head, *fast = head->next;
        while (fast && fast->next) { slow = slow->next; fast = fast->next->next; }
        ListNode* mid = slow->next;
        slow->next = nullptr;
        return merge(sortList(head), sortList(mid));
    }
};
```

### 17. 合并 K 个升序链表（LC 23）
**题目描述**：给你一个链表数组 `lists`，每个链表均已按升序排列，请将所有链表合并到一个升序链表中返回。
**核心思路**：用小顶堆维护当前所有非空链表的头节点，每次弹出值最小节点接到结果链表末尾，并将其 `next`（若非空）压入堆中。时间 $O(N\log k)$，空间 $O(k)$。
```cpp
class Solution {
public:
    ListNode* mergeKLists(vector<ListNode*>& lists) {
        auto cmp = [](ListNode* a, ListNode* b) { return a->val > b->val; };
        priority_queue<ListNode*, vector<ListNode*>, decltype(cmp)> pq(cmp);
        for (auto p : lists) if (p) pq.push(p);
        ListNode dummy(0), *tail = &dummy;
        while (!pq.empty()) {
            ListNode* cur = pq.top(); pq.pop();
            tail->next = cur; tail = cur;
            if (cur->next) pq.push(cur->next);
        }
        return dummy.next;
    }
};
```

### 18. LRU 缓存（LC 146 · 阿里国际真题）
**题目描述**：设计并实现满足 LRU（最近最少使用）约束的数据结构，要求 `get(key)` 和 `put(key, value)` 均为 $O(1)$ 时间。
**核心思路**：`unordered_map` 存 `key -> 链表迭代器` 实现 $O(1)$ 查找，双向链表 `std::list<pair<int,int>>` 维护访问时序（头最新、尾最旧）；命中或更新时用 `splice` 移到表头，满容插入时淘汰尾节点并按其 `key` 删除哈希项。时间 $O(1)$，空间 $O(\text{capacity})$。
```cpp
class LRUCache {
    int cap_;
    list<pair<int, int>> items_;
    unordered_map<int, list<pair<int, int>>::iterator> pos_;
public:
    LRUCache(int capacity) : cap_(capacity) {}
    int get(int key) {
        auto it = pos_.find(key);
        if (it == pos_.end()) return -1;
        items_.splice(items_.begin(), items_, it->second);
        return it->second->second;
    }
    void put(int key, int value) {
        auto it = pos_.find(key);
        if (it != pos_.end()) {
            it->second->second = value;
            items_.splice(items_.begin(), items_, it->second);
            return;
        }
        if ((int)items_.size() == cap_) {
            pos_.erase(items_.back().first);
            items_.pop_back();
        }
        items_.emplace_front(key, value);
        pos_[key] = items_.begin();
    }
};
```

### 19. O(1) 时间插入、删除和获取随机元素（LC 380 · 阿里 P1 真题）
**题目描述**：实现 `RandomizedSet` 类，支持平均 $O(1)$ 时间 `insert`、`remove` 与等概率 `getRandom`。
**核心思路**：动态数组 `nums` 支持 $O(1)$ 随机下标访问，哈希表 `idx` 记录 `值 -> 数组下标`；删除元素时用数组末尾元素覆盖被删槽位，先更新末尾元素在哈希表中的下标，再 `pop_back` 与 `erase`。时间均摊 $O(1)$，空间 $O(n)$。
```cpp
class RandomizedSet {
    vector<int> nums_;
    unordered_map<int, int> idx_;
    mt19937 rng_{random_device{}()};
public:
    bool insert(int val) {
        if (idx_.count(val)) return false;
        idx_[val] = nums_.size();
        nums_.push_back(val);
        return true;
    }
    bool remove(int val) {
        auto it = idx_.find(val);
        if (it == idx_.end()) return false;
        int i = it->second, last = nums_.back();
        nums_[i] = last;
        idx_[last] = i;
        nums_.pop_back();
        idx_.erase(val);
        return true;
    }
    int getRandom() {
        return nums_[uniform_int_distribution<int>(0, (int)nums_.size() - 1)(rng_)];
    }
};
```

---

## 四、二叉树、图论、二分与分治

### 20. 二叉树的最近公共祖先（LC 236 · 阿里国际真题）
**题目描述**：给定一个二叉树，找到该树中两个指定节点 `p` 和 `q` 的最近公共祖先。
**核心思路**：后序递归。若 `root` 为空或等于 `p/q` 直接返回 `root`；递归查左右子树，若左右返回值均非空说明 `p, q` 分居两侧，当前 `root` 即答案；否则将非空一侧结果向上传递。时间 $O(n)$，空间 $O(h)$。
```cpp
class Solution {
public:
    TreeNode* lowestCommonAncestor(TreeNode* root, TreeNode* p, TreeNode* q) {
        if (!root || root == p || root == q) return root;
        TreeNode* l = lowestCommonAncestor(root->left, p, q);
        TreeNode* r = lowestCommonAncestor(root->right, p, q);
        if (l && r) return root;
        return l ? l : r;
    }
};
```

### 21. 二叉树的层序遍历（LC 102）
**题目描述**：给你二叉树的根节点 `root`，返回其节点值的逐层从左到右层序遍历结果。
**核心思路**：队列 BFS，每轮开始前取当前队列长度 `sz` 代表本层节点个数，循环弹出 `sz` 个节点收集值并将其非空左右孩子入队。时间 $O(n)$，空间 $O(n)$。
```cpp
class Solution {
public:
    vector<vector<int>> levelOrder(TreeNode* root) {
        vector<vector<int>> res;
        if (!root) return res;
        queue<TreeNode*> q; q.push(root);
        while (!q.empty()) {
            int sz = q.size();
            vector<int> lv; lv.reserve(sz);
            while (sz--) {
                TreeNode* u = q.front(); q.pop();
                lv.push_back(u->val);
                if (u->left) q.push(u->left);
                if (u->right) q.push(u->right);
            }
            res.push_back(std::move(lv));
        }
        return res;
    }
};
```

### 22. 二叉树中的最大路径和（LC 124）
**题目描述**：路径被定义为一条节点序列，同一个节点至多出现一次，返回非空路径的最大节点值之和。
**核心思路**：后序 DFS 计算以当前节点为端点向下延伸的最大单链贡献 `max(0, dfs(child))`；经过当前节点拐弯的完整路径和为 `u->val + leftGain + rightGain` 用以更新全局答案，向上仅返回单侧较大支路 `u->val + max(leftGain, rightGain)`。时间 $O(n)$，空间 $O(h)$。
```cpp
class Solution {
    int ans = INT_MIN;
    int gain(TreeNode* u) {
        if (!u) return 0;
        int l = max(0, gain(u->left)), r = max(0, gain(u->right));
        ans = max(ans, u->val + l + r);
        return u->val + max(l, r);
    }
public:
    int maxPathSum(TreeNode* root) { gain(root); return ans; }
};
```

### 23. 岛屿数量（LC 200 · 淘天/阿里国际固定真题）
**题目描述**：给你由 `'1'`（陆地）和 `'0'`（水）组成的二维网格，请你计算网格中岛屿（四连通块）的数量。
**核心思路**：双重循环扫描网格，每遇到 `'1'` 则岛屿计数加 1，并启动 DFS（或队列 BFS）将该连通块内所有相连的 `'1'` 原地置为 `'0'`（沉岛防重访）。时间 $O(mn)$，空间最坏 $O(mn)$。
```cpp
class Solution {
    void dfs(vector<vector<char>>& g, int i, int j) {
        if (i < 0 || i >= (int)g.size() || j < 0 || j >= (int)g[0].size() || g[i][j] != '1') return;
        g[i][j] = '0';
        dfs(g, i + 1, j); dfs(g, i - 1, j);
        dfs(g, i, j + 1); dfs(g, i, j - 1);
    }
public:
    int numIslands(vector<vector<char>>& grid) {
        int cnt = 0;
        for (int i = 0; i < (int)grid.size(); ++i)
            for (int j = 0; j < (int)grid[0].size(); ++j)
                if (grid[i][j] == '1') { ++cnt; dfs(grid, i, j); }
        return cnt;
    }
};
```

### 24. 课程表 —— 拓扑排序判有向图环（LC 207）
**题目描述**：共 `numCourses` 门课及先修依赖对 `prerequisites`，判断是否可能完成所有课程学习。
**核心思路**：建邻接表与入度数组，将所有初始入度为 0 的课入队做 Kahn 拓扑排序；每次出队计数加 1 并将后继入度减 1，减至 0 则入队，最终修完数等于总课数即无环可行。时间 $O(V+E)$，空间 $O(V+E)$。
```cpp
class Solution {
public:
    bool canFinish(int numCourses, vector<vector<int>>& prerequisites) {
        vector<vector<int>> adj(numCourses);
        vector<int> indeg(numCourses, 0);
        for (auto& e : prerequisites) { adj[e[1]].push_back(e[0]); ++indeg[e[0]]; }
        queue<int> q;
        for (int i = 0; i < numCourses; ++i) if (indeg[i] == 0) q.push(i);
        int done = 0;
        while (!q.empty()) {
            int u = q.front(); q.pop(); ++done;
            for (int v : adj[u]) if (--indeg[v] == 0) q.push(v);
        }
        return done == numCourses;
    }
};
```

### 25. 寻找两个正序数组的中位数（LC 4 · 阿里 Agentic RL 二面真题）
**题目描述**：给定两个大小分别为 `m` 和 `n` 的正序数组，以 $O(\log(\min(m, n)))$ 时间找出两数组合并后的中位数。
**核心思路**：在较短数组 `nums1` 上二分左半部分切分点 `i`（范围 `[0, m]`），另一数组切点固定为 `j = (m + n + 1) / 2 - i`，越界处用 `INT_MIN/INT_MAX` 哨兵兜底；当满足交叉有序 `l1 <= r2 && l2 <= r1` 时命中切割线。时间 $O(\log\min(m,n))$，空间 $O(1)$。
```cpp
class Solution {
public:
    double findMedianSortedArrays(vector<int>& nums1, vector<int>& nums2) {
        if (nums1.size() > nums2.size()) return findMedianSortedArrays(nums2, nums1);
        int m = nums1.size(), n = nums2.size(), lo = 0, hi = m, half = (m + n + 1) / 2;
        while (lo <= hi) {
            int i = lo + (hi - lo) / 2, j = half - i;
            int l1 = (i == 0) ? INT_MIN : nums1[i - 1], r1 = (i == m) ? INT_MAX : nums1[i];
            int l2 = (j == 0) ? INT_MIN : nums2[j - 1], r2 = (j == n) ? INT_MAX : nums2[j];
            if (l1 <= r2 && l2 <= r1) {
                if ((m + n) & 1) return max(l1, l2);
                return ((long long)max(l1, l2) + min(r1, r2)) / 2.0;
            } else if (l1 > r2) hi = i - 1;
            else lo = i + 1;
        }
        return 0.0;
    }
};
```

### 26. 搜索旋转排序数组（LC 33）
**题目描述**：整数升序数组在未知点旋转（无重复元素），在 $O(\log n)$ 时间内搜索 `target` 下标（不存在返 -1）。
**核心思路**：二分取 `mid`，`[lo, mid]` 和 `[mid, hi]` 至少有一半严格有序；判断哪半有序并检查 `target` 是否落在该有序区间值域内，命中则缩向该半，否则去另一半。时间 $O(\log n)$，空间 $O(1)$。
```cpp
class Solution {
public:
    int search(vector<int>& nums, int target) {
        int lo = 0, hi = (int)nums.size() - 1;
        while (lo <= hi) {
            int mid = lo + (hi - lo) / 2;
            if (nums[mid] == target) return mid;
            if (nums[lo] <= nums[mid]) {
                if (nums[lo] <= target && target < nums[mid]) hi = mid - 1;
                else lo = mid + 1;
            } else {
                if (nums[mid] < target && target <= nums[hi]) lo = mid + 1;
                else hi = mid - 1;
            }
        }
        return -1;
    }
};
```

### 27. 数组中的第 K 个最大元素（LC 215 · 阿里 P1 真题）
**题目描述**：给定整数数组 `nums` 和整数 `k`，返回数组中第 `k` 个最大的元素（要求 $O(n)$ 期望时间）。
**核心思路**：转换目标为升序下标 `target = n - k`，用随机化三路快速选择（划分为 `< pivot`、`== pivot`、`> pivot` 三段，防大量重复元素退化为 $O(n^2)$）只递归包含 `target` 的那一段。期望时间 $O(n)$，空间 $O(1)$。
```cpp
class Solution {
public:
    int findKthLargest(vector<int>& nums, int k) {
        int n = nums.size(), target = n - k, lo = 0, hi = n - 1;
        mt19937 rng(random_device{}());
        while (lo <= hi) {
            int pivot = nums[lo + rng() % (hi - lo + 1)];
            int lt = lo, i = lo, gt = hi;
            while (i <= gt) {
                if (nums[i] < pivot) swap(nums[i++], nums[lt++]);
                else if (nums[i] > pivot) swap(nums[i], nums[gt--]);
                else ++i;
            }
            if (target < lt) hi = lt - 1;
            else if (target > gt) lo = gt + 1;
            else return pivot;
        }
        return -1;
    }
};
```

### 28. 前 K 个高频元素（LC 347 · 阿里 P1 真题）
**题目描述**：给你整数数组 `nums` 和整数 `k`，请你返回其中出现频率前 `k` 高的元素。
**核心思路**：先用哈希表统计每个数的频次，再维护容量为 `k` 的小顶堆（存 `{频次, 数值}`），超出 `k` 个即弹出当前最小频次，最后留下的即为前 `k` 高频。时间 $O(n\log k)$，空间 $O(n)$。
```cpp
class Solution {
public:
    vector<int> topKFrequent(vector<int>& nums, int k) {
        unordered_map<int, int> cnt;
        for (int x : nums) ++cnt[x];
        priority_queue<pair<int, int>, vector<pair<int, int>>, greater<>> pq;
        for (auto& [val, c] : cnt) {
            pq.push({c, val});
            if ((int)pq.size() > k) pq.pop();
        }
        vector<int> res;
        while (!pq.empty()) { res.push_back(pq.top().second); pq.pop(); }
        return res;
    }
};
```

---

## 五、动态规划、回溯与概率/数学特种真题

### 29. 最长递增子序列（LC 300）
**题目描述**：给你整数数组 `nums`，找到其中严格递增子序列的最大长度。
**核心思路**：贪心 + 二分维护数组 `tails`，`tails[k]` 表示长度为 `k+1` 的递增子序列末尾元素的最小可能值；遍历每个数 `x` 用 `lower_bound` 找首个 `>= x` 的位置替换（若全小于 `x` 则追加），最终 `tails.size()` 即答案。时间 $O(n\log n)$，空间 $O(n)$。
```cpp
class Solution {
public:
    int lengthOfLIS(vector<int>& nums) {
        vector<int> tails;
        for (int x : nums) {
            auto it = lower_bound(tails.begin(), tails.end(), x);
            if (it == tails.end()) tails.push_back(x);
            else *it = x;
        }
        return tails.size();
    }
};
```

### 30. 编辑距离（LC 72）
**题目描述**：给你两个单词 `word1` 和 `word2`，计算将 `word1` 转换成 `word2` 所使用的最少增、删、改单字符操作数。
**核心思路**：设 `dp[i][j]` 为 `w1` 前 `i` 个字符变 `w2` 前 `j` 个字符的最少步数；末字符相同时 `dp[i][j] = dp[i-1][j-1]`，不同时取删 `dp[i-1][j]`、增 `dp[i][j-1]`、改 `dp[i-1][j-1]` 三者最小值加 1。时间 $O(mn)$，空间 $O(mn)$。
```cpp
class Solution {
public:
    int minDistance(string word1, string word2) {
        int m = word1.size(), n = word2.size();
        vector<vector<int>> dp(m + 1, vector<int>(n + 1, 0));
        for (int i = 0; i <= m; ++i) dp[i][0] = i;
        for (int j = 0; j <= n; ++j) dp[0][j] = j;
        for (int i = 1; i <= m; ++i)
            for (int j = 1; j <= n; ++j)
                dp[i][j] = (word1[i - 1] == word2[j - 1])
                    ? dp[i - 1][j - 1]
                    : min({dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]}) + 1;
        return dp[m][n];
    }
};
```

### 31. 零钱兑换（LC 322）
**题目描述**：给定不同面额硬币 `coins` 和总金额 `amount`，计算凑成总金额所需的最少硬币个数（凑不出返 -1）。
**核心思路**：完全背包 DP。`dp[x]` 表示凑出金额 `x` 的最少硬币数，初始化为 `amount + 1`（`dp[0] = 0`），状态转移 `dp[x] = min(dp[x], dp[x - c] + 1)`。时间 $O(\text{amount}\cdot |\text{coins}|)$，空间 $O(\text{amount})$。
```cpp
class Solution {
public:
    int coinChange(vector<int>& coins, int amount) {
        vector<int> dp(amount + 1, amount + 1);
        dp[0] = 0;
        for (int i = 1; i <= amount; ++i)
            for (int c : coins)
                if (i >= c) dp[i] = min(dp[i], dp[i - c] + 1);
        return dp[amount] > amount ? -1 : dp[amount];
    }
};
```

### 32. 划分为 k 个相等的子集（LC 698 · 阿里健康真题）
**题目描述**：给定整数数组 `nums` 和正整数 `k`，判断是否可能把数组分成 `k` 个非空子集，其总和都相等。
**核心思路**：先判总和能否被 `k` 整除且最大元素不超过 `target = sum / k`。降序排序加速剪枝，回溯尝试把第 `idx` 个数放入第 `j` 个桶；关键剪枝是**若当前桶与前一个桶容量完全相同则跳过**，避免对称冗余搜索。时间最坏 $O(k^n)$（剪枝后极快），空间 $O(n+k)$。
```cpp
class Solution {
    bool dfs(const vector<int>& a, vector<int>& bucket, int idx, int target) {
        if (idx == (int)a.size()) return true;
        for (int j = 0; j < (int)bucket.size(); ++j) {
            if (j > 0 && bucket[j] == bucket[j - 1]) continue;
            if (bucket[j] + a[idx] > target) continue;
            bucket[j] += a[idx];
            if (dfs(a, bucket, idx + 1, target)) return true;
            bucket[j] -= a[idx];
        }
        return false;
    }
public:
    bool canPartitionKSubsets(vector<int>& nums, int k) {
        int sum = accumulate(nums.begin(), nums.end(), 0);
        if (sum % k != 0) return false;
        int target = sum / k;
        sort(nums.rbegin(), nums.rend());
        if (nums[0] > target) return false;
        vector<int> bucket(k, 0);
        return dfs(nums, bucket, 0, target);
    }
};
```

### 33. 用 Rand7() 实现 Rand10()（LC 470 · 阿里国际多场真题）
**题目描述**：给定均匀生成 `[1, 7]` 随机整数的 `rand7()`，实现均匀生成 `[1, 10]` 随机整数的 `rand10()`。
**核心思路**：拒绝采样。构造两位七进制数 `x = (rand7() - 1) * 7 + rand7()` 均匀覆盖 `[1, 49]`；仅接受 `[1, 40]`（10 的最大整数倍，每数恰好 4 个来源）映射为 `(x - 1) % 10 + 1`，落入 `[41, 49]` 则丢弃重采。期望调用次数 $2 \times \frac{49}{40} = 2.45$，空间 $O(1)$。
```cpp
class Solution {
public:
    int rand10() {
        while (true) {
            int x = (rand7() - 1) * 7 + rand7();
            if (x <= 40) return (x - 1) % 10 + 1;
        }
    }
};
```

### 34. 浮点数保总和最小误差取整（阿里国际大模型一面真题）
**题目描述**：给定一组浮点数 `a`，每个元素只能向上取整 `ceil` 或向下取整 `floor`，使取整后的总和等于原总和的四舍五入值 `round(sum(a))`，且总绝对误差最小。
**核心思路**：最大余数贪心法。先将全部元素向下取整 `floor(a[i])`，计算与目标总和相差的进位名额 `need = llround(total) - floorSum`；将元素按小数部分 `a[i] - floor(a[i])` 降序排列，把小数部分最大的前 `need` 个元素加 1 即可使总误差最小。时间 $O(n\log n)$，空间 $O(n)$。
```cpp
class Solution {
public:
    vector<int> roundKeepSum(const vector<double>& a) {
        int n = a.size();
        vector<int> res(n);
        vector<pair<double, int>> frac(n);
        double total = 0;
        long long floorSum = 0;
        for (int i = 0; i < n; ++i) {
            double f = floor(a[i]);
            res[i] = (int)f;
            floorSum += res[i];
            total += a[i];
            frac[i] = {a[i] - f, i};
        }
        int need = (int)(llround(total) - floorSum);
        sort(frac.begin(), frac.end(), [](const auto& x, const auto& y) {
            return x.first != y.first ? x.first > y.first : x.second < y.second;
        });
        for (int k = 0; k < need && k < n; ++k) ++res[frac[k].second];
        return res;
    }
};
```

### 35. 线程安全令牌桶限流器（Agent 服务/工程面高频设计手撕）
**题目描述**：实现一个支持并发调用的令牌桶限流器 `TokenBucket(rate, burst)`，`allow()` 判断当前请求是否放行。
**核心思路**：惰性补充令牌——不启后台线程，每次 `allow()` 加互斥锁计算距上次更新经过的秒数 `dt`，按 `min(burst, tokens + dt * rate)` 补齐当前令牌；若 `tokens >= 1.0` 则扣减 1 并放行，否则拒绝。单次调用 $O(1)$。
```cpp
class TokenBucket {
    double rate_, burst_, tokens_;
    chrono::steady_clock::time_point last_;
    mutex mtx_;
public:
    TokenBucket(double ratePerSec, double burst)
        : rate_(ratePerSec), burst_(burst), tokens_(burst), last_(chrono::steady_clock::now()) {}

    bool allow(double need = 1.0) {
        lock_guard<mutex> lk(mtx_);
        auto now = chrono::steady_clock::now();
        double dt = chrono::duration<double>(now - last_).count();
        last_ = now;
        tokens_ = min(burst_, tokens_ + dt * rate_);
        if (tokens_ >= need) { tokens_ -= need; return true; }
        return false;
    }
};
```
