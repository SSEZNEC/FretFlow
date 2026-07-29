"""MIDI → internal Song importer (via Mido)."""

from __future__ import annotations

import logging
from pathlib import Path

import mido

from fretflow.core.errors import ImportError as FretFlowImportError
from fretflow.core.models import Measure, Note, Song, Technique, Track

logger = logging.getLogger("fretflow.importers.midi")

_DEFAULT_TEMPO_BPM = 120.0


def _tempo_to_bpm(tempo_us_per_beat: int) -> float:
    """Convert MIDI tempo (microseconds per quarter note) to BPM."""
    if tempo_us_per_beat <= 0:
        return _DEFAULT_TEMPO_BPM
    return 60_000_000 / tempo_us_per_beat


class MidiImporter:
    """Import Type 0 / Type 1 MIDI files into the domain Song model.

    When iterating a ``mido.MidiFile``, ``msg.time`` is already in **seconds**
    (absolute deltas after tempo conversion). We therefore treat accumulated
    time as seconds directly.
    """

    def can_import(self, path: Path) -> bool:
        return path.suffix.lower() in {".mid", ".midi"}

    def import_song(self, path: Path) -> Song:
        path = Path(path)
        if not path.is_file():
            raise FretFlowImportError(f"MIDI file not found: {path}")

        try:
            mid = mido.MidiFile(str(path))
        except Exception as exc:
            raise FretFlowImportError(f"Cannot parse MIDI {path}: {exc}") from exc

        tempo_bpm = _DEFAULT_TEMPO_BPM
        time_sig = "4/4"
        numerator, denominator = 4, 4

        # (channel, pitch) -> (start_seconds, velocity)
        open_notes: dict[tuple[int, int], tuple[float, int]] = {}
        # (channel, start_s, end_s, pitch, velocity)
        finished: list[tuple[int, float, float, int, int]] = []

        absolute_seconds = 0.0
        title = path.stem
        artist = ""

        for msg in mid:
            # mido yields delta times already converted to seconds
            absolute_seconds += msg.time

            if msg.is_meta:
                if msg.type == "set_tempo":
                    tempo_bpm = _tempo_to_bpm(msg.tempo)
                elif msg.type == "time_signature":
                    numerator = msg.numerator
                    denominator = msg.denominator
                    time_sig = f"{numerator}/{denominator}"
                elif msg.type == "track_name" and msg.name:
                    if not title or title == path.stem:
                        title = msg.name
                elif msg.type == "copyright" and msg.text:
                    artist = msg.text
                continue

            if msg.type == "note_on" and msg.velocity > 0:
                key = (msg.channel, msg.note)
                open_notes[key] = (absolute_seconds, msg.velocity)
            elif msg.type in ("note_off", "note_on"):
                key = (msg.channel, msg.note)
                if key in open_notes:
                    start_s, velocity = open_notes.pop(key)
                    finished.append(
                        (msg.channel, start_s, absolute_seconds, msg.note, velocity)
                    )

        for (channel, pitch), (start_s, velocity) in open_notes.items():
            finished.append((channel, start_s, absolute_seconds, pitch, velocity))

        by_channel: dict[int, list[Note]] = {}
        for channel, start_s, end_s, pitch, velocity in finished:
            if end_s <= start_s:
                end_s = start_s + 0.01
            note = Note(
                start_seconds=start_s,
                duration_seconds=end_s - start_s,
                midi_pitch=pitch,
                velocity=velocity,
                technique=Technique.NONE,
            )
            by_channel.setdefault(channel, []).append(note)

        tracks: list[Track] = []
        for channel, notes in sorted(by_channel.items()):
            notes.sort(key=lambda n: n.start_seconds)
            end = (
                max(n.start_seconds + n.duration_seconds for n in notes)
                if notes
                else 0.0
            )
            measure = Measure(
                index=0,
                start_seconds=0.0,
                duration_seconds=end,
                numerator=numerator,
                denominator=denominator,
                notes=notes,
            )
            tracks.append(
                Track(
                    name=f"Channel {channel}",
                    midi_channel=channel,
                    measures=[measure],
                    is_guitar=True,
                )
            )

        duration = 0.0
        if tracks:
            duration = max(
                (n.start_seconds + n.duration_seconds)
                for t in tracks
                for n in t.notes
            )

        song = Song(
            title=title,
            artist=artist,
            tempo_bpm=tempo_bpm,
            tracks=tracks,
            source_path=path.resolve(),
            duration_seconds=duration,
            time_signature=time_sig,
        )
        logger.info(
            "Imported MIDI %s: %d tracks, %.1fs, %.0f BPM",
            path.name,
            len(tracks),
            duration,
            tempo_bpm,
        )
        return song
