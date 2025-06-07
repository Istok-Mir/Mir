from __future__ import annotations
from Mir.types.lsp import MarkedString, MarkupContent
from sublime_plugin import sublime
from typing import Any
import mdpopups
import re

class MinihtmlKind:
    FORMAT_STRING = 0x1
    FORMAT_MARKED_STRING = 0x2
    FORMAT_MARKUP_CONTENT = 0x4


REPLACEMENT_MAP = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "\t": 4 * "&nbsp;",
    "\n": "<br>",
    "\xa0": "&nbsp;",  # non-breaking space
    "\xc2": "&nbsp;",  # control character
}

def _replace_match(match: Any) -> str:
    special_match = match.group('special')
    if special_match:
        return REPLACEMENT_MAP[special_match]
    url = match.group('url')
    if url:
        return f"<a href='{url}'>{url}</a>"
    return len(match.group('multispace')) * '&nbsp;'

PATTERNS = [
    r'(?P<special>[{}])'.format(''.join(REPLACEMENT_MAP.keys())),
    r'(?P<url>https?://(?:[\w\d:#@%/;$()~_?\+\-=\\\.&](?:#!)?)*)',
    r'(?P<multispace> {2,})',
]

def text2html(content: str) -> str:
    REPLACEMENT_RE = re.compile('|'.join(PATTERNS), flags=re.IGNORECASE)
    return re.sub(REPLACEMENT_RE, _replace_match, content)

def minihtml(
    view: sublime.View,
    content: MarkedString | MarkupContent | list[MarkedString],
    allowed_formats: int,
) -> str:
    """
    Formats provided input content into markup accepted by minihtml.

    Content can be in one of those formats:

     - string: treated as plain text
     - MarkedString: string or { language: string; value: string }
     - MarkedString[]
     - MarkupContent: { kind: MarkupKind, value: string }

    We can't distinguish between plain text string and a MarkedString in a string form so
    FORMAT_STRING and FORMAT_MARKED_STRING can't both be specified at the same time.

    :param view
    :param content
    :param allowed_formats: Bitwise flag specifying which formats to parse.

    :returns: Formatted string
    """
    if allowed_formats == 0:
        raise ValueError("Must specify at least one format")
    parse_string = bool(allowed_formats & MinihtmlKind.FORMAT_STRING)
    parse_marked_string = bool(allowed_formats & MinihtmlKind.FORMAT_MARKED_STRING)
    parse_markup_content = bool(allowed_formats & MinihtmlKind.FORMAT_MARKUP_CONTENT)
    if parse_string and parse_marked_string:
        raise ValueError("Not allowed to specify FORMAT_STRING and FORMAT_MARKED_STRING at the same time")
    is_plain_text = True
    result = ''
    if (parse_string or parse_marked_string) and isinstance(content, str):
        # plain text string or MarkedString
        is_plain_text = parse_string
        result = content
    if parse_marked_string and isinstance(content, list):
        # MarkedString[]
        formatted = []
        for item in content:
            value = ""
            language = None
            if isinstance(item, str):
                value = item
            else:
                value = item.get("value") or ""
                language = item.get("language")

            if language:
                formatted.append(f"```{language}\n{value}\n```\n")
            else:
                formatted.append(value)

        is_plain_text = False
        result = "\n".join(formatted)
    if (parse_marked_string or parse_markup_content) and isinstance(content, dict):
        # MarkupContent or MarkedString (dict)
        language = content.get("language")
        kind = content.get("kind")
        value = content.get("value") or ""
        if parse_markup_content and kind:
            # MarkupContent
            is_plain_text = kind != "markdown"
            result = value
        if parse_marked_string and language:
            # MarkedString (dict)
            is_plain_text = False
            result = f"```{language}\n{value}\n```\n"
    if is_plain_text:
        return f"<p>{text2html(result)}</p>" if result else ''
    else:
        frontmatter = {
            "allow_code_wrap": True,
            "markdown_extensions": [
                "markdown.extensions.admonition",
                {
                    "pymdownx.magiclink": {
                        # links are displayed without the initial ftp://, http://, https://, or ftps://.
                        "hide_protocol": True,
                        # GitHub, Bitbucket, and GitLab commit, pull, and issue links are are rendered in a shorthand
                        # syntax.
                        "repo_url_shortener": True
                    }
                }
            ]
        }
        # Workaround CommonMark deficiency: two spaces followed by a newline should result in a new paragraph.
        result = re.sub('(\\S)  \n', '\\1\n\n', result)
        return mdpopups.md2html(view, mdpopups.format_frontmatter(frontmatter) + result)
