# 评测与验证工具

本目录提供三类公开工具。它们的职责不同：基础检查器验证代码和产物是否正确；静态诊断器比较固定两步效用排序；rollout 模拟器比较完整策略的长期表现。未公开的最终评测数据和内部工具不在学生包中。

所有命令均从学生目录根目录运行，并先安装 `requirements.txt` 中的依赖：

```bash
PYTHONPATH=src python3 -m ...
```

## 1. 基础检查器

先完成清洗、区域—时间统计、时间矩阵和三个策略文件，再运行：

```bash
PYTHONPATH=src python3 -m eval.sanity_check \
  --train-cleaned data/processed/train_cleaned.parquet \
  --validation-cleaned data/processed/validation_cleaned.parquet \
  --statistics data/processed/zone_time_statistics.parquet \
  --travel-times data/processed/travel_time_matrix_dijkstra.csv \
  --baseline-1 src/2_recommendation_algorithm/baseline_1.py \
  --baseline-2 src/2_recommendation_algorithm/baseline_2_2.py \
  --strategy src/2_recommendation_algorithm/improved_strategy.py \
  --output outputs/sanity_report.json
```

它会检查：

- 清洗结果和统计表是否具有规定字段；
- `263×263` 时间矩阵是否可读取、非负，对角线是否与训练集同区订单的平均时长一致；
- 三个策略是否能加载，且为固定时刻与区域返回合法 Top-3；
- Baseline 1/2 是否与根据你自己的统计表、时间矩阵直接计算出的参考结果一致。

若失败，`sanity_report.json` 会指出具体产物或规则，例如：

```json
{
  "passed": false,
  "checks": {
    "travel_time_matrix": {
      "passed": false,
      "reason": "travel_time_matrix: diagonal at LocationID 1 must be 12.345678, got 0.000000"
    }
  }
}
```

基础检查器不产生项目最终分数，也不读取 `validation_answers.parquet`。

一个通过检查的 JSON 结构可参照 [`data/examples/evaluation_output_example.json`](../../data/examples/evaluation_output_example.json) 中的 `sanity_report`；具体文字会随错误位置不同而变化。

## 2. 静态两步效用诊断器

策略文件需要实现：

```python
def recommend(current_datetime, current_location_id) -> list[int]:
    """返回三个互不重复、按优先级排序的 1..263 区域编号。"""
```

运行：

```bash
PYTHONPATH=src python3 -m eval.public_validation \
  --strategy src/2_recommendation_algorithm/improved_strategy.py \
  --queries data/processed/validation_input.parquet \
  --answers data/processed/validation_answers.parquet \
  --predictions outputs/validation_predictions.parquet \
  --output outputs/validation_static_metrics.json
```

输出包括 NDCG@3、Hit@3、Top-1 的参考两步效用、平均 `recommend` 耗时与峰值 Python 内存。参考效用对训练期多周累计需求使用 `n/(n+240)` 估计接单概率，并同时考虑接单失败后留在到达区域、以及接单成功后到达订单下车区域的下一状态。它主要帮助调试两步建模；长期表现应使用下方 rollout 结果。下方 rollout 的 `n` 是具体日期的单日市场需求，因此仍使用 `n/(n+40)`。

运行后还会写出 `validation_predictions.parquet`，字段依次为 `query_id`、`rank_1`、`rank_2`、`rank_3` 和 `latency_ns`。同一份实际运行输出的 JSON 字段和类型可参照 [`data/examples/evaluation_output_example.json`](../../data/examples/evaluation_output_example.json) 的 `static_diagnostic`。

`validation_answers.parquet` 是公开验证标签，只能用于验证实验与报告；不得把 `query_id` 当成答案查找表、把标签作为训练特征，或据此直接生成最终测试输出。

## 3. 一月 validation rollout 模拟器

```bash
PYTHONPATH=src python3 -m eval.validation_rollout \
  --strategy src/2_recommendation_algorithm/improved_strategy.py \
  --market data/processed/validation_uncleaned.parquet \
  --travel-times data/processed/travel_time_matrix_dijkstra.csv \
  --output outputs/validation_rollout.json \
  --trace outputs/validation_trace.csv
```

它在固定随机种子下，从 `2023-01-25 00:00`、区域 132 开始，模拟至 `2023-02-01 00:00`。默认运行 100 次；调试时可附加 `--runs 2`，并可用 `--seed` 固定不同随机种子。

每次决策遵循：

```text
输出 Top-3 → 按 60% / 30% / 10% 权重选择可达区域
→ 空驶移动 → 消耗一个 slot 尝试接单
→ 成功时随机抽取一笔订单并到达其下车区域 → 下一次决策
```

不可达候选会在抽样前移除并重新归一化。时间矩阵对角线记录历史同区订单时长；实际选择当前区域时不发生空驶，不读取对角线。跨区空驶和成功载客行程均按 `floor(分钟/30+0.5)` 四舍五入为 slot，结果允许为 0；每次接单尝试固定消耗 1 个 slot。模拟车费统一使用 `fare_amount` 的订单基础车费代理，不是 `total_amount`，更不是司机净收入。

完整状态转移见项目根目录的[问题建模与评测规则](../../问题建模与评测规则.md)；Task C 的两步公式见[项目说明书与评分细则](../../项目说明书与评分细则.md)。

`validation_rollout.json` 包含平均日车费、波动、平均服务订单数、平均空驶分钟数和单次推荐耗时。`validation_trace.csv` 记录一条固定随机种子轨迹中的每次 Top-3、实际选择、需求、接单概率、订单车费和下一状态；报告应利用它解释至少一个成功或失败案例。

[`data/examples/evaluation_output_example.json`](../../data/examples/evaluation_output_example.json) 还包含一次已通过基础检查的临时参考实现的 rollout JSON。该示例以 `--runs 1` 运行，只用于说明输出结构；不同清洗规则和策略的数值不同，正式报告按规定配置运行并如实填写结果。

模拟器按不可变规则直接从 `validation_uncleaned.parquet` 构造验证市场，因此每组在相同市场上比较。你的清洗结果仍用于构造训练统计量、图和策略本身。

## 使用边界

- 公开工具可被阅读和本地修改；助教只认可对最终提交代码的复跑结果。
- 验证集只能用于参数选择、方案比较和报告；不要在最终策略运行时读取验证集文件。
- 助教将在未见数据上以同一类机制复跑提交代码。公开验证得分不能自动替代数据清洗、建模、代码质量或报告评分。
