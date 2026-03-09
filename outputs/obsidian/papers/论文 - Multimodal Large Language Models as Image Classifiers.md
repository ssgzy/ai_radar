# 论文 - Multimodal Large Language Models as Image Classifiers

关联：[[AI Radar 日报 - 2026-03-10 - 20260310_024851]] | [[结果索引]] | [[任务笔记 - AI Radar 搭建]]

## V2 结论
- 推荐级别：高优先级跟进
- 总分：8.9
- 关注建议：建议放入今日重点，优先精读论文或试用项目。
- 评分理由：总分 8.9。新颖性较强（10.0）；个人相关性较强（8.7）；适合持续做研究跟踪。

## 基本信息
- 来源：arxiv
- 标题：Multimodal Large Language Models as Image Classifiers
- 链接：http://arxiv.org/abs/2603.06578v1
- 时间：2026-03-06T18:59:58+00:00
- 作者 / 维护者：Nikita Kisel, Illia Volkov, Klara Janouskova, Jiri Matas
- 使用模型：mistral:7b
- PDF：https://arxiv.org/pdf/2603.06578v1

## 标签
- 论文
- 大模型
- 多模态
- 评测与基准
- 研究跟踪

## 分数拆解
- 新颖性：10.0
- 落地信号：8.0
- 个人相关性：8.7

## 中文总结
### 内容概述
该文章研究了多模态大语言模型（Multimodal Large Language Models，MLLM）在图像分类任务中的表现，并探讨了其评估协议和真实标签质量对其表现的影响。

### 解决的问题
该文章试图解决多模态大语言模型在图像分类任务中的表现存在不一致的问题，并且揭示了这些不一致的原因是由于不适当的评估协议和低质量的真实标签所导致的。

### 为什么值得关注
该文章值得关注，因为它揭示了多模态大语言模型在图像分类任务中的表现可能是由于不适当的评估协议和低质量的真实标签所导致的误导性结果，而不是模型本身的缺陷。

### 适合我关注的原因
作为个人 AI 情报系统使用者，该文章值得关注，因为它可以帮助我了解多模态大语言模型在图像分类任务中的表现，并且提供了一些可以改善其表现的建议。

### 关键词
- 多模态大语言模型（MLLM）
- 图像分类
- 评估协议
- 真实标签
- 表现

### 简洁引用
> "多模态大语言模型在图像分类任务中的表现可能是由于不适当的评估协议和低质量的真实标签所导致的误导性结果"。

## 原始内容
Multimodal Large Language Models (MLLM) classification performance depends critically on evaluation protocol and ground truth quality. Studies comparing MLLMs with supervised and vision-language models report conflicting conclusions, and we show these conflicts stem from protocols that either inflate or underestimate performance. Across the most common evaluation protocols, we identify and fix key issues: model outputs that fall outside the provided class list and are discarded, inflated results from weak multiple-choice distractors, and an open-world setting that underperforms only due to poor output mapping. We additionally quantify the impact of commonly overlooked design choices - batch size, image ordering, and text encoder selection - showing they substantially affect accuracy. Evaluating on ReGT, our multilabel reannotation of 625 ImageNet-1k classes, reveals that MLLMs benefit most from corrected labels (up to +10.8%), substantially narrowing the perceived gap with supervised models. Much of the reported MLLMs underperformance on classification is thus an artifact of noisy ground truth and flawed evaluation protocol rather than genuine model deficiency. Models less reliant on supervised training signals prove most sensitive to annotation quality. Finally, we show that MLLMs can assist human annotators: in a controlled case study, annotators confirmed or integrated MLLMs predictions in approximately 50% of difficult cases, demonstrating their potential for large-scale dataset curation.

## 调试信息
- Prompt：`/Users/sam/Documents/AI Models/ai_radar/outputs/debug/prompts/20260310_024851_arxiv_2603.06578v1_prompt.txt`
- Response：`/Users/sam/Documents/AI Models/ai_radar/outputs/debug/responses/20260310_024851_arxiv_2603.06578v1_response.txt`