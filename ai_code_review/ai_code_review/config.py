from __future__ import annotations

import os

from dataclasses import dataclass

from ai_code_review.diff import MAX_DIFF_LENGTH
from ai_code_review.intelligence.bots import BackendReviewBot, FrontendReviewBot, _CodeReviewBot
from ai_code_review.intelligence.prompt import BasePromptStrategy, PackagePromptStrategy


CONSENSUS_RUNS = int(os.environ.get('AI_REVIEW_CONSENSUS_RUNS', '3'))
CONSENSUS_THRESHOLD = int(os.environ.get('AI_REVIEW_CONSENSUS_THRESHOLD', '1'))
OPENCODE_MODULE = os.environ.get('AI_REVIEW_OPENCODE_MODULE', '')

_registry: list[ReviewConfig] = []


@dataclass
class ReviewConfig:
    bot: type[_CodeReviewBot]
    enabled_var: str
    extensions: tuple[str, ...]
    label: str
    prefix: str
    skills: set[str]
    strategy: BasePromptStrategy
    max_diff_length: int = MAX_DIFF_LENGTH
    temperature: float = 0.0

    @property
    def enabled(self) -> bool:
        return os.environ.get(self.enabled_var, 'true').lower() == 'true'


def register(*configs: ReviewConfig) -> None:
    _registry.extend(configs)


if OPENCODE_MODULE:
    register(
        ReviewConfig(
            bot=BackendReviewBot,
            enabled_var='AI_REVIEW_BACKEND',
            extensions=('.py',),
            label='Backend Bot',
            prefix='Backend Bot',
            skills={
                'best-practices', 'form_views', 'models', 'queryset',
                'seeding', 'service-layer', 'service_layer',
            },
            strategy=PackagePromptStrategy(
                module=OPENCODE_MODULE,
            ),
        ),
        ReviewConfig(
            bot=FrontendReviewBot,
            enabled_var='AI_REVIEW_FRONTEND',
            extensions=('.html', '.css', '.js'),
            label='Frontend Bot',
            prefix='Frontend Bot',
            skills={
                'badge_templates', 'best-practices', 'button-template',
                'container-template', 'detail_templates', 'form_templates',
                'list_templates', 'tab-template', 'table-template', 'template',
            },
            strategy=PackagePromptStrategy(
                module=OPENCODE_MODULE,
            ),
        ),
    )
