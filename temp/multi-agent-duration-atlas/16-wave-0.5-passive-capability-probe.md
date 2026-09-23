# Wave 0.5: passive provider capability probe

実施日: 2026-08-26

Status: Codex / Claude / Grokの非生成probeを実装し、WSL hostとnetwork-disabled devcontainer imageで観測済み。task durationのlive sampleはまだ0件。

## Outcome

`scripts/agent-duration-study probe-capability`を追加しました。providerへpromptを送らず、次の有限commandだけを実行します。

- CLI version
- root help
- providerが持つmodel catalog/list。ただし`--offline-only`ではCodexのbundled catalogだけを読み、Grokのprovider model listは呼ばない

raw stdout / stderr、binary path、account、prompt、codeはrecordへ保存しません。allowlistしたversion、model ID、catalog snapshot hint、effort広告値、coverage、command outcomeだけをschema validation後に一件一JSONへ保存します。

## Contract correction

Milestone Aのcapability v1は「CLIに設定値が広告されている」と「実行時にrequested valueが適用された」を十分に分けられませんでした。実観測前だったためcapability schemaをv2へ更新し、次を分離しました。

| Field | 証明するもの |
| --- | --- |
| `model_inventory` | catalog/list commandに掲載されたmodel |
| `model_identity` | task実行時のdefault/requested/resolved identity。受動probeでは推測しない |
| `setting_surfaces` | help/catalogに広告されたflag・値域・catalog default |
| `setting_probes` | explicit canaryで実際にrequested/applied/rejectedを確認した結果 |
| `metadata_scope` | `provider-current` / `bundled` / `not-requested` |
| `coverage` | 何をexact/partial/not-observedとして取得できたか |

`passive-cli` recordでは`generation_request_performed=false`、`setting_probes=[]`、`setting_application=not-observed`をsemantic validatorが強制します。広告値をappliedへ昇格したrecordはrejectされます。

## Observation surfaces

### WSL host / provider-current where available

| Provider | CLI identity | Model evidence | Effort evidence | Runtime default |
| --- | --- | --- | --- | --- |
| Codex | `0.146.0` | current catalog 9 entries、snapshot hintあり | model別enumerated | unresolved |
| Claude | `2.1.220` | list/defaultを取得できる非生成commandなし | `low, medium, high, xhigh, max`をhelpで広告 | unresolved |
| Grok | `1.0.5 (5115b46bc9) [stable]` | `grok-4.6` default、`grok-4.5` available | effort flagのみ。値域非広告 | `grok-4.6` alias-only |

Codex current catalogの主要差分:

- `gpt-5.6-sol` / `gpt-5.6-terra`: `low`から`ultra`
- `gpt-5.6-luna`: `low`から`max`
- 旧seriesはmodelごとに`xhigh`または`max`まで
- catalogの先頭やpriorityからruntime defaultを推測しない

### Frozen devcontainer image / offline-only

Image digest:

```text
sha256:3f58b6614a86e40bd3adfa49f9a9b5711bcf24b8a28fe574dec8ea1e0872cc9d
```

`docker run --network none`で観測しました。

| Provider | CLI identity | Metadata scope | Model evidence | Effort evidence |
| --- | --- | --- | --- | --- |
| Codex | `0.146.0` | bundled | 8 entries | model別enumerated |
| Claude | `2.1.220` | not-requested | not-observed | 5 valuesをhelpで広告 |
| Grok | `1.0.3 (1a29d5bc12)` | not-requested | not-observed | flag-only |

Grokのmodel evidenceが無いのは「modelが無い」という意味ではありません。offline-onlyがnetwork metadata commandを実行しなかったため`not-observed`です。

## Important finding: version alone is not a series boundary

同じCodex `0.146.0`でも、frozen imageのbundled catalogとWSL hostのprovider-current catalogは一致しませんでした。

- bundled: 8 entries。`gpt-5.2`を含む
- provider-current: 9 entries。`gpt-reserve`と`gpt-5.3-codex-spark`を含む
- `codex-auto-review`の広告effort上限もcatalog scope間で異なる

したがってduration atlasでは、CLI versionだけでseriesを結合しません。少なくともmodel ID、snapshot hint、CLI version/source、image digest、metadata scope、requested/applied setting confidenceを保持します。catalog広告差はtask実行時のresolved model差を直接証明しないため、live canaryのidentity evidenceとは別に扱います。

## Evidence files

sanitized capability v2 recordを[`evidence/wave-0.5/`](evidence/wave-0.5/)へ保存しました。

- `wave05-devcontainer-offline-*.json`: network-disabled frozen image
- `wave05-wsl-host-current-*.json`: current WSL host。Codex/Grokだけprovider metadataを試行

各recordは`agent-duration-study validate --kind capability`を通過します。probe commandの所要時間はprobe診断であり、agent task duration sampleへ混ぜません。

## Usage

Network metadataを許可する受動probe:

```bash
scripts/agent-duration-study probe-capability \
  --provider codex \
  --environment-kind host \
  --output-dir /tmp/duration-capabilities
```

offline-only probe:

```bash
scripts/agent-duration-study probe-capability \
  --provider grok \
  --environment-kind devcontainer \
  --cli-source container-image \
  --offline-only \
  --output-dir /tmp/duration-capabilities
```

一command最大timeoutは既定15秒、設定可能範囲は60秒以下です。未導入binary、失敗、timeoutもexceptionで消さずpartial capability recordとして残します。

## Remaining unknowns

受動probeでは次を証明できません。

- requested modelが実際にどのresolved buildへ到達したか
- requested effortがappliedされたか、silent fallbackしたか
- progress artifact / synthesis envelopeをprovider eventから観測できるか
- permission modeとnested delegationをtask runで固定できるか

次のlive canaryでは、これらを取得可能なproviderだけexact/partialへ昇格します。取得不能なら`unknown`を保持し、そのmodel/effort stratumをatlasへ掲載しません。

## Skill deliveryへの影響

`skill-creator`のprogressive disclosureに合わせ、これらの詳細recordを将来の`SKILL.md`へ埋め込みません。raw capability/run evidenceは詳細層、集約済みseries keyとcoverageだけをbounded query scriptが読み、通常のskill responseには該当cellだけを返します。

## Validation

fixtureはhelp/model outputへsecret markerとprivate-looking pathを混ぜ、生成recordに残らないことを確認します。また、offline-only、missing binary、invalid safety input、immutable CLI write、schema再validationを含む34 testsがpassしました。
