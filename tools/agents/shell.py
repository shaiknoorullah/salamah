"""Split a shell command line into simple commands for the agent guards."""

import posixpath
import re
import shlex

_SEPARATORS = frozenset({";", "&&", "||", "|", "|&", "&", "(", ")"})
_ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_SHELLS = frozenset({"sh", "bash", "zsh", "dash"})
_SHELL_C = re.compile(r"^-[a-zA-Z]*c[a-zA-Z]*$")
_ARG_OPTS = {
    "env": {"-u", "--unset", "-C", "--chdir"},
    "sudo": {"-u", "-g", "-h", "-p", "-C", "-D", "-r", "-t", "-U"},
}
_GIT_ARG_OPTS = frozenset({"-C", "-c", "--git-dir", "--work-tree", "--namespace"})


_HEREDOC = re.compile(r"<<(-?)[ \t]*(['\"]?)([^\s'\"<>;&|]+)\2")


def _skip_heredoc(text: str, i: int, out: list[str]) -> int:
    """Keep the heredoc's own line, drop its body, resume after the delimiter line."""
    end = text.find("\n", i)
    if end < 0:
        out.append(text[i:])
        return len(text)
    out.append(text[i:end])
    m = _HEREDOC.match(text, i)
    if not m:
        return len(text)
    word, strip_tabs = m.group(3), m.group(1) == "-"
    pos = end + 1
    while pos <= len(text):
        nxt = text.find("\n", pos)
        line = text[pos : len(text) if nxt < 0 else nxt]
        if (line.lstrip("\t") if strip_tabs else line) == word:
            out.append(" ; ")
            return len(text) if nxt < 0 else nxt + 1
        if nxt < 0:
            break
        pos = nxt + 1
    return len(text)


def _preprocess(text: str) -> str:
    """Turn unquoted newlines into `;`, decode `$'..'`, drop heredoc bodies."""
    out: list[str] = []
    i, n, quote = 0, len(text), ""
    while i < n:
        ch = text[i]
        if quote == "'":
            quote = "" if ch == "'" else quote
        elif quote == '"':
            if ch == "\\" and i + 1 < n:
                out.append(ch)
                i += 1
                ch = text[i]
            elif ch == '"':
                quote = ""
        elif ch == "\\" and i + 1 < n:
            out.append(ch)
            i += 1
            ch = text[i]
        elif ch in "'\"":
            quote = ch
        elif ch == "$" and text[i + 1 : i + 2] == "'":
            j = i + 2
            while j < n and text[j] != "'":
                j += 2 if text[j] == "\\" else 1
            raw = text[i + 2 : j]
            try:
                raw = raw.encode("ascii").decode("unicode_escape")
            except (UnicodeError, ValueError):
                pass
            out.append(shlex.quote(raw))
            i = j + 1
            continue
        elif ch == "\n":
            ch = " ; "
        elif text.startswith("<<", i) and text[i + 2 : i + 3] != "<":
            i = _skip_heredoc(text, i, out)
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _tokens(text: str) -> list[str]:
    lex = shlex.shlex(_preprocess(text), posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    lex.commenters = ""
    return list(lex)


def _unwrap(cmd: list[str]) -> list[list[str]]:
    """Strip wrappers and env assignments; unwrap `sh -c`. Returns simple commands."""
    cmd = list(cmd)
    while cmd:
        name = posixpath.basename(cmd[0])
        if _ASSIGN.match(cmd[0]):
            cmd = cmd[1:]
        elif name in ("env", "sudo", "command", "exec", "nohup", "time", "nice"):
            opts = _ARG_OPTS.get(name, set())
            i, extra = 1, []
            while i < len(cmd) and (cmd[i].startswith("-") or _ASSIGN.match(cmd[i])):
                tok = cmd[i]
                if name == "env" and tok in ("-S", "--split-string"):
                    extra = shlex.split(cmd[i + 1]) if i + 1 < len(cmd) else []
                    i += 2
                elif name == "env" and tok.startswith("--split-string="):
                    extra = shlex.split(tok.split("=", 1)[1])
                    i += 1
                else:
                    i += 2 if tok in opts else 1
            cmd = extra + cmd[i:]
        elif name in _SHELLS:
            flags = [t for t in cmd[1:] if t.startswith("-")]
            idx = next((k for k, t in enumerate(cmd[1:], 1) if _SHELL_C.match(t)), None)
            if idx is not None and idx + 1 < len(cmd) and len(flags) >= 1:
                return split_commands(cmd[idx + 1])
            return [cmd]
        elif name == "git":
            i = 1
            while i < len(cmd) and cmd[i].startswith("-") and cmd[i] != "--":
                i += 2 if cmd[i] in _GIT_ARG_OPTS else 1
            return [["git", *cmd[i:]]]
        else:
            return [cmd]
    return []


def split_commands(command: str) -> list[list[str]]:
    """Split into simple commands (token lists); raises ValueError on bad quoting."""
    result: list[list[str]] = []
    current: list[str] = []
    for tok in [*_tokens(command), ";"]:
        if tok in _SEPARATORS:
            result.extend(_unwrap(current))
            current = []
        else:
            current.append(tok)
    return result
