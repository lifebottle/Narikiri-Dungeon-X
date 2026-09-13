# LZX decompressor in pure python, logic extracted from
# Narikiri Dungeon's code, later determined to be a
# modified version of Cabextract's code hardcoded to 32K
# window size and with a global state, so most of this
# code is basically Cabextract's lzxd.c

# Return codes
DECR_OK = 0
DECR_DATAFORMAT = 1
DECR_ILLEGALDATA = 2
DECR_NOMEMORY = 3

# LZX specification constants
LZX_MIN_MATCH = 2
LZX_MAX_MATCH = 257
LZX_NUM_CHARS = 256
LZX_BLOCKTYPE_INVALID = 0
LZX_BLOCKTYPE_VERBATIM = 1
LZX_BLOCKTYPE_ALIGNED = 2
LZX_BLOCKTYPE_UNCOMPRESSED = 3
LZX_PRETREE_NUM_ELEMENTS = 20
LZX_ALIGNED_NUM_ELEMENTS = 8
LZX_NUM_PRIMARY_LENGTHS = 7
LZX_NUM_SECONDARY_LENGTHS = 249

# Huffman table parameters
LZX_PRETREE_MAXSYMBOLS = LZX_PRETREE_NUM_ELEMENTS
LZX_PRETREE_TABLEBITS = 6
LZX_MAINTREE_MAXSYMBOLS = LZX_NUM_CHARS + 50 * 8  # 656
LZX_MAINTREE_TABLEBITS = 12
LZX_LENGTH_MAXSYMBOLS = LZX_NUM_SECONDARY_LENGTHS + 1  # 250
LZX_LENGTH_TABLEBITS = 12
LZX_ALIGNED_MAXSYMBOLS = LZX_ALIGNED_NUM_ELEMENTS
LZX_ALIGNED_TABLEBITS = 7

LZX_LENTABLE_SAFETY = 64

# Bit buffer width (simulate 32-bit unsigned)
ULONG_BITS = 32


class LZXError(Exception):
    """Raised when LZX decompression encounters invalid data."""

    pass


class _BitBuffer:
    """Bitstream reader operating over a bytes/memoryview buffer.

    Implements the lzxd.c macros: INIT_BITSTREAM, ENSURE_BITS,
    PEEK_BITS, REMOVE_BITS, READ_BITS with a Python int as the buffer
    (masked to 32 bits on every write) so arithmetic matches the C unsigned.
    """

    __slots__ = ("data", "pos", "bitbuf", "bitsleft")

    def __init__(self, data: bytes | bytearray | memoryview):
        self.data = data
        self.pos = 0
        self.bitbuf = 0
        self.bitsleft = 0

    def reset(self):
        self.bitbuf = 0
        self.bitsleft = 0

    def ensure_bits(self, n: int):
        while self.bitsleft < n:
            if self.pos + 1 < len(self.data):
                lo = self.data[self.pos]
                hi = self.data[self.pos + 1]
            elif self.pos < len(self.data):
                lo = self.data[self.pos]
                hi = 0
            else:
                lo = hi = 0
            self.pos += 2
            self.bitbuf |= ((hi << 8) | lo) << (ULONG_BITS - 16 - self.bitsleft)
            self.bitbuf &= 0xFFFFFFFF
            self.bitsleft += 16

    def peek_bits(self, n: int) -> int:
        return (self.bitbuf >> (ULONG_BITS - n)) & 0xFFFFFFFF

    def remove_bits(self, n: int):
        self.bitbuf = (self.bitbuf << n) & 0xFFFFFFFF
        self.bitsleft -= n

    def read_bits(self, n: int) -> int:
        if n == 0:
            return 0
        self.ensure_bits(n)
        val = self.peek_bits(n)
        self.remove_bits(n)
        return val

    def rewind(self, nbytes: int):
        """Move the byte position backwards (used for uncompressed block alignment)."""
        self.pos -= nbytes


