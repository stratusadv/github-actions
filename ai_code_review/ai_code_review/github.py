from __future__ import annotations

import requests

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


BOT_LOGIN = 'github-actions[bot]'
GITHUB_API = 'https://api.github.com'


class GitHubClient:
    def __init__(self, pr_number: str, repo: str, token: str) -> None:
        self._commit_sha = ''
        self._pr_number = pr_number
        self._repo = repo
        self._session = self._build_session(token)

    def _build_session(self, token: str) -> requests.Session:
        session = requests.Session()

        session.headers.update({
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {token}',
        })

        retry = Retry(
            backoff_factor=0.5,
            status_forcelist=[502, 503, 504],
            total=3,
        )

        session.mount('https://', HTTPAdapter(max_retries=retry))

        return session

    def _fetch_head_sha(self) -> str:
        if self._commit_sha:
            return self._commit_sha

        response = self._session.get(
            self._pr_url(),
            timeout=30,
        )
        response.raise_for_status()

        self._commit_sha = response.json()['head']['sha']

        return self._commit_sha

    def _pr_url(self) -> str:
        return (
            f'{GITHUB_API}/repos/{self._repo}'
            f'/pulls/{self._pr_number}'
        )

    def _repo_url(self) -> str:
        return f'{GITHUB_API}/repos/{self._repo}'

    def delete_previous_comments(self) -> None:
        page = 1

        while True:
            response = self._session.get(
                f'{self._pr_url()}/comments',
                params={'page': page, 'per_page': 100},
                timeout=30,
            )
            response.raise_for_status()

            comment_list = response.json()

            if not comment_list:
                break

            for comment in comment_list:
                if comment.get('user', {}).get('login') != BOT_LOGIN:
                    continue

                self._session.delete(
                    f'{self._repo_url()}/pulls/comments/{comment["id"]}',
                    timeout=30,
                )

            page += 1

    def post_comments(self, comment_list: list[dict]) -> None:
        if not comment_list:
            return

        commit_sha = self._fetch_head_sha()

        response = self._session.post(
            f'{self._pr_url()}/reviews',
            json={
                'body': '',
                'comments': [
                    {
                        'body': comment['body'],
                        'line': comment['line'],
                        'path': comment['path'],
                        'side': comment.get('side', 'RIGHT'),
                    }
                    for comment in comment_list
                ],
                'commit_id': commit_sha,
                'event': 'COMMENT',
            },
            timeout=30,
        )

        response.raise_for_status()
