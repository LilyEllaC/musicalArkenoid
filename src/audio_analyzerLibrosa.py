import numpy as np
import sounddevice as sd
import librosa
import math


class CircularBuffer:
    def __init__(self, chunkSize, numChunks):
        self.chunkSize = chunkSize
        self.numChunks = numChunks
        self.buffer = np.zeros((numChunks, chunkSize))
        self.index = 0
        self.full = False
    def add_chunk(self, chunk):
        self.buffer[self.index] = chunk
        self.index = (self.index + 1) % self.numChunks
        if self.index == 0:
            self.full = True
    def getFlat(self):
        # will be incorect until buffer is full
        # Buffer is full; the 'oldest' chunk is at the current self.index
        # Use np.roll to move the oldest data to the front, then flatten
        return np.roll(self.buffer, -self.index, axis=0).flatten()
    
class LibrosaAudioAnalyzer:
    def __init__(self):
        # Configuration
        self.RATE = 44100
        self.CHUNK = 1024  # Increased for better CQT resolution
        self.sensitivity = -10 
        
        self.recording = CircularBuffer(self.CHUNK, 10)

        # Define range: C2 to C7 (60 notes / 5 octaves)
        self.fmin = librosa.note_to_hz('C2')
        self.numOctives = 5
        self.n_bins = self.numOctives *12  # 12 notes per octave
        self.minNote = 'C2'
        self.maxNote = 'C7'
        
        # sampling rate limits out highest note to be half the sampling rate (darn you Nyquist) (yes I'm ignoreing band pass stuff)
        self.maxNoteAllowed =librosa.hz_to_note(self.RATE/2.2)
        self.adjustRange('C2', 'C7')
        #self.adjustRange('B4', 'C7')

        self.current_audio = np.zeros(self.CHUNK)
        self.stream = sd.InputStream(
            channels=1, samplerate=self.RATE, 
            blocksize=self.CHUNK, callback=self._audio_callback
        )
        self.stream.start()


    def adjustRange(self, minNote, maxNote):
        """
        Adjusts the frequency range of the spectrum and pitch tracking.
        Example: analyzer.adjustRange('C2', 'C6')
        """
        # 1. Convert note names to MIDI numbers to calculate range size
        
        midi_min = librosa.note_to_midi(minNote)
        midi_max = librosa.note_to_midi(maxNote)
        midi_max = min(midi_max, librosa.note_to_midi(self.maxNoteAllowed))
        self.minNote = minNote
        self.maxNote = librosa.midi_to_note(midi_max)
        # 2. Update core range parameters
        self.fmin = librosa.note_to_hz(minNote)
        self.n_bins = int(midi_max - midi_min) + 1  # Total semi-tones in range
        
        # 3. Re-compute note names for the new range
        self.note_names = [librosa.midi_to_note(m,unicode=False) for m in range(midi_min, midi_max + 1)]
        
        # 4. Re-compute A-weighting for the specific frequencies in this range
        self.note_freqs = librosa.cqt_frequencies(self.n_bins, fmin=self.fmin)
        self.a_weighting = librosa.A_weighting(self.note_freqs)

        print(f"Adjusted range: {minNote} to {maxNote}, Total Notes: {self.n_bins} fmin ={self.note_freqs[0]} fmax={self.note_freqs[-1]}")


    def getNumOctives(self):
        return math.ceil(len(self.note_freqs) / 12)



    def _audio_callback(self, indata, frames, time, status):
        # sounddevice gives us a numpy array directly
        self.recording.add_chunk(indata[:, 0])
        self.current_audio = indata[:, 0]

    def getStrongestNote(self):
        
        f0, voiced_flag, voiced_probs = self.getNoteIndexPyin()
        
        # 3. Apply A-Weighting
        if voiced_flag.any():
            # Find the average pitch of voiced frames, ignoring NaNs
            valid_pitches = f0[voiced_flag]
            if len(valid_pitches) > 0:
                actual_pitch = np.median(valid_pitches)

                
                # 4. Convert Frequency to Note Name
                note_name = librosa.hz_to_note(actual_pitch, unicode=False)
                return f"{note_name} (Prob: {np.mean(voiced_probs[voiced_flag]):.2f})"
        
        return "No strong note"

    def update(self):
        pass  # No internal state to update; analysis is done on-the-fly

    def getSampleRate(self):
        return self.RATE
    
    def getSensitivity(self):
        return self.sensitivity

    def getSpectrum(self):
        """
        Returns a list of (note_name, magnitude) tuples.
        Uses Constant-Q Transform to map energy directly to musical notes.
        """
        # 1. Compute CQT Magnitude (Frequency bins are musical notes)
        # We use a small hop_length to get a single frame of data
        wav = self.recording.getFlat()
        cqt = np.abs(librosa.cqt(
            wav, 
            sr=self.RATE, 
            fmin=self.fmin, 
            n_bins=self.n_bins,
            hop_length=len(wav)+ 1 
        ))
        
        # Flatten to get the 1D magnitude array
        note_magnitudes = cqt.flatten()

        # 2. Convert to dB and Apply A-Weighting
        mag_db = librosa.amplitude_to_db(note_magnitudes, ref=1.0)
        weighted_mag = mag_db + self.a_weighting

        # Returns: [('C2', -10.5), ('C#2', -15.2), ...]
        return zip(self.note_freqs, weighted_mag)

    def adjust_sensitivity(self, increase=True):
        """Increase or decrease the dB threshold."""
        # Moving closer to 0 makes it harder to trigger (requires more volume)
        step = 2 
        if increase:
            self.sensitivity += step
        else:
            self.sensitivity -= step
    
    def adjustSpectrum(self, noteShift=0, rangeShift=0):
        """
        Adjusts the spectrum by shifting notes or changing range.
        noteShift: number of semitones to shift the spectrum
        rangeShift: number of notes to shift the range
        """
        minNote = librosa.midi_to_note(librosa.note_to_midi(self.minNote) + noteShift)
        maxNote = librosa.midi_to_note(librosa.note_to_midi(self.maxNote) + noteShift+rangeShift)
        self.adjustRange(minNote, maxNote)       


    def getNoteIndexPyin(self):
        f0, voiced_flag, voiced_probs = librosa.pyin(self.recording.getFlat(),
                                             sr=self.RATE,
                                             fmin=self.note_freqs[0], 
                                             fmax=self.note_freqs[-1])
        return f0, voiced_flag, voiced_probs
    
    def getNoteIndex(self):       
        """
        Returns the index of the strongest note in the current spectrum.
        """
        # 1. Compute Pitch and Magnitudes using piptrack
        # Piptrack is more accurate than raw FFT for musical notes
        pitches, magnitudes = librosa.piptrack(
            y=self.current_audio, 
            sr=self.RATE, 
            fmin=self.note_freqs[0], 
            fmax=self.note_freqs[-1]
        )

        # 2. Find the strongest peak in the current frame
        return pitches, magnitudes, magnitudes.argmax()

    def __del__(self):
        self.stream.stop()
        self.stream.close()

    