# NDX function at 0x088d9374
def _make_decode_table(
    nsyms: int, nbits: int, length: list[int], table: list[int]
) -> bool:
    """Build a fast Huffman decoding table from canonical code lengths.
    Returns True on success, False on error.
    """
    bit_num = 1
    pos = 0
    table_mask = 1 << nbits
    bit_mask = table_mask >> 1  # skip 0-length codes
    next_symbol = bit_mask  # base of allocation for long codes

    # Fill entries for codes short enough for a direct mapping
    while bit_num <= nbits:
        for sym in range(nsyms):
            if length[sym] == bit_num:
                leaf = pos
                pos += bit_mask
                if pos > table_mask:
                    return False  # table overrun
                for fill in range(bit_mask):
                    table[leaf + fill] = sym
        bit_mask >>= 1
        bit_num += 1

    # If there are codes longer than nbits
    if pos != table_mask:
        # Clear the remainder of the table
        for i in range(pos, table_mask):
            table[i] = 0

        # Give room for codes to grow by up to 16 more bits
        pos <<= 16
        table_mask <<= 16
        bit_mask = 1 << 15

        while bit_num <= 16:
            for sym in range(nsyms):
                if length[sym] == bit_num:
                    leaf = pos >> 16
                    for fill in range(bit_num - nbits):
                        # If this path hasn't been taken yet, allocate two entries
                        if table[leaf] == 0:
                            table[next_symbol << 1] = 0
                            table[(next_symbol << 1) + 1] = 0
                            table[leaf] = next_symbol
                            next_symbol += 1
                        # Follow the path and select left or right
                        leaf = table[leaf] << 1
                        if (pos >> (15 - fill)) & 1:
                            leaf += 1
                    table[leaf] = sym
                    pos += bit_mask
                    if pos > table_mask:
                        return False  # table overflow
            bit_mask >>= 1
            bit_num += 1

    # Full table?
    if pos == table_mask:
        return True

    # Either erroneous table, or all elements are 0
    return all(not length[sym] for sym in range(nsyms))


def _read_huffsym(
    table: list[int], length: list[int], nsyms: int, nbits: int, bb: _BitBuffer
) -> int:  # noqa: E501
    """Decode one Huffman symbol from the bitstream.
    It's the READ_HUFFSYM C macro.
    """
    bb.ensure_bits(16)
    i = table[bb.peek_bits(nbits)]
    if i >= nsyms:
        j = 1 << (ULONG_BITS - nbits)
        while True:
            j >>= 1
            i <<= 1
            i |= 1 if (bb.bitbuf & j) else 0
            if j == 0:
                raise LZXError("Huffman symbol decode overflow")
            i = table[i]
            if i < nsyms:
                break
    bits_consumed = length[i]
    bb.remove_bits(bits_consumed)
    return i


