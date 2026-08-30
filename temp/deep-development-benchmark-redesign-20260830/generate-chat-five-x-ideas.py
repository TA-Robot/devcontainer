#!/usr/bin/env python3
"""Generate the reviewed 20 x 10 x 5 chat-development-system inventory."""
from pathlib import Path


SECTIONS = [
    ("A", "Room・conversation model", [
        "room内のgoal thread", "humanとagentの同時発言", "messageの訂正と撤回",
        "decision専用thread", "artifact専用thread", "incident専用thread",
        "cross-room参照", "会話のbranchとmerge", "roomのarchiveと再開", "会話からactionへの変換",
    ], [
        "を自然なchat操作だけで扱えるようにする", "をtyped eventと明示状態で永続化する",
        "へ同時操作・遅延・取消競合を重ねる", "の理解と操作成功を自動taskで測る",
        "を既存履歴を壊さず後続要求へ進化させる",
    ]),
    ("B", "Human attention・ambient UX", [
        "重要発見のambient表示", "承認要求の集約", "長時間作業の進捗帯",
        "agent間cruxの提示", "待機理由の提示", "失敗severityの提示",
        "人間の未送信draft", "復帰時のdelta summary", "notification優先度", "mobileでのcritical操作",
    ], [
        "をcodingの邪魔にならない最小surfaceで実現する", "をuser別attention policyとして保存する",
        "へ連続発生・重複・stale表示を注入する", "のhuman interruption削減効果をtraceで測る",
        "を利用傾向から安全に適応させる",
    ]),
    ("C", "Goal・requirement discovery", [
        "broad goalのobjective tree", "implicit user journey", "hard constraintとpreference",
        "latent requirement ledger", "assumptionの可逆性", "requirement間の衝突",
        "scope削減判断", "milestone acceptance", "residual unknown", "成功後に生じる次要求",
    ], [
        "を追加質問なしで初期発見する", "をchat・plan・test・codeへ一貫して接続する",
        "を反例・新証拠・期限変更で揺さぶる", "が成果品質へ与えた因果を自動記録する",
        "を後続campaignからproject-local知識へ更新する",
    ]),
    ("D", "Planning・task graph", [
        "milestone graph", "artifact dependency", "critical path", "ready/stale/blocked状態",
        "task ownership", "stop condition", "integration checkpoint", "replan trigger",
        "parallelism budget", "unfinished work handoff",
    ], [
        "を目的からagent自身に構成させる", "をroom上で説明可能な実行contractにする",
        "へ依存変更・失敗・優先度反転を注入する", "の予測と実際の差を自動評価する",
        "を実績から固定presetなしで改善する",
    ]),
    ("E", "Agent collaboration・deliberation", [
        "independent proposal", "blind review", "structured debate", "minority report",
        "expert consultation", "cross-provider critique", "claim-centered synthesis",
        "counterexample exchange", "fresh-context verification", "consultation終了判断",
    ], [
        "を必要な不確実性がある時だけ起動する", "を根拠・反証・採否付きcontractにする",
        "へ同調・重複・誤ったconsensusを仕込む", "がdecisionとartifactを改善したか測る",
        "をprojectごとの観測結果で再編する",
    ]),
    ("F", "Candidate competition・experiments", [
        "architecture candidate", "algorithm prototype", "UX interaction candidate",
        "storage strategy", "verification strategy", "migration strategy", "performance optimization",
        "prompt/workflow variant", "baseline and ablation", "winner integration",
    ], [
        "を複数agentへ独立実装させる", "を同一fixtureとbudgetで比較可能にする",
        "へworkload shiftとadversarial caseを当てる", "の選択理由とdiscard costを記録する",
        "を一度の勝敗で固定せずportfolio化する",
    ]),
    ("G", "Provider・model routing", [
        "Codex routing", "Claude routing", "Grok routing", "model effort選択",
        "provider availability", "capability差分", "cost/latency予測", "fallback chain",
        "parallel provider quorum", "provider result acceptance",
    ], [
        "をtask特性とproject evidenceから選ぶ", "をversioned capability contractで表現する",
        "へ認証切れ・遅延・malformed出力を注入する", "のquality・時間・再作業を自動比較する",
        "をglobal presetでなくproject-local実績から更新する",
    ]),
    ("H", "Context・memory・knowledge", [
        "task context capsule", "repository map", "decision memory", "failure memory",
        "user preference memory", "domain glossary", "artifact summary", "context freshness",
        "cross-agent evidence sharing", "long campaign compaction",
    ], [
        "を必要最小限で自動構成する", "をsource anchorとversion付きで保存する",
        "へbase変更・矛盾・情報欠落を注入する", "のtask entry短縮と誤り増加を同時測定する",
        "を利用結果から忘却・統合・再取得する",
    ]),
    ("I", "Code・artifact interaction", [
        "diff preview", "symbol-aware code reference", "generated artifact", "design document",
        "test report", "benchmark result", "screenshot and UI state", "terminal evidence",
        "artifact lineage", "accepted deliverable bundle",
    ], [
        "をchatから直接理解・操作できるようにする", "をmessage・decision・commitへ双方向linkする",
        "へstale preview・partial生成・conflictを注入する", "の閲覧がreview品質へ効いたか測る",
        "を新artifact種へpluginで拡張できるようにする",
    ]),
    ("J", "Git・workspace・integration", [
        "dirty initial worktree", "agent worktree", "branch ownership", "single-writer integration",
        "semantic conflict", "generated file conflict", "rebase onto moving base", "commit evidence",
        "rollback point", "multi-repository campaign",
    ], [
        "をuser変更を失わず自律処理する", "をauthorityとbase digest付きcontractにする",
        "へ同時commit・force変更・partial mergeを注入する", "のintegration tailとlost workを測る",
        "を後続のrepository topology変更へ進化させる",
    ]),
    ("K", "Execution・terminal・process", [
        "command execution", "long-running process", "interactive terminal", "background service",
        "process tree ownership", "resource quota", "cancellation", "timeout and retry",
        "environment capture", "reproducible command transcript",
    ], [
        "をchat taskから安全に起動・監督する", "をrun identityとterminal state付きで保存する",
        "へhang・orphan・late success・signal raceを注入する", "の実行claimを独立再現で検証する",
        "をcontainer再起動とhost差分へ対応させる",
    ]),
    ("L", "Testing・verification・acceptance", [
        "acceptance obligation", "independent verifier", "property-based test", "mutation test",
        "UI task test", "performance regression", "security review", "test evidence",
        "false positive triage", "completion reopen",
    ], [
        "をrequirementとriskから自動選定する", "をmakerと独立したartifact contractで実行する",
        "へflaky・stale・誤oracleを注入する", "のunique defectとreview costを測る",
        "をescaped defectから次campaign向けに改善する",
    ]),
    ("M", "Authority・security・governance", [
        "workspace write authority", "network authority", "external message authority",
        "destructive action", "secret access", "untrusted repository", "tool capability grant",
        "approval delegation", "audit retention", "policy exception",
    ], [
        "をchat内で理解可能な境界として示す", "をleast-privilege typed contractで強制する",
        "へprompt injection・symlink・confused deputyを仕込む", "の安全性と作業阻害を同時測定する",
        "をproject stageとrisk実績で安全に変更する",
    ]),
    ("N", "Durability・failure recovery", [
        "room state", "campaign state", "agent task state", "provider attempt", "artifact state",
        "in-flight decision", "partial result", "server restart", "container rebuild", "host interruption",
    ], [
        "をlossなく復元する", "をmulti-axis stateとatomic transitionで表現する",
        "へcrash point・corruption・duplicate replayを注入する", "のrecovery truthと時間を測る",
        "をschema migrationと旧state互換へ進化させる",
    ]),
    ("O", "Observability・evidence・audit", [
        "agent activity event", "claim evidence", "decision provenance", "experiment lineage",
        "test command evidence", "human interruption", "resource usage", "quality curve",
        "failure classification", "campaign replay",
    ], [
        "を人手入力なしで収集する", "をcompact typed schemaでquery可能にする",
        "へ欠損・順序逆転・重複を注入する", "からorchestration効果を過大評価せず推定する",
        "を長期運用で集約しcontext圧迫を防ぐ",
    ]),
    ("P", "Proactive・scheduled・ambient agents", [
        "periodic dependency review", "continuous test improvement", "background benchmark",
        "stale documentation review", "security advisory scan", "performance watch",
        "unfinished task recovery", "idle-time exploration", "maintenance suggestion", "scheduled report",
    ], [
        "を有限jobとして安全に定義する", "をdedupe・budget・yield contract付きで実行する",
        "へ重複schedule・無限retry・provider不在を注入する", "の成果とcredit消費を自動評価する",
        "を価値が実証されたprojectだけで継続する",
    ]),
    ("Q", "Extension・project contract", [
        "project AGENTS contract", "native agent role", "provider adapter", "campaign plugin",
        "artifact renderer", "evaluator plugin", "skill package", "custom tool", "event schema version",
        "third-party extension isolation",
    ], [
        "をchat systemが自動発見して利用する", "をcapability・permission・version付きで定義する",
        "へincompatible version・crash・malicious inputを注入する", "の導入価値と削除容易性を測る",
        "をcore変更なしで追加・rollback可能にする",
    ]),
    ("R", "Learning・adaptive orchestration", [
        "task duration prior", "model quality prior", "parallelism prior", "review value prior",
        "experiment success prior", "project stage inference", "failure recurrence model",
        "human preference model", "stop/continue prediction", "method recommendation skill",
    ], [
        "を自動traceから条件付きで学習する", "をsample数・uncertainty・provenance付きで保存する",
        "へdistribution shift・bad episode・leakageを注入する", "が次campaignを改善したかmatched runで測る",
        "を誤り検出時に忘却・rollbackできるようにする",
    ]),
    ("S", "Evaluation・anti-gaming", [
        "completion floor", "quality vector", "time-to-first-valid", "time-to-best",
        "human review cost", "agent contribution", "multi-agent ablation", "heldout campaign",
        "task-based operator", "benchmark saturation alarm",
    ], [
        "をfield checklistなしで定義する", "をraw criterionとconfidence付きで保存する",
        "へhardcode・metric gaming・oracle driftを仕込む", "でforwardingとorchestrationをmatched比較する",
        "を新しいcoherent design発見時にversion修正する",
    ]),
    ("T", "Composite evolution scenarios", [
        "single-agentからmulti-agentへの拡張", "一providerから三providerへの拡張",
        "一repositoryから複数repositoryへの拡張", "local chatからremote observerへの拡張",
        "manual integrationからowned integrationへの拡張", "one-shotからcontinuationへの拡張",
        "foreground taskからscheduled taskへの拡張", "unrestricted authorityからpolicy制御への拡張",
        "raw logからlearning skillへの拡張", "prototypeからlong-running team運用への拡張",
    ], [
        "を初期大目的から予見できる状況として与える", "を既存user historyとartifactを保持して実装する",
        "へ途中crash・concurrent user・provider failureを重ねる", "のchange amplificationとregressionを測る",
        "を三段階のcampaignで繰り返し進化させる",
    ]),
]


def main() -> None:
    output = Path(__file__).with_name("17-chat-development-system-five-x-ideas-1000.md")
    lines = [
        "# Chat development system — five-times-harder inventory (1,000 ideas)", "",
        "人間とCodex・Claude・Grokがnative chat roomで共同開発するsystem自体を、単なる機能数ではなく、体験・状態contract・競合/障害・自動評価・後続進化の深さで難しくする探索母集団。各中核能力を5方向へ展開し、動くだけのchat UIで早期飽和しないproduct taskを作る。", "",
    ]
    number = 0
    for letter, title, concepts, angles in SECTIONS:
        if len(concepts) != 10 or len(angles) != 5:
            raise ValueError(f"{letter}: expected 10 concepts and 5 angles")
        start = number + 1
        end = number + 50
        lines.extend([f"## {letter}. {title}（{start:04d}–{end:04d}）", ""])
        for concept in concepts:
            for angle in angles:
                number += 1
                lines.append(f"{number}. [C{number:04d}] {concept}{angle}")
        lines.append("")
    if number != 1000:
        raise ValueError(f"expected 1000 ideas, got {number}")
    output.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
