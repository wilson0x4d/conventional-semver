# SPDX-FileCopyrightText: © 2026 Shaun Wilson
# SPDX-FileCopyrightText: (c) 2024 sw4k 
# SPDX-License-Identifier: MIT

from __future__ import annotations

from .GitEntry import GitEntry


class GitEntryParser:

    def parse(self, input_str: str) -> GitEntry:
        if not input_str:
            return GitEntry()

        entry = GitEntry()

        lines = input_str.split('\n')

        entry.commit_hash = lines[0]

        if len(lines) > 1:
            refs_raw = lines[1]
            if refs_raw:
                entry.refs = [
                    ref.strip()
                    for ref in refs_raw.split(',')
                    if ref
                ]

            if len(lines) > 2:
                try:
                    subject_end = lines.index('', 2)
                except ValueError:
                    subject_end = len(lines)

                subject_lines = lines[2:subject_end]
                entry.subject = '\n'.join(subject_lines)

                body_start = subject_end + 1
                if body_start < len(lines):
                    try:
                        body_end = lines.index('', body_start)
                    except ValueError:
                        body_end = len(lines)

                    body_lines = lines[body_start:body_end]
                    entry.body = '\n'.join(body_lines)

                    footer_start = body_end + 1
                    if footer_start < len(lines):
                        entry.footers = [
                            footer
                            for footer in lines[footer_start:]
                            if footer
                        ]
                    else:
                        entry.footers = []
            else:
                entry.subject = ''
                entry.body = ''
                entry.footers = []

        return entry