class LZXDecompressor:
    """Pure-Python LZX decompressor.

    Usage::

        dec = LZXDecompressor()   # window size assumed 32K
        for block in cfdata_blocks:
            out = dec.decompress(block.compressed, block.uncompressed_size)
    """

    # NDX function at 0x088d9218
    def __init__(self):
        # window_size hardcoded to 32K, only size supported by NDX
        window_size = 1 << 15
        window_bits = window_size.bit_length() - 1

        self.window_size = window_size
        self.window = bytearray(window_size)
        self.window_posn = 0

        # LRU repeated offset queue
        self.R0 = 1
        self.R1 = 1
        self.R2 = 1

        # Compute position slots
        if window_bits == 20:
            posn_slots = 42
        elif window_bits == 21:
            posn_slots = 50
        else:
            posn_slots = window_bits << 1

        self.main_elements = LZX_NUM_CHARS + (posn_slots << 3)

        # Build extra_bits and position_base tables
        self.extra_bits = [0] * 51
        eb = 0
        for i in range(0, 51, 2):
            self.extra_bits[i] = eb
            if i + 1 < 51:
                self.extra_bits[i + 1] = eb
            if i != 0 and eb < 17:
                eb += 1

        self.position_base = [0] * 51
        pb = 0
        for i in range(51):
            self.position_base[i] = pb
            pb += 1 << self.extra_bits[i]

        # Header / block state
        self.header_read = False
        self.block_type = LZX_BLOCKTYPE_INVALID
        self.block_length = 0
        self.block_remaining = 0
        self.frames_read = 0
        self.intel_filesize = 0
        self.intel_curpos = 0
        self.intel_started = False

        # Huffman tables
        self.PRETREE_table = [0] * (
            (1 << LZX_PRETREE_TABLEBITS) + (LZX_PRETREE_MAXSYMBOLS << 1)
        )
        self.PRETREE_len = [0] * (LZX_PRETREE_MAXSYMBOLS + LZX_LENTABLE_SAFETY)

        self.MAINTREE_table = [0] * (
            (1 << LZX_MAINTREE_TABLEBITS) + (LZX_MAINTREE_MAXSYMBOLS << 1)
        )
        self.MAINTREE_len = [0] * (LZX_MAINTREE_MAXSYMBOLS + LZX_LENTABLE_SAFETY)

        self.LENGTH_table = [0] * (
            (1 << LZX_LENGTH_TABLEBITS) + (LZX_LENGTH_MAXSYMBOLS << 1)
        )
        self.LENGTH_len = [0] * (LZX_LENGTH_MAXSYMBOLS + LZX_LENTABLE_SAFETY)

        self.ALIGNED_table = [0] * (
            (1 << LZX_ALIGNED_TABLEBITS) + (LZX_ALIGNED_MAXSYMBOLS << 1)
        )
        self.ALIGNED_len = [0] * (LZX_ALIGNED_MAXSYMBOLS + LZX_LENTABLE_SAFETY)

    # Internal Huffman helpers, adapted lzxd.c C macros
    def _read_huffsym_PRETREE(self, bb: _BitBuffer) -> int:
        return _read_huffsym(
            self.PRETREE_table,
            self.PRETREE_len,
            LZX_PRETREE_MAXSYMBOLS,
            LZX_PRETREE_TABLEBITS,
            bb,
        )

    def _read_huffsym_MAINTREE(self, bb: _BitBuffer) -> int:
        return _read_huffsym(
            self.MAINTREE_table,
            self.MAINTREE_len,
            LZX_MAINTREE_MAXSYMBOLS,
            LZX_MAINTREE_TABLEBITS,
            bb,
        )

    def _read_huffsym_LENGTH(self, bb: _BitBuffer) -> int:
        return _read_huffsym(
            self.LENGTH_table,
            self.LENGTH_len,
            LZX_LENGTH_MAXSYMBOLS,
            LZX_LENGTH_TABLEBITS,
            bb,
        )

    def _read_huffsym_ALIGNED(self, bb: _BitBuffer) -> int:
        return _read_huffsym(
            self.ALIGNED_table,
            self.ALIGNED_len,
            LZX_ALIGNED_MAXSYMBOLS,
            LZX_ALIGNED_TABLEBITS,
            bb,
        )

    def _build_table_PRETREE(self):
        if not _make_decode_table(
            LZX_PRETREE_MAXSYMBOLS,
            LZX_PRETREE_TABLEBITS,
            self.PRETREE_len,
            self.PRETREE_table,
        ):
            raise LZXError("Failed to build PRETREE decode table")

    def _build_table_MAINTREE(self):
        if not _make_decode_table(
            LZX_MAINTREE_MAXSYMBOLS,
            LZX_MAINTREE_TABLEBITS,
            self.MAINTREE_len,
            self.MAINTREE_table,
        ):
            raise LZXError("Failed to build MAINTREE decode table")

    def _build_table_LENGTH(self):
        if not _make_decode_table(
            LZX_LENGTH_MAXSYMBOLS,
            LZX_LENGTH_TABLEBITS,
            self.LENGTH_len,
            self.LENGTH_table,
        ):
            raise LZXError("Failed to build LENGTH decode table")

    def _build_table_ALIGNED(self):
        if not _make_decode_table(
            LZX_ALIGNED_MAXSYMBOLS,
            LZX_ALIGNED_TABLEBITS,
            self.ALIGNED_len,
            self.ALIGNED_table,
        ):
            raise LZXError("Failed to build ALIGNED decode table")

    # NDX function at 0x088d98b0
    def _read_lengths(self, lens: list[int], first: int, last: int, bb: _BitBuffer):
        """Read code lengths via pretree.  Ported from lzx_read_lens()."""
        # Read pretree code lengths (20 entries, 4 bits each)
        for x in range(20):
            self.PRETREE_len[x] = bb.read_bits(4)
        self._build_table_PRETREE()

        x = first
        while x < last:
            z = self._read_huffsym_PRETREE(bb)
            if z == 17:
                y = bb.read_bits(4) + 4
                while y > 0:
                    lens[x] = 0
                    x += 1
                    y -= 1
            elif z == 18:
                y = bb.read_bits(5) + 20
                while y > 0:
                    lens[x] = 0
                    x += 1
                    y -= 1
            elif z == 19:
                y = bb.read_bits(1) + 4
                z = self._read_huffsym_PRETREE(bb)
                z = lens[x] - z
                if z < 0:
                    z += 17
                while y > 0:
                    lens[x] = z
                    x += 1
                    y -= 1
            else:
                z = lens[x] - z
                if z < 0:
                    z += 17
                lens[x] = z
                x += 1

    # Public
    # NDX function at 0x088d9d6c
    def decompress(self, compressed_data: bytes | bytearray, out_len: int) -> bytes:
        """Decompress one CFDATA block.

        Parameters
        ----------
        compressed_data : bytes
            Raw compressed payload from the CFDATA block.
        out_len : int
            Expected uncompressed size for this block.

        Returns
        -------
        bytes
            Decompressed data of length *out_len*.
        """
        bb = _BitBuffer(compressed_data)
        endinp = len(compressed_data)

        window = self.window
        window_posn = self.window_posn
        window_size = self.window_size
        R0 = self.R0
        R1 = self.R1
        R2 = self.R2

        togo = out_len

        # Read header if necessary
        if not self.header_read:
            k = bb.read_bits(1)
            if k:
                i = bb.read_bits(16)
                j = bb.read_bits(16)
                self.intel_filesize = (i << 16) | j
            else:
                self.intel_filesize = 0
            self.header_read = True

        # Main decoding loop
        while togo > 0:
            # Last block finished, new block expected
            if self.block_remaining == 0:
                if self.block_type == LZX_BLOCKTYPE_UNCOMPRESSED:
                    if self.block_length & 1:
                        bb.pos += 1  # realign bitstream to word
                    bb.reset()

                self.block_type = bb.read_bits(3)
                i = bb.read_bits(16)
                j = bb.read_bits(8)
                self.block_remaining = (i << 8) | j
                self.block_length = self.block_remaining

                if self.block_type == LZX_BLOCKTYPE_ALIGNED:
                    for idx in range(8):
                        self.ALIGNED_len[idx] = bb.read_bits(3)
                    self._build_table_ALIGNED()
                    # fall through to verbatim tree reading

                if (
                    self.block_type == LZX_BLOCKTYPE_ALIGNED
                    or self.block_type == LZX_BLOCKTYPE_VERBATIM
                ):
                    self._read_lengths(self.MAINTREE_len, 0, 256, bb)
                    self._read_lengths(self.MAINTREE_len, 256, self.main_elements, bb)
                    self._build_table_MAINTREE()
                    if self.MAINTREE_len[0xE8] != 0:
                        self.intel_started = True

                    self._read_lengths(
                        self.LENGTH_len, 0, LZX_NUM_SECONDARY_LENGTHS, bb
                    )
                    self._build_table_LENGTH()

                elif self.block_type == LZX_BLOCKTYPE_UNCOMPRESSED:
                    self.intel_started = True
                    bb.ensure_bits(16)
                    if bb.bitsleft > 16:
                        bb.rewind(2)
                    # Read R0, R1, R2 as little-endian 32-bit from the byte stream
                    p = bb.pos
                    d = bb.data
                    R0 = d[p] | (d[p + 1] << 8) | (d[p + 2] << 16) | (d[p + 3] << 24)
                    p += 4
                    R1 = d[p] | (d[p + 1] << 8) | (d[p + 2] << 16) | (d[p + 3] << 24)
                    p += 4
                    R2 = d[p] | (d[p + 1] << 8) | (d[p + 2] << 16) | (d[p + 3] << 24)
                    p += 4
                    bb.pos = p
                    bb.reset()
                else:
                    raise LZXError(f"Invalid block type {self.block_type}")

            # Buffer exhaustion check
            if bb.pos > endinp and (bb.pos > endinp + 2 or bb.bitsleft < 16):
                raise LZXError("Input buffer exhausted")

            while self.block_remaining > 0 and togo > 0:
                this_run = self.block_remaining
                if this_run > togo:
                    this_run = togo
                togo -= this_run
                self.block_remaining -= this_run

                # Apply 2^x - 1 mask
                window_posn &= window_size - 1
                # Runs can't straddle the window wraparound
                if window_posn + this_run > window_size:
                    raise LZXError("Run straddles window wraparound")

                if self.block_type == LZX_BLOCKTYPE_VERBATIM:
                    while this_run > 0:
                        main_element = self._read_huffsym_MAINTREE(bb)

                        if main_element < LZX_NUM_CHARS:
                            # Literal byte
                            window[window_posn] = main_element
                            window_posn += 1
                            this_run -= 1
                        else:
                            # Match
                            main_element -= LZX_NUM_CHARS
                            match_length = main_element & LZX_NUM_PRIMARY_LENGTHS
                            if match_length == LZX_NUM_PRIMARY_LENGTHS:
                                length_footer = self._read_huffsym_LENGTH(bb)
                                match_length += length_footer
                            match_length += LZX_MIN_MATCH

                            match_offset = main_element >> 3

                            if match_offset > 2:
                                # Not a repeated offset
                                if match_offset != 3:
                                    extra = self.extra_bits[match_offset]
                                    verbatim_bits = bb.read_bits(extra)
                                    match_offset = (
                                        self.position_base[match_offset]
                                        - 2
                                        + verbatim_bits
                                    )
                                else:
                                    match_offset = 1

                                # Update LRU queue
                                R2 = R1
                                R1 = R0
                                R0 = match_offset
                            elif match_offset == 0:
                                match_offset = R0
                            elif match_offset == 1:
                                match_offset = R1
                                R1 = R0
                                R0 = match_offset
                            else:  # match_offset == 2
                                match_offset = R2
                                R2 = R0
                                R0 = match_offset

                            rundest = window_posn
                            runsrc = rundest - match_offset
                            window_posn += match_length
                            if window_posn > window_size:
                                raise LZXError("Match exceeds window")
                            this_run -= match_length

                            # Copy wrapped source data
                            while runsrc < 0 and match_length > 0:
                                window[rundest] = window[runsrc + window_size]
                                rundest += 1
                                runsrc += 1
                                match_length -= 1
                            # Copy match data
                            while match_length > 0:
                                window[rundest] = window[runsrc]
                                rundest += 1
                                runsrc += 1
                                match_length -= 1

                elif self.block_type == LZX_BLOCKTYPE_ALIGNED:
                    while this_run > 0:
                        main_element = self._read_huffsym_MAINTREE(bb)

                        if main_element < LZX_NUM_CHARS:
                            # Literal byte
                            window[window_posn] = main_element
                            window_posn += 1
                            this_run -= 1
                        else:
                            # Match
                            main_element -= LZX_NUM_CHARS
                            match_length = main_element & LZX_NUM_PRIMARY_LENGTHS
                            if match_length == LZX_NUM_PRIMARY_LENGTHS:
                                length_footer = self._read_huffsym_LENGTH(bb)
                                match_length += length_footer
                            match_length += LZX_MIN_MATCH

                            match_offset = main_element >> 3

                            if match_offset > 2:
                                extra = self.extra_bits[match_offset]
                                match_offset = self.position_base[match_offset] - 2
                                if extra > 3:
                                    # Verbatim and aligned bits
                                    extra -= 3
                                    verbatim_bits = bb.read_bits(extra)
                                    match_offset += verbatim_bits << 3
                                    aligned_bits = self._read_huffsym_ALIGNED(bb)
                                    match_offset += aligned_bits
                                elif extra == 3:
                                    # Aligned bits only
                                    aligned_bits = self._read_huffsym_ALIGNED(bb)
                                    match_offset += aligned_bits
                                elif extra > 0:
                                    # Verbatim bits only (extra == 1 or 2)
                                    verbatim_bits = bb.read_bits(extra)
                                    match_offset += verbatim_bits
                                else:
                                    # extra == 0
                                    match_offset = 1

                                # Update LRU queue
                                R2 = R1
                                R1 = R0
                                R0 = match_offset
                            elif match_offset == 0:
                                match_offset = R0
                            elif match_offset == 1:
                                match_offset = R1
                                R1 = R0
                                R0 = match_offset
                            else:  # match_offset == 2
                                match_offset = R2
                                R2 = R0
                                R0 = match_offset

                            rundest = window_posn
                            runsrc = rundest - match_offset
                            window_posn += match_length
                            if window_posn > window_size:
                                raise LZXError("Match exceeds window")
                            this_run -= match_length

                            # Copy wrapped source data
                            while runsrc < 0 and match_length > 0:
                                window[rundest] = window[runsrc + window_size]
                                rundest += 1
                                runsrc += 1
                                match_length -= 1
                            # Copy match data
                            while match_length > 0:
                                window[rundest] = window[runsrc]
                                rundest += 1
                                runsrc += 1
                                match_length -= 1

                elif self.block_type == LZX_BLOCKTYPE_UNCOMPRESSED:
                    if bb.pos + this_run > endinp:
                        raise LZXError("Uncompressed block overflows input")
                    window[window_posn : window_posn + this_run] = bb.data[
                        bb.pos : bb.pos + this_run
                    ]
                    bb.pos += this_run
                    window_posn += this_run

                else:
                    raise LZXError(f"Invalid block type {self.block_type}")

        if togo != 0:
            raise LZXError("Decompression did not produce expected output length")

        # Copy output from window
        start = window_size - out_len if window_posn == 0 else window_posn - out_len
        outbuf = bytearray(window[start : start + out_len])

        # Save state
        self.window_posn = window_posn
        self.R0 = R0
        self.R1 = R1
        self.R2 = R2

        # Intel E8 decoding
        self.frames_read += 1
        if self.frames_read < 32768 and self.intel_filesize != 0:
            if out_len <= 6 or not self.intel_started:
                self.intel_curpos += out_len
            else:
                curpos = self.intel_curpos
                filesize = self.intel_filesize
                self.intel_curpos = curpos + out_len

                i = 0
                end = out_len - 10
                while i < end:
                    if outbuf[i] != 0xE8:
                        i += 1
                        curpos += 1
                        continue
                    i += 1
                    abs_off = (
                        outbuf[i]
                        | (outbuf[i + 1] << 8)
                        | (outbuf[i + 2] << 16)
                        | (outbuf[i + 3] << 24)
                    )
                    # Sign-extend to 32-bit signed
                    if abs_off & 0x80000000:
                        abs_off -= 0x100000000

                    if abs_off >= -curpos and abs_off < filesize:
                        if abs_off >= 0:
                            rel_off = abs_off - curpos
                        else:
                            rel_off = abs_off + filesize
                        # Write back as unsigned little-endian
                        rel_off &= 0xFFFFFFFF
                        outbuf[i] = rel_off & 0xFF
                        outbuf[i + 1] = (rel_off >> 8) & 0xFF
                        outbuf[i + 2] = (rel_off >> 16) & 0xFF
                        outbuf[i + 3] = (rel_off >> 24) & 0xFF

                    i += 4
                    curpos += 5

        return bytes(outbuf)
