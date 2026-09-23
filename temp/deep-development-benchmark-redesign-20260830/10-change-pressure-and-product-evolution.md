# Change pressure and product evolution

## 1. Why change pressure is necessary

A candidate can satisfy known campaigns with brittle special cases. A later
change reveals whether the outer developer discovered durable requirements and
placed architecture boundaries well.

Change pressure must not be an arbitrary surprise. The public brief declares
change domains; the concrete payload is withheld.

## 2. Two different kinds of change

### Project change

ForgeRoom receives a follow-up objective for a project it already developed.
This tests context, repository architecture, verification, and campaign
continuity.

### Product change

The outer orchestrator receives a new requirement for ForgeRoom itself after
the first frozen evaluation. This tests whether the product architecture is
evolvable and whether previous requirement discovery anticipated the need.

These are reported separately.

## 3. Pre-registered product change classes

One concrete class is selected per matched run:

1. add a provider with a different streaming and cancellation contract;
2. support two Git workspaces in one campaign with separate authorities;
3. add offline replay/audit export without provider access;
4. enforce project roles and narrower mutation permissions;
5. resume a campaign on another process instance;
6. reduce routine human interruption under the same safety gates;
7. accept a version-two result/event contract while preserving old state;
8. support concurrent campaigns without cross-project leakage.

## 4. Delivery protocol

At the original stop budget:

1. freeze and evaluate candidate V1;
2. reveal one product change request;
3. start a fixed continuation budget, initially 30 minutes;
4. permit the same outer tools/providers but no heldout details;
5. freeze V2 and run old plus new evaluation criteria;
6. compare source changes, migrations, regressions, and time.

The V2 run is not merged into the original Q(t) cell. It forms an adaptability
extension `A-change`.

## 5. Scored evidence

- time to first new-contract success;
- old-contract regression;
- files/modules touched;
- storage migration correctness;
- authority preservation;
- whether existing tests localized the change;
- whether requirement/decision records were revised truthfully;
- whether the agent reused or invalidated earlier assumptions;
- new dependency and operational burden;
- clean rollback or compatibility path.

## 6. Avoiding a hidden-interface contest

The change request describes user/system outcomes and supplies protocol fixtures.
It does not require a class name, module layout, or pre-imagined plugin system.
A monolith may still succeed quickly; a plugin architecture receives credit
only if it actually reduces adaptation cost and regressions.

## 7. Requirement-discovery evaluation

Before seeing the change, inspect V1's own requirements and decisions. After
V2, classify:

- anticipated need with useful architecture support;
- anticipated need without implementation value;
- unanticipated need handled cleanly;
- unanticipated need causing broad rewrite;
- falsely claimed support;
- speculative abstraction that did not help.

This separates genuine foresight from generic “extensible” language.

## 8. Time frontier

B30 may spend almost all time crossing the completion floor. B60 may add
evidence and recovery. B120 should have opportunity to invest in architecture
and product learning. The change extension tests whether those investments were
valuable rather than ornamental.

If B120 adapts no better than B30, inspect whether:

- the extra architecture was misaligned;
- the change class was too easy;
- the evaluator missed maintainability effects;
- deeper work focused on assurance/performance instead;
- the outer orchestration plateaued.
