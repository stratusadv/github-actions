from dandy import Bot, Prompt

from ai_code_review.intelligence.intel import CodeReviewIntel


class _CodeReviewBot(Bot):
    intel_class = CodeReviewIntel

    def process(
        self,
        diff: str,
        sources: dict[str, str],
        standard: Prompt,
    ) -> CodeReviewIntel:
        prompt = Prompt()

        if standard.snippets:
            prompt.prompt(standard)
            prompt.lb()

        if sources:
            prompt.heading('Source Files')
            prompt.lb()

            for path, content in sources.items():
                prompt.sub_heading(path)
                prompt.text(content, triple_backtick=True)
                prompt.lb()

        prompt.heading('Pull Request Diff')
        prompt.text(diff, triple_backtick=True)

        return self.llm.prompt_to_intel(prompt=prompt)


class BackendReviewBot(_CodeReviewBot):
    guidelines = (
        Prompt()
        .sub_heading('What to Review')
        .text(
            'Everything covered by the project standards provided above.'
            ' Treat the standards as the complete checklist.'
            ' Be thorough and verify every point is met for each'
            ' added or changed line.'
        )
        .lb()
        .sub_heading('Rules')
        .list([
            'Every comment MUST cite which project standard is violated.',
            'Each comment must reference the exact file path and line'
            ' number from the diff.',
            'Never reference lines outside the diff.',
            'Comments must be specific and actionable: state what is'
            ' wrong, which standard applies, and what the fix looks like.',
            'Return an empty comments list ONLY when every added or'
            ' changed line satisfies all provided standards.',
        ])
        .lb()
        .sub_heading('What to Ignore')
        .list([
            'Linting, formatting, and import ordering. Ruff handles those.',
            'Deliberate design decisions such as custom manager methods,'
            ' intentional denormalization, or overridden Django defaults.',
            'Speculative, nitpick, or purely stylistic observations.',
        ])
        .lb()
        .sub_heading('Comment Format')
        .text(
            'Every comment must follow this exact structure:'
            '\n1. State what is wrong.'
            '\n2. Cite the violated standard.'
            '\n3. Show what the fix looks like.'
            '\n4. If referencing another file, end with: See `path/to/file`.'
        )
    )
    role = 'Senior Django Developer'
    task = (
        'Find violations of the project standards in the provided'
        ' pull request diff and produce review comments.'
    )


class FrontendReviewBot(_CodeReviewBot):
    guidelines = (
        Prompt()
        .sub_heading('What to Review')
        .text(
            'Everything covered by the project template standards provided above.'
            ' Treat the standards as the complete checklist.'
            ' Be thorough and verify every point is met for each'
            ' added or changed line.'
        )
        .lb()
        .sub_heading('Rules')
        .list([
            'Every comment MUST cite which project template standard is violated.',
            'Each comment must reference the exact file path and line'
            ' number from the diff.',
            'Never reference lines outside the diff.',
            'Comments must be specific and actionable: state what is'
            ' wrong, which standard applies, and what the fix looks like.',
            'Return an empty comments list ONLY when every added or'
            ' changed line satisfies all provided standards.',
        ])
        .lb()
        .sub_heading('What to Ignore')
        .list([
            'Linting and formatting. Other tooling handles those.',
            'Deliberate design decisions such as custom template tags,'
            ' intentional inline styles for one-off overrides, or'
            ' project-specific component variations.',
            'Speculative, nitpick, or purely stylistic observations.',
        ])
        .lb()
        .sub_heading('Comment Format')
        .text(
            'Every comment must follow this exact structure:'
            '\n1. State what is wrong.'
            '\n2. Cite the violated standard.'
            '\n3. Show what the fix looks like.'
            '\n4. If referencing another file, end with: See `path/to/file`.'
        )
    )
    role = 'Senior Frontend Developer'
    task = (
        'Find violations of the project template standards in the'
        ' provided pull request diff and produce review comments.'
    )
