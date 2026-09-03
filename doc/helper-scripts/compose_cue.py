#!/usr/bin/env python3
"""
Orchestral cue for the CybICS demo video, about 180 s in D minor at 100 BPM.

Writes a General MIDI file whose sections follow the walkthrough recorded by
record_demo.py: a drone and cymbal swell under the logo, a string ostinato for
the home page, brass and choir joining for CTF and virtual hardware, the horn
motif for OpenPLC, FUXA and IDS, the full ensemble with taiko rolls for the
engineering workstation and attack machine, and a final chord.

Render and master it with FluidSynth and ffmpeg, both in the Ubuntu repos:

    python3 record_demo.py --out demo.mp4 --keep-raw
    python3 compose_cue.py cue.mid --marks demo.marks.json --length <video length>
    fluidsynth -ni -q -r 44100 -g 0.7 -F cue_raw.wav /usr/share/sounds/sf2/FluidR3_GM.sf2 cue.mid
    ffmpeg -i cue_raw.wav -af "acompressor=threshold=-18dB:ratio=3:attack=10:release=200,\
alimiter=limit=0.95,loudnorm=I=-16:TP=-1.5:LRA=11" -t 180 -ar 44100 cue.wav

record_demo.py pads the track to the picture and fades it out with the outro card.
    python3 record_demo.py --music cue.wav

Needs the mido package.
"""
import argparse, json, random
import mido
from mido import Message, MidiFile, MidiTrack, MetaMessage

ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("--marks", help="<video>.marks.json from record_demo.py; aligns the sections to the recording")
ap.add_argument("--intro", type=float, default=2.7, help="seconds the title card adds before the capture")
ap.add_argument("--length", type=float, default=180)
args = ap.parse_args()

random.seed(7)
BPM = 100
TPB = 480                       # ticks per beat
BEAT = TPB
BAR = 4 * BEAT
SEC = BPM / 60 * TPB            # ticks per second
TOTAL_SEC = args.length

mid = MidiFile(ticks_per_beat=TPB)

def track(name, program, channel, volume=100, pan=64, reverb=60):
    t = MidiTrack(); mid.tracks.append(t)
    t.append(MetaMessage("track_name", name=name))
    if channel != 9:
        t.append(Message("program_change", program=program, channel=channel, time=0))
    t.append(Message("control_change", control=7, value=volume, channel=channel, time=0))
    t.append(Message("control_change", control=10, value=pan, channel=channel, time=0))
    t.append(Message("control_change", control=91, value=reverb, channel=channel, time=0))
    t.events = []               # (abs_tick, message)
    t.channel = channel
    return t

def note(t, start, dur, pitch, vel):
    vel = max(1, min(127, int(vel + random.randint(-6, 6))))
    t.events.append((int(start), Message("note_on", note=pitch, velocity=vel, channel=t.channel, time=0)))
    t.events.append((int(start + dur) - 1, Message("note_off", note=pitch, velocity=0, channel=t.channel, time=0)))

def finish():
    tempo = MidiTrack(); mid.tracks.insert(0, tempo)
    tempo.append(MetaMessage("set_tempo", tempo=mido.bpm2tempo(BPM), time=0))
    for t in mid.tracks[1:]:
        t.events.sort(key=lambda e: (e[0], e[1].type == "note_on"))
        last = 0
        for tick, msg in t.events:
            msg.time = tick - last; last = tick
            t.append(msg)

# --- instruments -----------------------------------------------------------
strings_lo = track("cellos/basses", 48, 0, volume=105, pan=54)
strings_hi = track("violins", 48, 1, volume=95, pan=74)
pad        = track("slow strings", 49, 2, volume=80, pan=64, reverb=90)
choir      = track("choir", 52, 3, volume=85, pan=64, reverb=100)
brass      = track("brass", 61, 4, volume=100, pan=60)
horns      = track("french horns", 60, 5, volume=100, pan=68)
bass       = track("synth bass", 38, 6, volume=95, pan=64, reverb=20)
timpani    = track("timpani", 47, 7, volume=110, pan=50)
taiko      = track("taiko", 116, 8, volume=115, pan=64, reverb=70)
drums      = track("drums", 0, 9, volume=110, pan=64, reverb=50)

# --- harmony ----------------------------------------------------------------
D, E, F, G, A, Bb, C = 50, 52, 53, 55, 57, 58, 60      # D3 = 50
CH = {"Dm": [D, F, A], "Bb": [Bb-12, D, F], "F": [F-12, A-12, C-12+12], "C": [C-12, E, G],
      "Gm": [G-12, Bb-12, D], "A": [A-12, C+1-12, E]}
prog_a = ["Dm", "Bb", "F", "C"]
prog_b = ["Dm", "Bb", "Gm", "A"]

def sec(s): return s * SEC

# Section boundaries in seconds. Defaults match a typical recording; with
# --marks they come from the recording itself.
T_LOGO, T_HOME, T_CTF, T_PLC, T_ENG, T_END = 0, 3.5, 35, 70, 120, 165
if args.marks:
    at = {title: t + args.intro for t, title, _ in json.load(open(args.marks)) if title}
    T_CTF, T_PLC, T_ENG = at["CTF training"], at["OpenPLC"], at["Engineering workstation"]
    T_END = at["Attack machine"] + 5

