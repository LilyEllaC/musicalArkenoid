import numpy as np
import sounddevice as sd
import librosa
import math


class LibrosaAudioAnalyzer:
    def __init__(self):
        # Configuration
        self.RATE = 44100
        self.CHUNK = 1024   # Increased for better CQT resolution
        self.sensitivity = -10 
        
        # Define range: C2 to C7 (60 notes / 5 octaves)
        self.fmin = librosa.note_to_hz('C2')
        self.numOctives = 5
        self.n_bins = self.numOctives *12  # 12 notes per octave
        self.minNote = 'C2'
        self.maxNote = 'C7'
        self.adjustRange(self.minNote, self.maxNote)        

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
        self.current_audio = indata[:, 0]

    def getStrongestNote(self):
        pitches, magnitudes, index = self.getNoteIndex()
        pitch = pitches.flatten()[index]
        mag_db = librosa.amplitude_to_db(np.atleast_1d(magnitudes.flatten()[index]))[0]

        # 3. Apply A-Weighting
        if pitch > 0:
            a_weight = librosa.A_weighting(pitch)
            adjusted_mag = mag_db + a_weight
            
            if adjusted_mag > self.sensitivity:
                # 4. Convert Frequency to Note Name
                note_name = librosa.hz_to_note(pitch, unicode=False)
                return f"{note_name} (Mag: {adjusted_mag:.2f} dB)"
        
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
        cqt = np.abs(librosa.cqt(
            self.current_audio, 
            sr=self.RATE, 
            fmin=self.fmin, 
            n_bins=self.n_bins,
            hop_length=self.CHUNK + 1 
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
        self.minNote = librosa.midi_to_note(librosa.note_to_midi(self.minNote)+noteShift)
        self.maxNote = librosa.midi_to_note(librosa.note_to_midi(self.maxNote)+noteShift+rangeShift)
        self.adjustRange(self.minNote, self.maxNote)       

    
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

    
