"""Guitar Pro (GP3/GP4/GP5) → internal Song importer (via PyGuitarPro)."""

from __future__ import annotations

import logging
from pathlib import Path

import guitarpro

from fretflow.core.errors import ImportError as FretFlowImportError
from fretflow.core.models import Measure, Note, Song, Technique, Track

logger = logging.getLogger("fretflow.importers.guitarpro")


def _map_technique(gp_note: guitarpro.Note) -> Technique:
    """Map the first recognized Guitar Pro effect to our Technique enum."""
    effect = gp_note.effect
    if effect is None:
        return Technique.NONE
    if effect.bend is not None:
        return Technique.BEND
    if effect.slides:
        return Technique.SLIDE
    if effect.hammer:
        return Technique.HAMMER_ON
    if effect.vibrato:
        return Technique.VIBRATO
    if effect.palmMute:
        return Technique.PALM_MUTE
    if effect.harmonic is not None:
        return Technique.HARMONIC
    return Technique.NONE


def _beat_duration_seconds(beat: guitarpro.Beat, tempo_bpm: float) -> float:
    """Duration of a beat in seconds given current tempo."""
    # Duration.value is the denominator (1=whole, 2=half, 4=quarter, …)
    # Duration.dotted, tuplet also affect length
    base = 4.0 / beat.duration.value  # in quarter-note units
    if beat.duration.isDotted:
        base *= 1.5
    tuplet = beat.duration.tuplet
    if tuplet is not None and tuplet.times > 0:
        base *= tuplet.enters / tuplet.times
    return base * (60.0 / tempo_bpm)


class GuitarProImporter:
    """Import GP3, GP4, GP5 files into the domain Song model."""

    def can_import(self, path: Path) -> bool:
        return path.suffix.lower() in {".gp3", ".gp4", ".gp5", ".gpx"}

    def import_song(self, path: Path) -> Song:
        path = Path(path)
        if not path.is_file():
            raise FretFlowImportError(f"Guitar Pro file not found: {path}")

        try:
            gp_song = guitarpro.parse(str(path))
        except Exception as exc:
            raise FretFlowImportError(
                f"Cannot parse Guitar Pro file {path}: {exc}"
            ) from exc

        tempo_bpm = float(gp_song.tempo) if gp_song.tempo else 120.0
        title = gp_song.title or path.stem
        artist = gp_song.artist or ""

        tracks: list[Track] = []
        max_end = 0.0

        for gp_track in gp_song.tracks:
            tuning = tuple(
                s.number for s in (gp_track.strings or [])
            ) or (64, 59, 55, 50, 45, 40)

            # PyGuitarPro stores open-string MIDI pitches in string.value
            if gp_track.strings:
                tuning = tuple(s.value for s in gp_track.strings)

            is_guitar = not gp_track.isPercussionTrack and not gp_track.isBanjoTrack

            domain_measures: list[Measure] = []
            measure_start = 0.0

            for mi, gp_measure in enumerate(gp_track.measures):
                header = gp_measure.header
                numerator = header.timeSignature.numerator
                denominator = header.timeSignature.denominator.value

                # Measure tempo override if present
                measure_tempo = tempo_bpm
                # Duration of this measure in seconds
                # Approximate: sum beat durations of first voice
                measure_notes: list[Note] = []
                beat_time = measure_start

                for voice in gp_measure.voices:
                    voice_time = measure_start
                    for beat in voice.beats:
                        dur = _beat_duration_seconds(beat, measure_tempo)
                        if beat.status == guitarpro.BeatStatus.normal:
                            for gp_note in beat.notes:
                                if gp_note.type == guitarpro.NoteType.rest:
                                    continue
                                # Real pitch: open string + fret
                                string_idx = gp_note.string - 1  # 1-based in GP
                                if 0 <= string_idx < len(tuning):
                                    midi_pitch = tuning[string_idx] + gp_note.value
                                else:
                                    midi_pitch = max(0, min(127, gp_note.value + 40))

                                measure_notes.append(
                                    Note(
                                        start_seconds=voice_time,
                                        duration_seconds=dur,
                                        midi_pitch=midi_pitch,
                                        string=gp_note.string,
                                        fret=gp_note.value,
                                        technique=_map_technique(gp_note),
                                        velocity=gp_note.velocity or 80,
                                    )
                                )
                        voice_time += dur
                    beat_time = max(beat_time, voice_time)

                measure_duration = beat_time - measure_start
                if measure_duration <= 0:
                    # Fallback: 4 quarter notes
                    measure_duration = 4.0 * (60.0 / measure_tempo)

                domain_measures.append(
                    Measure(
                        index=mi,
                        start_seconds=measure_start,
                        duration_seconds=measure_duration,
                        numerator=numerator,
                        denominator=denominator,
                        notes=measure_notes,
                    )
                )
                measure_start += measure_duration

            track_end = measure_start
            max_end = max(max_end, track_end)

            tracks.append(
                Track(
                    name=gp_track.name or f"Track {gp_track.number}",
                    midi_channel=getattr(gp_track, "channel", None)
                    and getattr(gp_track.channel, "channel", 0)
                    or 0,
                    measures=domain_measures,
                    is_guitar=is_guitar,
                    tuning=tuning if isinstance(tuning, tuple) else tuple(tuning),
                )
            )

        # Time signature from first measure header if available
        time_sig = "4/4"
        if gp_song.measureHeaders:
            ts = gp_song.measureHeaders[0].timeSignature
            time_sig = f"{ts.numerator}/{ts.denominator.value}"

        song = Song(
            title=title,
            artist=artist,
            tempo_bpm=tempo_bpm,
            tracks=tracks,
            source_path=path.resolve(),
            duration_seconds=max_end,
            time_signature=time_sig,
        )
        logger.info(
            "Imported GP %s: %d tracks, %.1fs, %.0f BPM",
            path.name,
            len(tracks),
            max_end,
            tempo_bpm,
        )
        return song
