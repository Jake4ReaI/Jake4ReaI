"""Tic-tac-toe on the profile README.

A visitor plays X by opening an issue titled "ttt|move|<0-8>". The board
answers as O, the README is redrawn, and the workflow closes the issue.
Run with --selfcheck to test the logic, or --reset to start a fresh board.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "game", "state.json")
README = os.path.join(ROOT, "README.md")
REPLY = os.path.join(ROOT, "game", "reply.txt")
REPO = os.environ.get("GITHUB_REPOSITORY", "Jake4ReaI/Jake4ReaI")

START, END = "<!-- game:start -->", "<!-- game:end -->"
WINS = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]
FRESH = {"board": [" "] * 9, "over": False, "result": "", "played": 0, "draws": 0, "board_wins": 0, "visitor_wins": 0, "last": ""}


def winner(b):
    for x, y, z in WINS:
        if b[x] != " " and b[x] == b[y] == b[z]:
            return b[x]
    return "draw" if " " not in b else None


def score(b, turn):
    """Best outcome for O from this position: 1 win, 0 draw, -1 loss."""
    w = winner(b)
    if w:
        return {"O": 1, "X": -1, "draw": 0}[w]
    results = []
    for i in range(9):
        if b[i] == " ":
            b[i] = turn
            results.append(score(b, "X" if turn == "O" else "O"))
            b[i] = " "
    return max(results) if turn == "O" else min(results)


def best_reply(b):
    best, pick = -2, None
    for i in (4, 0, 2, 6, 8, 1, 3, 5, 7):
        if b[i] == " ":
            b[i] = "O"
            s = score(b, "X")
            b[i] = " "
            if s > best:
                best, pick = s, i
    return pick


def play(state, cell, player):
    """Apply a visitor move and the board's answer. Returns the reply text."""
    if state["over"]:
        state.update(board=[" "] * 9, over=False, result="")
    b = state["board"]
    if b[cell] != " ":
        return "That cell is taken. Pick an empty one."
    b[cell] = "X"
    state["last"] = player
    w = winner(b)
    if not w:
        b[best_reply(b)] = "O"
        w = winner(b)
    if not w:
        return "Move played, and the board has answered. Refresh the profile to see it."
    state["over"], state["result"] = True, w
    state["played"] += 1
    key = {"draw": "draws", "O": "board_wins", "X": "visitor_wins"}[w]
    state[key] += 1
    return {
        "draw": "A draw. That is the best anyone can do. Click an empty cell to start again.",
        "O": "The board wins this one. Click an empty cell to start again.",
        "X": "You won. Nobody was supposed to manage that.",
    }[w]


def render(state):
    b = state["board"]
    status = {
        "": "You are X. Click an empty cell, then press <b>Submit new issue</b>. The board answers in about a minute.",
        "draw": "Draw. Click an empty cell to start a new game.",
        "O": "The board won. Click an empty cell to start a new game.",
        "X": "A visitor won. Click an empty cell to start a new game.",
    }[state["result"]]
    rows = []
    for r in range(3):
        cells = []
        for i in range(r * 3, r * 3 + 3):
            if b[i] == " ":
                link = "https://github.com/%s/issues/new?title=ttt%%7Cmove%%7C%d&body=Press+Submit+new+issue+to+play+this+move." % (REPO, i)
                cells.append('<td><a href="%s"><img src="./assets/game/empty.svg" width="92" alt="empty cell, play here" /></a></td>' % link)
            else:
                name = "x" if b[i] == "X" else "o"
                cells.append('<td><img src="./assets/game/%s.svg" width="92" alt="%s" /></td>' % (name, b[i]))
        rows.append("  <tr>\n    " + "\n    ".join(cells) + "\n  </tr>")
    tally = "Games: %d &nbsp;•&nbsp; Draws: %d &nbsp;•&nbsp; Board wins: %d &nbsp;•&nbsp; Visitor wins: %d" % (
        state["played"], state["draws"], state["board_wins"], state["visitor_wins"])
    if state["last"]:
        tally += ' &nbsp;•&nbsp; Last move: <a href="https://github.com/%s">@%s</a>' % (state["last"], state["last"])
    return "\n".join([
        START,
        '<p align="center">%s</p>' % status,
        "",
        '<table align="center">',
        "\n".join(rows),
        "</table>",
        "",
        '<p align="center"><sub>%s</sub></p>' % tally,
        END,
    ])


def save(state):
    with open(STATE, "w", encoding="utf-8", newline="\n") as f:
        json.dump(state, f, indent=2)
        f.write("\n")
    with open(README, encoding="utf-8") as f:
        text = f.read()
    a, z = text.index(START), text.index(END) + len(END)
    with open(README, "w", encoding="utf-8", newline="\n") as f:
        f.write(text[:a] + render(state) + text[z:])


def selfcheck():
    """Whatever X plays, the board never loses."""
    def walk(b):
        w = winner(b)
        if w:
            assert w != "X", b
            return 1
        n = 0
        for i in range(9):
            if b[i] == " ":
                c = b[:]
                c[i] = "X"
                if not winner(c):
                    c[best_reply(c)] = "O"
                n += walk(c)
        return n
    games = walk([" "] * 9)
    s = dict(FRESH, board=[" "] * 9)
    assert play(s, 4, "tester").startswith("Move played") and s["board"].count("O") == 1
    assert play(s, 4, "tester").startswith("That cell is taken")
    assert render(s).count("<td>") == 9 and render(s).count("issues/new") == 7
    print("selfcheck ok: %d complete games, board never lost" % games)


def main():
    if "--selfcheck" in sys.argv:
        return selfcheck()
    if "--reset" in sys.argv:
        return save(dict(FRESH, board=[" "] * 9))
    with open(STATE, encoding="utf-8") as f:
        state = json.load(f)
    m = re.fullmatch(r"ttt\|move\|([0-8])", os.environ.get("TITLE", ""))
    player = os.environ.get("PLAYER", "")
    if not re.fullmatch(r"[A-Za-z0-9-]{1,39}", player):
        player = ""
    if m:
        reply = play(state, int(m.group(1)), player)
        save(state)
    else:
        reply = "That is not a move I understand. Click an empty cell on the profile board."
    with open(REPLY, "w", encoding="utf-8", newline="\n") as f:
        f.write(reply + "\n")


if __name__ == "__main__":
    main()
