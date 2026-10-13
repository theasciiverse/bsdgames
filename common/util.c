// Copyright (c) 2016 by Mike Sharov <msharov@users.sourceforge.net>
// This file is free software, distributed under the BSD license.

#include "../config.h"
#include <sys/stat.h>
#include <paths.h>

// The standard bsd checksum, summing with right rotation
uint16_t bsdsum (const void* v, size_t n, uint16_t sum)
{
    const uint8_t* s = (const uint8_t*) v;
    for (; n--; ++s) {
	sum = ror16 (sum, 1);
	sum += *s;
    }
    return sum;
}

// Randomly initializes the random number generator
void srandrand (void)
{
    struct timespec now;
    clock_gettime (CLOCK_REALTIME, &now);
    uint32_t seed = now.tv_sec;
    seed ^= getppid();
    seed = ror32 (seed, 16);
    seed ^= getpid();
    seed ^= now.tv_nsec;
    srand (seed);
}

// Generate a random number in given range
unsigned nrand (unsigned r)
{
    return !r ? 0 : rand() % r;
}

// Return current time in milliseconds
uint64_t time_ms (void)
{
    struct timespec now;
    clock_gettime (CLOCK_REALTIME, &now);
    return now.tv_sec*1000 + now.tv_nsec/1000000;
}

// Creates all directories in path
int mkpath (const char* path, mode_t mode)
{
    char pbuf [PATH_MAX], *pbe = pbuf;
    do {
	if (*path == '/' || !*path) {
	    *pbe = '\0';
	    if (pbuf[0] && 0 > mkdir (pbuf, mode) && errno != EEXIST)
		return -1;
	}
	*pbe++ = *path;
	if ((size_t)(pbe - pbuf) >= sizeof(pbuf)-1)
	    return ENAMETOOLONG;
    } while (*path++);
    return 0;
}

// Returns username or something to call the player. Never fails.
// LOGNAME and USER come first, so a player can choose the name the score
// tables show; getlogin reads the login from the system and ignores them.
const char* player_name (void)
{
    const char* un = getenv ("LOGNAME");
    if (!un || !*un)
	un = getenv ("USER");
    if (!un || !*un)
	un = getlogin();
    if (!un)
	un = "player";
    return un;
}

// Creates a saved game dir name from XDG vars
const char* player_saved_game_dir (char* buf, size_t bufsz)
{
    const char* datahome = getenv ("XDG_DATA_HOME");
    if (datahome) {
	snprintf (buf, bufsz, "%s", datahome);
	return buf;
    }
    const char* homedir = getenv ("HOME");
    if (homedir) {
	snprintf (buf, bufsz, "%s/.local/share", homedir);
	return buf;
    }
    datahome = getenv ("TMPDIR");
    if (!datahome)
	datahome = "/tmp";
    snprintf (buf, bufsz, "%s", datahome);
    return buf;
}

// Creates a saved game filename from its file suffix and XDG vars.
const char* player_saved_game_file (char* buf, size_t bufsz, const char* file)
{
    const char* sgdir = player_saved_game_dir (buf, bufsz);
    size_t sgdirlen = strlen (sgdir);
    snprintf (&buf[sgdirlen], bufsz-sgdirlen, "/%s.save", file);
    return buf;
}

void StringBuilder_skip (struct StringBuilder* sb, ssize_t n) {
    if (n < 0) {
	sb->s[0] = 0; // snprintf error - ensure terminator is restored
	return;
    }
    assert (n <= (ssize_t) sb->n && "StringBuilder buffer full");
    if ((size_t) n > sb->n)
	n = sb->n;
    sb->s += n;
    sb->n -= n;
}
