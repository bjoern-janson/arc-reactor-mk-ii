# Feedback-to-inquiry core: V0 design proposal

Status: DESIGN FOR REVIEW. No implementation, training, scientific run, or new repository is authorized by this document. ARO-001e is not a prerequisite.

## Objective

Create a small serializable query selector whose parameters change through informative training feedback and improve repair on previously unused diagnostic problems. Primitive queries, belief updates, repair rules, storage caps, and evaluation problems are identical across treatment and controls.

The initial claim is improvement in diagnostic selection over a frozen finite problem distribution. Novel algorithms, new primitive tests, unknown-change detection, protected frontier expansion, and transfer between research repositories are separate questions.

## Existing material to reuse

At MATRIX commit 5bca7ec6508e9d7ca1008ba745748281139fcfac, the A2 implementation already separates the hidden environment from the policy, freezes learned state, records full executions, and performs constructor-state transplants.

Its RealizedPolicy.action always asks query len(observations), so the diagnostic sequence is 0, 1, 2. Learning changes the decoder. This proposal targets query selection while holding belief update and terminal repair fixed. Reuse the boundary and transplant patterns; do not modify the frozen A2 experiment or claim its scientific identity for this experiment.

Sources:
- https://github.com/bjoern-janson/matrix/blob/5bca7ec6508e9d7ca1008ba745748281139fcfac/experiments/a2_v0/implementation/a2_v0/model.py
- https://github.com/bjoern-janson/matrix/blob/5bca7ec6508e9d7ca1008ba745748281139fcfac/experiments/a2_v1/implementation/a2_v1/engine.py
- https://papers.nips.cc/paper_files/paper/2017/hash/8ca8da41fe1ebc8d3ca31dc14f5fc56c-Abstract.html

Learning a query-selection regressor from previous outcomes is established prior art. Reuse is acceptable; this project must earn its own finite effect and any later engineering usefulness.

## Architecture and information boundary

Four pieces suffice:

1. A hidden-world executor owns the true fault x and answers a selected primitive query.
2. A fixed belief updater filters the current candidate set by the observed answer.
3. The learned selector ranks the remaining queries from public problem information, current candidates, and remaining budget.
4. A fixed repair rule stops at a singleton or budget exhaustion and returns the lowest numbered remaining candidate.

The selector receives the candidate set and the public truth tables of permitted queries. It never receives x, actual correctness before terminal feedback, a privileged candidate pair, or evaluation labels.

This deliberately studies learning to select inquiries when query semantics are known. It does not study learning unknown sensor semantics. Since a full planner could solve this tiny public problem, include an exact planner as a reference and charge the learner's feature construction and planning work.

Interface:

    choose_query(theta, candidate_set, remaining_queries, remaining_budget)
        -> query_id or STOP

The host owns observations and fixed belief updates. theta is read-only during evaluation. The host must be identical when comparing theta_before and theta_after.

## Finite apparatus

Proposed initial grammar:

- Fault universe: the eight 3-bit strings.
- An episode starts with all eight faults possible.
- A problem supplies four distinct nonconstant binary partitions of that universe.
- Every primitive query costs one unit and reveals its binary answer.
- Query budgets: 2 and 3.
- Faults are uniform within a problem; evaluation enumerates all eight.
- Query answers are deterministic and nondestructive.
- Repair is correct exactly when the returned fault equals x.
- A terminal repair has the same fixed charge in every arm.

All arms receive the same menu for a given problem. Different menus constitute different problem instances drawn from the same grammar; the learner never gains a query unavailable to a control.

A hand-checkable control is the menu {majority, bit_1, bit_2, bit_3}. Every first query splits the eight faults 4/4. Asking all three coordinate queries repairs every fault in three queries. Asking majority first leaves a four-state set on which each coordinate splits 1/3; with two remaining queries, at most three of those four states can be repaired. Thus that first choice permits at most 6/8 success.

This is a control showing that query choice can matter. It is not a held-out learning result, and the target family must not be filtered for worlds where a desired learner wins.

## Dataset boundary

Proposed size: 256 training menus and 64 evaluation menus, all with distinct canonical task identities. Evaluate both budgets and all eight faults: 1,024 paired cases per artifact.

Canonical task identity removes permutations of fault names, permutations of the four query names, and complements of individual binary answers. It can be computed by trying the 4! column permutations and 16 answer complements, sorting the eight resulting row signatures, and retaining the least byte string. The true episode fault is not part of this identity.

Training and evaluation manifests must be committed before fitting or inspecting evaluation results. Rejection during manifest construction is limited to grammar violations and duplicate canonical identities. Neither repair outcomes nor a learner's advantage may determine inclusion.

The finite claim concerns unseen query configurations over the same eight-fault universe. It does not establish transfer to new fault types or larger systems.

