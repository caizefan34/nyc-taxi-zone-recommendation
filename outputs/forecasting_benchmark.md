# Forecasting-Enhanced Recommendation Benchmark

Static metrics measure agreement with the existing public reference utility. Rollout fare is limited to the fixed single-driver simulator and is not a deployment estimate.

| Strategy | NDCG@3 | Hit@3 | Mean simulator fare/day | SD |
|---|---:|---:|---:|---:|
| Historical single-step | 0.9024 | 0.8804 | $548.77 | $72.98 |
| Forecast-enhanced | 0.8835 | 0.8408 | $530.89 | $78.91 |

Paired forecast minus historical fare: $-17.88/day, 95% bootstrap CI [$-38.15, $3.03], paired t-test p=0.0865, Cohen's dz=-0.173.

Wilcoxon signed-rank p=0.00129. The CI crosses zero and the mean difference is negative, so this strategy does not replace the default recommender.
