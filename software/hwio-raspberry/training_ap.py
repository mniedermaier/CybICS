"""The channel of the board's training access point (the profile 'cybics').

A classroom full of boards puts one training network per board on 2.4 GHz,
a few metres apart, next to the CybICS-mgmt access point the boards' USB
dongles join. Left to NetworkManager, the training networks landed on 1, 6
and 11 alike, so cybics-mgmt (channel 6 by default) shared its channel with
some of them and overlapped none less. The boards therefore stay on 1 and 11,
split by their STM32 UID, and leave 6 to cybics-mgmt. Both channels are
allowed in every regulatory domain.
"""
import zlib

CHANNELS = ('1', '11')


def channel_for(uid):
    """1 or 11 for a board UID, about half the boards each.

    A CRC rather than the last hex digit: the UIDs of one production batch
    share their tail.
    """
    return CHANNELS[zlib.crc32(uid.encode('ascii', 'replace')) % len(CHANNELS)]
