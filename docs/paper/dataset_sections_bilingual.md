# Stu-Bench Dataset Sections, Bilingual Draft

Generated: 2026-06-21  
Scope: AAAI-style draft text for Dataset Construction, Annotation Quality, and Inter-Annotator Agreement.  
Citation note: replace `[Eedi2k]` and `[Stu-Bench artifact]` with verified BibTeX keys before submission.

## Dataset Construction

### English

We construct Stu-Bench from the held-out test split of the Eedi Question-Anchored Tutoring Dialogues 2k dataset `[Eedi2k]`. Each benchmark instance is an episode identified by an `(InterventionId, QuestionId_DQ)` pair and contains the math problem, answer options, subject/topic metadata, a real tutoring dialogue, and the tutor scaffold turns replayed during evaluation. To avoid train-test contamination when comparing against Eedi-trained simulated-student baselines, we quarantine the Eedi train split as a development-only pool for annotation guideline design, auxiliary model training, and baseline reproduction. Official Stu-Bench results are computed only on the 395 held-out test episodes, covering 13,395 messages, 324 unique questions, and four subject areas: Number, Algebra, Geometry and Measure, and Data and Statistics.

For each test episode, we build three context views. The Learner Context Set (LCS) is an internal benchmark object containing the problem, scaffold sequence, student-facing context, and evaluator-facing context. The Student-facing Context Set (SCS) contains only information that a simulated student may observe, such as the initial learner state abstraction and visible profile. The Evaluator-facing Context Set (ECS) contains hidden reference information, including the real student trajectory, gold or verified annotations, and evaluation rubric. The platform enforces this boundary by exposing SCS but not ECS through public episode APIs.

### 中文

我们基于 Eedi Question-Anchored Tutoring Dialogues 2k 数据集 `[Eedi2k]` 的留出测试集构建 Stu-Bench。每个基准样本对应一个由 `(InterventionId, QuestionId_DQ)` 标识的对话片段，包含数学题目、选项、学科与主题元数据、真实师生辅导对话，以及评测时按顺序重放的教师支架轮次。为避免在比较基于 Eedi 训练的模拟学生基线时产生训练集与测试集污染，我们将 Eedi 训练集隔离为开发用途数据池，仅用于标注指南设计、辅助模型训练和基线复现。Stu-Bench 的正式结果只在 395 个留出测试样本上计算；这些样本覆盖 13,395 条消息、324 道不同题目，以及 Number、Algebra、Geometry and Measure、Data and Statistics 四个学科领域。

对于每个测试样本，我们构建三类上下文视图。Learner Context Set（LCS）是基准内部对象，包含题目、支架序列、学生可见上下文和评估器可见上下文。Student-facing Context Set（SCS）只包含模拟学生可观察的信息，例如初始学习状态抽象和可见学习者画像。Evaluator-facing Context Set（ECS）则保存隐藏的参考信息，包括真实学生轨迹、人工确认或裁决后的标注，以及评估准则。平台通过公开的样本接口仅暴露 SCS、隐藏 ECS，从而执行这一信息边界。

## Annotation Quality

### English

The raw Eedi files provide problem text, answer options, subject/topic metadata, real tutor/student turns, and raw tutor talk-move predictions, but they do not directly provide all labels required for process-level learner realism metrics. In particular, correct answers, knowledge-component decompositions, misconception paths, learner uptake, KC state transitions, and over-improvement labels must be derived through annotation. Stu-Bench therefore uses a provenance-aware annotation pipeline with four tiers: deterministic extraction, LLM-assisted pre-labeling, human verification, and adjudication.

Every derived field is assigned a provenance value from `raw`, `auto_extracted`, `llm_assisted`, `human_verified`, `adjudicated`, or `unavailable`. Only labels with `human_verified` or `adjudicated` provenance are treated as gold annotations. Current demo scores for LRS, ISF, MA, SU, KTC, and OCC are explicitly marked as `judge_estimated`; formula metrics such as KTS, Uptake, and OverImprove remain `pending_annotation` until structured human-verified labels are available. This separation prevents the benchmark from silently mixing LLM estimates with gold labels and makes each reported metric auditable.

### 中文

Eedi 原始文件提供题干、选项、学科与主题元数据、真实教师/学生轮次，以及原始教师话语行为预测，但并不直接提供过程级学习者真实性指标所需的全部标签。具体而言，正确答案、知识组件拆解、误解路径、学习者吸收情况、知识状态转移和过度提升标签都需要通过额外标注获得。因此，Stu-Bench 采用带有来源记录的分层标注流程，包括确定性抽取、大模型辅助预标注、人工核验和分歧裁决四个层级。

每个派生字段都会记录其来源，取值包括 `raw`、`auto_extracted`、`llm_assisted`、`human_verified`、`adjudicated` 或 `unavailable`。只有来源为 `human_verified` 或 `adjudicated` 的标签才被视为金标准标注。当前演示平台中的 LRS、ISF、MA、SU、KTC 和 OCC 明确标记为 `judge_estimated`；KTS、Uptake、OverImprove 等公式化指标在结构化人工核验标签可用之前保持 `pending_annotation`。这种区分可以避免基准在无提示的情况下混用大模型估计值和金标准标签，并使每个报告指标都具备可审计性。

## Inter-Annotator Agreement

### English

To quantify annotation reliability, we reserve a 60-episode agreement subset from the official test split. Each episode in this subset is independently annotated by three annotators following the Stu-Bench annotation codebook. We measure agreement separately for problem-level labels, KC decomposition, scaffold type, learner uptake, KC state transitions, final outcome, and over-improvement. For categorical labels, we report Fleiss' kappa or Krippendorff's alpha; for ordered labels such as KC state and support level, we report weighted kappa; for free-text KC descriptions, we report adjudication rate and normalized semantic-overlap diagnostics rather than treating surface-form matches as agreement.

Disagreements are resolved through adjudication by a senior annotator or project lead. Final labels produced after adjudication receive `adjudicated` provenance, while unresolved or low-confidence cases are flagged in the annotation artifact. In the paper, we will report the number of annotated episodes, number of annotators, per-label agreement statistics, adjudication rates, and the proportion of labels retained as gold. The current platform exposes the annotation schema and metric-readiness status so that official results can distinguish computed metrics from judge-estimated metrics before the agreement study is complete.

### 中文

为量化标注可靠性，我们从正式测试集中预留 60 个样本作为一致性评估子集。该子集中的每个样本均由三名标注者根据 Stu-Bench 标注手册独立标注。我们分别测量题目级标签、知识组件拆解、支架类型、学习者吸收情况、知识状态转移、最终结果和过度提升标签的一致性。对于类别标签，我们报告 Fleiss' kappa 或 Krippendorff's alpha；对于知识状态、支持强度等有序标签，我们报告加权 kappa；对于自由文本形式的知识组件描述，我们报告裁决比例和归一化语义重合诊断结果，而不是将表层文本匹配直接视为一致。

标注分歧由资深标注者或项目负责人进行裁决。经过裁决得到的最终标签使用 `adjudicated` 来源记录，未解决或低置信度样本则在标注产物中保留相应标记。在论文中，我们将报告已标注样本数量、标注者数量、各类标签的一致性统计、裁决比例，以及最终保留为金标准标签的比例。当前平台已经暴露标注 schema 和指标就绪状态，因此在一致性研究完成之前，正式结果也可以明确区分可计算指标和评审估计指标。
