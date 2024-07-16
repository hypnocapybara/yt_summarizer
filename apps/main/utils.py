import re
from datetime import timedelta

from .models import Chapter


def split_chaptered_summary_into_parts(summary: str) -> list[Chapter]:
    """
    Splits summary text into parts. Ex:
    [0:00:00] Into
    - Point 1
    - Point 2
    --->
    [
        {
            "title": Intro
            "start": 0
            "time_label": "0:00:00",
            "lines": [
                "- Point 1",
                "- Point 2",
            ]
        }
    ]
    """

    if "\n\n" not in summary:
        return []

    result = []
    parts = summary.split('\n\n')
    for part in parts:
        part_lines = part.split('\n')

        time_parts = re.findall('\[(\d+:\d+:\d+)\]', part_lines[0])[0]

        hour, minute, second = time_parts.split(':')
        time_delta = timedelta(hours=int(hour), minutes=int(minute), seconds=int(second))
        start = time_delta.seconds

        title = part_lines[0].split(']')[1].strip()

        result.append(Chapter(
            title=title,
            start=start,
            time_label=time_parts,
            lines=part_lines[1:]
        ))

    return result
