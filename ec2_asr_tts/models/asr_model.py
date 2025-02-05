import nemo.collections.asr as nemo_asr
from nemo.collections.asr.models import EncDecMultiTaskModel


class TranscriptionWrapper:
    def __init__(self, model_name):
        if model_name == "nvidia/canary-1b":
            self.asr_model = EncDecMultiTaskModel.from_pretrained(model_name)
        if model_name == "nvidia/parakeet-ctc-0.6b":
            self.asr_model = nemo_asr.models.EncDecCTCModelBPE.from_pretrained(model_name)

    def transcribe(self, audio_file_path):
        transcript = self.asr_model.transcribe([audio_file_path])

        return transcript