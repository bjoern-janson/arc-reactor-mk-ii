# Arc Reactor Mk II

**Feedback-to-Inquiry Core**

**Status:** `DESIGN_ONLY / NO_IMPLEMENTATION / NO_TRAINING / NO_SCIENTIFIC_RESULT`

Arc Reactor Mk II is a clean-room continuation of the original
[`arc-reactor`](https://github.com/bjoern-janson/arc-reactor) idea.

The original ARC asked how reality-coupled failure should govern structural
change:

```text
Error -> Diagnosis -> Permission -> Allocation -> Correction
```

Mk II moves one causal step upstream. Its first target is a reusable mechanism
whose learned state changes **which question gets asked next**:

```text
informative feedback
        ->
changed serialized query selector
        ->
different future inquiry
        ->
better bounded diagnosis
        ->
better repair on previously unused problems
```

The old repository is lineage, not evidence. Mk II does not inherit ARC's
scientific claims, metrics, or implementation status.

## V0 target

Build a tiny serializable selector `theta` that ranks a fixed menu of primitive
binary queries. Primitive queries, belief updates, repair rules, storage caps,
and evaluation problems are identical across treatment and controls.

The selector is the portable artifact:

```text
fresh host + theta_before
fresh host + theta_after
```

If swapping only `theta` transfers the changed query choices and resulting
performance, the artifact has isolated causal leverage over future inquiry.

## Controls

V0 compares:

- **LEARN** — fits the selector from informative terminal feedback.
- **SCRAMBLED** — fits from a prospectively fixed corruption of the same
  feedback values.
- **FROZEN** — retains the competent initial greedy balanced-splitting selector.

All arms receive the same primitive tools, public query semantics, feature
schema, storage cap, and frozen evaluation cases.

## Ignition vs useful power

**Ignition** means informative feedback changes the serialized selector and,
on frozen unused diagnostic problems, produces strictly better repair than both
controls at at least one common budget without losing to either control at the
other budget. The behavior and performance change must follow the selector
under bidirectional state transplant.

**Useful power** is a separate engineering threshold. For a declared number
`H` of future tasks, the trained selector must justify its training and
deployment cost relative to the baseline at matched repair performance.

A positive ignition result does **not** establish a novel active-learning
algorithm, unknown-change detection, learned primitive sensors, safe forgetting,
protected corrective-frontier expansion, general intelligence, or compatibility
with MATRIX, OpenCore, Revisics, neural systems, or other repositories.

## Current design

See:

[`docs/superpowers/specs/2026-09-09-feedback-to-inquiry-core-design.md`](docs/superpowers/specs/2026-09-09-feedback-to-inquiry-core-design.md)

The design is review-state only. The next legal step after review is a narrow
implementation plan that pins manifests and numerical conventions before any
training or learned-result inspection.

## Program rule

> Build one component whose benefit survives removal, replacement, and reuse.

The first reactor claim is deliberately small:

> These saved parameters change tomorrow's questions, improve tomorrow's
> repairs on the frozen finite family, and can be evaluated against their own
> resource cost.
