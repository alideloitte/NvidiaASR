import torch
from nemo.collections.tts.models.base import SpectrogramGenerator, Vocoder
from nemo.collections.tts.models import FastPitchModel, MixerTTSModel, HifiGanModel, UnivNetModel#, TwoStagesModel
import soundfile as sf

class SpeechWrapper:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.spec_gen = self.load_spectrogram_model("tts_en_fastpitch").eval().cuda()
        self.vocoder = self.load_vocoder_model("tts_en_lj_univnet").eval().cuda()

    def load_spectrogram_model(self, model_name):
        model = SpectrogramGenerator.from_pretrained(model_name)
        return model


    def load_vocoder_model(self, model_name):
        model = Vocoder.from_pretrained(model_name, strict=True)
        return model


    def infer(self, str_input):
        parser_model = self.spec_gen
        with torch.no_grad():
            parsed = parser_model.parse(str_input)
            gen_spec_kwargs = {}
            
            spectrogram = self.spec_gen.generate_spectrogram(tokens=parsed, **gen_spec_kwargs)
            audio = self.vocoder.convert_spectrogram_to_audio(spec=spectrogram)

        if spectrogram is not None:
            if isinstance(spectrogram, torch.Tensor):
                spectrogram = spectrogram.to('cpu').numpy()
            if len(spectrogram.shape) == 3:
                spectrogram = spectrogram[0]
        if isinstance(audio, torch.Tensor):
            audio = audio.to('cpu').detach().numpy()[0]

        print("Audio created.")
        #sf.write("speech.wav", audio, 22050)
        return audio