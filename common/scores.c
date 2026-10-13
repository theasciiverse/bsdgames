// Copyright (c) 2016 by Mike Sharov <msharov@users.sourceforge.net>
// This file is free software, distributed under the BSD license.

#include "../config.h"
#include <sys/file.h>
#include <sys/uio.h>

struct ScorefileHeader {
    char	magic [6];
    uint16_t	sum;
};

// The system score file when the player can write to it, else the
// player's own one in the XDG data folder, bsdgames/<name>.scores.
// Installed without root (by av, or from an archive) there is no system
// score file, and no scores were ever kept.
static const char* score_file_path (const char* filename, char* buf, size_t bufsz, bool create)
{
    if (0 == access (filename, W_OK))
	return filename;
    const char* base = strrchr (filename, '/');
    base = base ? base+1 : filename;
    size_t dirlen = strlen (player_saved_game_dir (buf, bufsz));
    snprintf (&buf[dirlen], bufsz-dirlen, "/bsdgames");
    if (create)
	mkpath (buf, 0755);
    dirlen = strlen (buf);
    snprintf (&buf[dirlen], bufsz-dirlen, "/%s", base);
    return buf;
}

bool read_score_file (const char* filename, const char* magic, void* scores, size_t scoresSize)
{
    char pathbuf [PATH_MAX];
    filename = score_file_path (filename, pathbuf, sizeof(pathbuf), false);
    int fd = open (filename, O_RDONLY);
    if (fd < 0)
	return false;
    struct ScorefileHeader header;
    struct iovec iov[2] = {
	{ &header, sizeof(header)},
	{ scores, scoresSize}
    };
    while (0 != flock (fd, LOCK_SH))
	sleep (1);
    size_t br = readv (fd, iov, ArraySize(iov));
    close (fd);
    // Check that score list appears valid
    return br == sizeof(header)+scoresSize
	    && memcmp (header.magic, magic, sizeof(header.magic)) == 0
	    && header.sum == bsdsum (scores, scoresSize, 0);
}

void write_score_file (const char* filename, const char* magic, const void* scores, size_t scoresSize)
{
    char pathbuf [PATH_MAX];
    filename = score_file_path (filename, pathbuf, sizeof(pathbuf), true);
    int fd = open (filename, O_WRONLY| O_CREAT, 0644);
    if (fd < 0)
	return;
    struct ScorefileHeader header;
    memcpy (header.magic, magic, sizeof(header.magic));
    header.sum = bsdsum (scores, scoresSize, 0);
    #pragma GCC diagnostic ignored "-Wcast-qual"
    const struct iovec iov[2] = {
	{ &header, sizeof(header)},
	{ (void*) scores, scoresSize}
    };
    while (0 != flock (fd, LOCK_EX))
	sleep (1);
    writev (fd, iov, ArraySize(iov));
    ftruncate (fd, sizeof(header)+scoresSize);
    close (fd);
}
