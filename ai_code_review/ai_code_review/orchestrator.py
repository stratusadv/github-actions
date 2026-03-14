from __future__ import annotations

import sys

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from ai_code_review.config import CONSENSUS_RUNS, CONSENSUS_THRESHOLD, ReviewConfig, _registry
from ai_code_review.consensus import comments_from_intel, consensus_comments
from ai_code_review.intelligence.prompt import load_instruction_prompt
from ai_code_review.linter import RuffLinter

if TYPE_CHECKING:
    from ai_code_review.diff import DiffSet
    from ai_code_review.github import GitHubClient


MAX_CONCURRENT_API_CALL = 3


@dataclass
class ReviewOrchestrator:
    diffs: DiffSet
    github: GitHubClient
    consensus_runs: int = CONSENSUS_RUNS
    consensus_threshold: int = CONSENSUS_THRESHOLD
    review_dir: Path = field(default_factory=lambda: Path('.review'))

    def _run_config(self, config: ReviewConfig) -> list[dict]:
        filtered = self.diffs.filter_by_extension(
            config.extensions,
            max_length=config.max_diff_length,
        )

        if not filtered.strip():
            return []

        sources = self.diffs.read_files(config.extensions)

        standard = config.strategy.load(config.skills)

        instruction = load_instruction_prompt(self.review_dir)

        if instruction.snippets:
            standard.lb()
            standard.prompt(instruction)

        all_comments: list[list[dict]] = []

        def _single_run(run_index: int) -> list[dict]:
            try:
                bot = config.bot(llm_temperature=config.temperature)

                intel = bot.process(
                    diff=filtered,
                    sources=sources,
                    standard=standard,
                )
            except Exception:
                print(f'{config.label} run {run_index} failed', file=sys.stderr)
                return []
            else:
                return comments_from_intel(
                    intel,
                    self.diffs.added,
                    config.prefix,
                )

        with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_API_CALL) as executor:
            futures = [
                executor.submit(_single_run, index)
                for index in range(self.consensus_runs)
            ]

            all_comments.extend(
                future.result()
                for future in as_completed(futures)
            )

        return consensus_comments(all_comments, self.consensus_threshold)

    def run(self) -> None:
        applicable = [
            config for config in _registry
            if config.enabled
            and self.diffs.has_extension(config.extensions)
        ]

        if not applicable:
            return

        comments: list[dict] = []

        with ThreadPoolExecutor(max_workers=len(applicable)) as executor:
            futures = {
                executor.submit(self._run_config, config): config
                for config in applicable
            }

            for future in as_completed(futures):
                comments.extend(future.result())

        self.github.post_comments(comments)

    def run_ruff(self) -> None:
        linter = RuffLinter(diffs=self.diffs)
        comments = linter.run()

        if comments:
            self.github.post_comments(comments)