# --- 0. logo: drone, cymbal swell, timpani hit at the cut ------------------
note(pad, 0, sec(4), D-12, 60); note(pad, 0, sec(4), A-12, 55)
note(strings_lo, 0, sec(3.6), D-24, 70)
for i in range(14):                                     # swelling suspended cymbal
    drums.events.append((int(sec(0.2 + i*0.22)), Message("note_on", note=49, velocity=20 + i*6, channel=9, time=0)))
note(timpani, sec(3.3), sec(1.5), D-24, 120); note(timpani, sec(3.3), sec(1.5), D-12, 110)
drums.events.append((int(sec(3.3)), Message("note_on", note=49, velocity=120, channel=9, time=0)))

# --- bar grid from the cut ----------------------------------------------------
start = sec(T_HOME)
bars = int((sec(T_END) - start) // BAR)

for b in range(bars):
    t0 = start + b * BAR
    t_sec = t0 / SEC
    intense = t_sec >= T_ENG
    full = t_sec >= T_PLC
    build = t_sec >= T_CTF
    prog = prog_b if intense else prog_a
    chord = CH[prog[b % 4]]
    root = chord[0]

    # low strings: eighth-note ostinato on the root, tension note every 4th bar
    for i in range(8):
        p = root - 12 if i % 2 == 0 else root
        if b % 4 == 3 and i >= 6: p = root - 12 + 1
        note(strings_lo, t0 + i * BEAT/2, BEAT/2, p, 78 + (18 if build else 0) + (10 if intense else 0))

    # pad + choir: chord held
    for p in chord:
        note(pad, t0, BAR, p + 12, 55 + (15 if full else 0))
        if build: note(choir, t0, BAR, p + 12, 45 + (25 if intense else 0))

    # violins: arpeggio in 16ths once the build starts, sustained line before
    if build:
        arp = [chord[0]+24, chord[1]+24, chord[2]+24, chord[1]+24]
        for i in range(16):
            note(strings_hi, t0 + i*BEAT/4, BEAT/4, arp[i % 4] + (12 if intense and i % 8 >= 4 else 0), 70 + (20 if intense else 0))
    else:
        note(strings_hi, t0, BAR, chord[2] + 12, 60)

    # bass: root on 1 and 3, octave on the & of 4
    note(bass, t0, BEAT, root - 24, 95); note(bass, t0 + 2*BEAT, BEAT, root - 24, 90)
    note(bass, t0 + 3.5*BEAT, BEAT/2, root - 12, 85)

    # horns: motif from the full section (long-short-short-long, up a fourth)
    if full:
        m = [(0, 1.5, chord[0]+12), (1.5, 0.5, chord[1]+12), (2, 0.5, chord[2]+12), (2.5, 1.5, chord[0]+17)]
        for off, dur, p in m:
            note(horns, t0 + off*BEAT, dur*BEAT, p, 95 + (20 if intense else 0))
    # brass stabs on 1 and the & of 2 during the build and later
    if build:
        for off in (0, 1.5):
            for p in chord: note(brass, t0 + off*BEAT, BEAT/2, p, 85 + (25 if intense else 0))
        if intense:
            for p in chord: note(brass, t0 + 3*BEAT, BEAT, p + 12, 105)

    # percussion
    tk = 100 + (20 if intense else 0)
    note(taiko, t0, BEAT, 36, tk); note(taiko, t0 + 2*BEAT, BEAT, 36, tk - 10)
    if build: note(taiko, t0 + 1.5*BEAT, BEAT/2, 38, tk - 20); note(taiko, t0 + 3.5*BEAT, BEAT/2, 38, tk - 15)
    if intense:
        for i in range(4): note(taiko, t0 + 3*BEAT + i*BEAT/4, BEAT/4, 36, 80 + i*10)   # roll into the next bar
    note(timpani, t0, BEAT, root - 24, 90 + (20 if full else 0))
    if b % 4 == 3: note(timpani, t0 + 3*BEAT, BEAT, root - 24 + 7, 100)
    if full:
        drums.events.append((int(t0 + 2*BEAT), Message("note_on", note=38, velocity=90, channel=9, time=0)))
        if b % 8 == 0: drums.events.append((int(t0), Message("note_on", note=49, velocity=100, channel=9, time=0)))
    if intense and b % 2 == 0:
        drums.events.append((int(t0), Message("note_on", note=57, velocity=110, channel=9, time=0)))

# --- ending: final chord, timpani roll, crash, decay ------------------------
t_end = start + bars * BAR
for p in CH["Dm"]:
    note(brass, t_end, sec(3), p + 12, 115); note(horns, t_end, sec(4), p, 110)
    note(pad, t_end, sec(14), p, 90); note(choir, t_end, sec(14), p + 12, 90); note(strings_hi, t_end, sec(10), p + 24, 100)
note(strings_lo, t_end, sec(14), D-24, 110); note(bass, t_end, sec(5), D-36, 110)
for i in range(16): note(timpani, t_end - BEAT + i*BEAT/8, BEAT/8, D-24, 70 + i*3)
note(timpani, t_end, sec(3), D-24, 127)
drums.events.append((int(t_end), Message("note_on", note=49, velocity=127, channel=9, time=0)))
drums.events.append((int(t_end + sec(2)), Message("note_on", note=52, velocity=90, channel=9, time=0)))

finish()
mid.save(args.out)
print(f"bars={bars} end at {t_end/SEC:.1f}s, length {mid.length:.1f}s")
