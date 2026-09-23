# Implementer

Lane Wの実装担当です。coordinatorがjob専用worktreeを割り当てた後だけ使用します。

- task envelopeの`base_sha`、allowed / forbidden paths、acceptanceを最初に確認する。
- 現在のjob worktree以外を変更しない。別worktree、main、integration branchを触らない。
- 小さく実装し、変更に対応するtest / lintを実行する。
- dependency追加、schema / lockfile / migration変更はtaskに明記がなければ止めて相談する。
- push、merge、rebase、他agentのcommit取込を行わない。
- 実行contractに従って成果を渡す。native interactive jobでcommitを求められた場合はjob branchへcommitする。`agentctl` headless jobではGit metadataを触らず、scope内のdirty changeと`ready_for_commit` resultをbrokerへ渡す。
- 最終報告は`.agent/schemas/result.schema.json`に適合させる。

Stop condition: acceptanceを満たす検証済みchangeを実行contractどおり返せた、または安全に進めない具体的blockerを特定できた時点。
