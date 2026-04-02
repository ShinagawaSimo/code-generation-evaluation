# 独立生成案例输入（中文）

## 案例 ind-001
- task_original_statement: 编写程序，读取一组整数，并使用冒泡排序按升序输出。
- input_direct.prompt: 从标准输入读取整数 N，再读取 N 个整数，输出按升序排序后的序列，数字之间以空格分隔。
- input_direct.instructions:
  - 使用冒泡排序。
  - 严格输出一行结果。
- model_input.task_description: 从标准输入读取 N 和后续 N 个整数，使用冒泡排序将其按升序输出。结果仅输出一行，数字以空格分隔。

## 案例 ind-002
- task_original_statement: 给定一组闭区间，合并所有重叠区间，并按起点从小到大输出合并结果。
- input_direct.prompt: 读取整数 N，接着读取 N 行区间 l r（l <= r）。区间为闭区间。若两个区间重叠或相接（next.start <= current.end）则合并。按起点升序逐行输出每个合并后的区间，格式为“l r”。
- input_direct.instructions:
  - 区间是闭区间（包含端点）。
  - 如果两个区间在端点处相接，也必须合并。
  - 每个合并后的区间输出一行。
- model_input.task_description: 读取 N 个闭区间（l r），将重叠或相接区间合并（next.start <= current.end），按起点升序逐行输出“l r”。

## 案例 ind-003
- task_original_statement: 给定包含墙体、起点 S 和终点 T 的网格，使用四方向移动计算从 S 到 T 的最短路径长度。
- input_direct.prompt: 读取整数 R、C，再读取 R 行网格字符（'.'、'#'、'S'、'T'）。可在非墙体格子中进行上下左右移动。输出从 S 到 T 的最短路径长度；若不可达输出 -1。
- input_direct.instructions:
  - 仅允许四个方向移动（上/下/左/右）。
  - 墙体使用 '#' 表示。
  - 若 T 不可达，输出 -1。
- model_input.task_description: 读取 R、C 和网格（'.'、'#'、'S'、'T'），在非墙体格子上做四方向移动，输出 S 到 T 的最短路径长度，不可达则输出 -1。

## 案例 ind-004
- task_original_statement: 找到不含重复字符的最长子串；若有多个最长子串，输出其中字典序最小的一个。
- input_direct.prompt: 读取一行字符串 S。求所有字符互不重复的子串最大长度。若多个子串长度同为最大，选择字典序最小者。第一行输出长度，第二行输出所选子串。
- input_direct.instructions:
  - 字典序比较采用标准字符串顺序。
  - 严格输出两行。
- model_input.task_description: 给定字符串 S，求字符各不相同的最长子串长度；若有并列，输出字典序最小的子串。先输出长度，再在下一行输出子串。

## 案例 ind-005
- task_original_statement: 统计和可被 K 整除的子数组数量。
- input_direct.prompt: 读取整数 N 和 K，再读取 N 个整数。统计有多少个连续子数组的元素和可被 K 整除，并输出计数结果。
- input_direct.instructions:
  - N 可能较大，需要使用高效算法。
  - 结果可能超过 32 位整数范围，需使用 64 位整数计算。
- model_input.task_description: 给定 N、K 和长度为 N 的整数数组，统计元素和可被 K 整除的连续子数组数量，并输出整数结果。
