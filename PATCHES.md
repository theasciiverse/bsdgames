# Changes from upstream

This is the Asciiverse packaging of BSD Games, from Mike Sharov's
bsd-games (https://sourceforge.net/projects/bsd-games, the `upstream`
remote): the Linux port of the classic BSD games, continued from the
bsdgames 2.17 that Debian and others still ship, and rewritten for
modern curses. The `asciiverse` branch starts from upstream's `master`
at `9f8b7e6` (2025-07-18, after v3.3).

In the Asciiverse catalog each game is its own title, credited as part of
BSD Games. 15 of upstream's 18 programs are published: adventure is left
out because the catalog's Colossal Cave is the same game, and arithmetic
and caesar because they are not games.

## Code

- **Scores without root.** Scores were kept only in system score files
  (`/var/lib/bsdgames/*.scores`), which the games open but never create,
  so an install without root kept no scores at all. When the system file
  is not writable, each game now keeps its own in the XDG data folder,
  `bsdgames/<game>.scores` (`common/scores.c`).
- **Card suits in UTF-8 terminals.** The suit symbols were shown only when
  `LANG` contained a lower-case `utf8`, so the usual `C.UTF-8` and
  `en_US.UTF-8` got letters (S, H, D, C) in klondike and cribbage. The
  check now asks the locale for its character set (`nl_langinfo`), which
  also honours `LC_ALL` and `LC_CTYPE` (`common/ui.c`).
- **atc's planes keep their colour.** Marked planes, which every new
  plane is, were drawn with `wstandout`, which replaces the plane colour,
  leaving them black on black in reverse; and `wstandend` then dropped the
  colour for the planes after them. Marked planes now just turn reverse
  video on and off (`atc/graphics.c`).
- **Centred on the screen.** Most games sat at the bottom of the terminal
  (their windows were placed at `LINES` minus their height) and several
  at its left edge. They now sit in the middle, through two helpers in
  `common/ui.c`: `centered_origin` for a fixed block (gomoku, klondike,
  dab with its status line, drop4, robots, hangman, atc and battlestar's
  space fight), and `centered_layout` for a board under a scrolling
  message area, which now gets at most a set number of lines so the
  whole can be centred (cribbage and spirhunt 8, sail 10, gofish 18, so
  its instructions fit). drop4 and robots centre what they draw, not
  their wider 80-column windows. A terminal smaller than a game shows its
  top left part, as before.
- **Grey that shows everywhere.** gomoku's grid, robots' junk heaps,
  spirhunt's space, drop4's help text and atc's radar background were
  black with A_BOLD on black, which only terminals that brighten bold
  text show as grey; elsewhere, the website's preview player included,
  they were invisible. They use a new `COLOR_GREY`: bright black where
  the terminal has 16 colours, white otherwise.
- **The name on score tables.** `player_name` now takes `LOGNAME` and
  `USER` before `getlogin`, which reads the login from the system and
  ignores them, so a player can choose the name the tables show.

## Packaging (new files)

- `asciiverse/games.txt`: the catalog id and program of each game.
- `asciiverse/build.sh`: builds the games into `out/` with upstream's
  configure and Makefile, linking `-lncursesw` by default: upstream links
  `-lncurses`, which on Debian and Ubuntu lacks the wide-character calls
  the shared UI code uses.
- `asciiverse/package.sh`: one archive per game and target in `dist/`, the
  binary at the top beside its man page, LICENSE, README.md and the game's
  own LICENSE.
- `asciiverse/hangman/words`: hangman's word list, built from SCOWL
  2020.12.07 (sizes 10 to 50, English and American words, lower-case
  only, 61,494 words; release sha256
  `5587667caa20c4891390c2d42dbb4d5c4c3f41bee77af1457ece3ba23fb859cc`),
  with SCOWL's copyright notice beside it. Many systems have no
  `/usr/share/dict/words`; av starts hangman with `-d words`.
- `asciiverse/record/`: the preview recorder (`rec.py`, from New BSD Games')
  and one driver per game that plays it for its cast in
  `asciiverse/casts/`, reading the screen through pyte.
- `.github/workflows/release.yml`: static Linux builds in Alpine (x86_64,
  aarch64) and macOS (x86_64, arm64), plus SHA256SUMS, on a tag. No
  Windows build yet.

## Ours

- **How to play it, at the top of README.md.** A short note on installing and
  starting it with av, or from a release archive; the original text follows
  unchanged.