## Minimal learner

Use an eight-coefficient linear query scorer. A feature vector is computed only from public candidate/query structure:

- intercept;
- remaining budget divided by 3;
- candidate count divided by 8;
- smaller child fraction after the proposed query;
- product of the two child fractions;
- fraction of candidates in singleton children;
- weighted best next-query split score across children;
- worst-child best next-query split score.

For a non-singleton child, the next-query split score is the largest smaller-child fraction among remaining queries; it is zero if no useful query remains. A singleton child receives score 1/2. The last two features are zero when no further query budget remains. Empty children are omitted from their aggregation.

The frozen initial coefficients implement ordinary greedy balanced splitting: coefficient one on smaller-child fraction, zero elsewhere. Deterministic ties use the public query ordering. This makes FROZEN a competent standard baseline from the start.

Training uses a shared, policy-independent exploration corpus. For each training menu, budget, and fault, execute every ordered sequence of distinct queries of the permitted length, with the common terminal repair rule. Queries after an already achieved singleton are skipped. The feedback is actual terminal repair success, associated with each preceding state/action row. The selector is not allowed to adapt this collection policy.

Fit ridge regression to terminal success with regularization 0.01 toward the initial coefficient vector. This learns an approximate action value under the supplied exploration continuation; improvement under the resulting greedy policy is an empirical question, not guaranteed by the fit.

Feature normalization and regularization are fixed design choices, not evaluation-tuned quantities. The final numerical solver, arithmetic precision, training-row order, and serialization must be fixed in the implementation plan before execution.

## Controls and transplant

LEARN fits to the actual feedback.
SCRAMBLED fits to a prospectively fixed permutation of the same feedback values within equal budget and decision-depth strata.
FROZEN retains the initial greedy coefficients.

All three share the same training inputs, feature definitions, permitted tools, storage cap, and evaluation cases. The corruption is a specific feedback control, not a guarantee of zero information under every conditioning.

Retain the exact training permutation. A chance helpful scrambled fit remains an observed outcome; do not redraw it.

Serialize all eight coefficients and their schema into a standalone policy artifact. At evaluation:

- load each artifact into the same fresh host;
- disable training and discard training caches;
- run the same paired cases;
- transplant theta_before into the LEARN host and require identical behavior to FROZEN;
- transplant theta_after into the FROZEN host and require identical behavior to LEARN.

The state swap changes only selector parameters. Training tables, query-response caches, random-generator state, and instance identifiers cannot travel with the artifact.

The exact dynamic-programming planner is an evaluator reference, with its work reported separately. Its answers never become evaluation feedback. If an ordinary planner is cheaper and equally effective, record that engineering comparison.

## Outcomes and interpretation

Primary outcome: exact paired repair success at each fixed query budget on the frozen evaluation family.

Also retain paired wins, losses, ties, per-menu results, query traces, and the decisions that changed after learning. Average success alone does not imply expansion or preservation of the full jointly correctable frontier.

The proposed acceptance rule requires strictly higher repair success than both FROZEN and the specified SCRAMBLED control at at least one common budget, and no lower success than either control at the other budget. Behavior and performance must transfer with the selector-state swap. A gain at one budget with a loss at the other is a recorded tradeoff, not passage of this rule. This is a finite deterministic comparison; do not count correlated fault/budget cases as independent statistical replications or infer population-wide significance.

Query counts must be compared with success held fixed or with failures explicitly included. Early failed episodes must not be presented as query savings. Generalization beyond the frozen family requires a later independently constituted test.

A baseline match is a useful reduction: no advantage over ordinary greedy query selection was established. A win only against corrupted feedback is insufficient. A failed transplant means the proposed artifact did not isolate the cause.

## Resource accounting and reuse

Track persistent artifact bytes, peak working memory, training work, feature/table inspections, query executions, terminal actions, and wall-clock time. Use equal resource caps and report actual usage; do not force controls to waste resources to manufacture equal spending.

Causal query-selection improvement and net engineering savings are separate thresholds. For a declared number H of future tasks, compare:

    training cost + H * learned deployment cost
    versus
    H * baseline deployment cost

at matched repair performance and declared cost weights. If there is no positive per-task saving, a training-payback claim is unavailable.

First portability check: the same serialized artifact works in a fresh host on unseen menus under this exact interface. A genuinely different downstream application is a separate load test. Do not claim that MATRIX, OpenCore, Revisics, monitoring, or neural systems can consume this artifact without checking their semantic interfaces.

## Next gate

Review this design, especially the public query-semantics assumption and the restriction to unseen configurations in an eight-fault universe. Then write the narrow implementation plan, pin manifests and numerical conventions, and implement the core plus controls. No learned-result inspection may choose the evaluation family or rewrite the success criterion.
