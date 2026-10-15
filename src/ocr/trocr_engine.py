from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image

class TrOCREngine:
    def __init__(self):
        print("Carregando o modelo TrOCR da Microsoft...")
        print("Nota: O primeiro uso fará o download do modelo (aprox. 1.5GB) para a sua máquina.")
        
        # Carrega o processador de imagem e o modelo focado em manuscrito
        self.processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
        self.model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-handwritten")

    def extract_text(self, image_path):
        """
        Recebe o caminho de uma imagem fatiada e retorna o texto lido.
        """
        # O TrOCR trabalha com imagens carregadas via PIL (Pillow) em RGB
        image = Image.open(image_path).convert("RGB")
        
        # Converte a imagem em tensores para a rede neural
        pixel_values = self.processor(image, return_tensors="pt").pixel_values
        
        # Faz a predição (inferência)
        generated_ids = self.model.generate(pixel_values)
        
        # Decodifica o resultado para texto legível
        generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        return generated_text