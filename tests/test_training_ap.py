"""The channel of a board's training access point (software/hwio-raspberry/training_ap.py).

Boards stay on 1 and 11 and leave 6 to the CybICS-mgmt access point, split by
their STM32 UID. Needs no Pi and no running stack.
"""
import training_ap  # software/hwio-raspberry, on sys.path via conftest.py

# One production batch, from a classroom: the UIDs share their tail.
BATCH = ['000e51083436', '0029510a3436', '0022510a3436', '0014510a3436', '0018510a3436',
         '001b510a3436', '001f510a3436', '004551083436', '0020510a3436']


def test_boards_leave_channel_6_to_cybics_mgmt():
    assert {training_ap.channel_for(uid) for uid in BATCH} == {'1', '11'}


def test_a_batch_with_a_common_tail_is_split_roughly_in_half():
    on_1 = sum(training_ap.channel_for(uid) == '1' for uid in BATCH)
    assert 3 <= on_1 <= len(BATCH) - 3


def test_a_board_keeps_its_channel():
    assert [training_ap.channel_for(uid) for uid in BATCH] == [training_ap.channel_for(uid) for uid in BATCH]
