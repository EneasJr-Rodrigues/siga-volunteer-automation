from paddleocr import PaddleOCR
import logging

# Desativa logs verbosos do PaddleOCR para não sujar o terminal
logging.getLogger("ppocr").setLevel(logging.ERROR)

class PaddleEngine:
    def __init__(self):
        print("Carregando o modelo PaddleOCR (Multilíngue)...")
        # lang='pt' foca no nosso idioma. 
        # use_angle_cls=True tenta corrigir se a palavra estiver meio torta.
        self.ocr = PaddleOCR(use_angle_cls=True, lang='pt')

    def extract_text(self, image_path):
        """
        Lê a imagem fatiada e devolve o texto.
        """
        # O PaddleOCR recebe direto o caminho da imagem
        result = self.ocr.ocr(image_path, cls=True)
        
        texto_extraido = ""
        
        # O retorno é complexo (inclui coordenadas do polígono e grau de confiança).
        # Vamos extrair apenas o texto final.
        if result and result[0]:
            # result[0] é a lista de caixas de texto encontradas
            textos = [linha[1][0] for linha in result[0]]
            texto_extraido = " ".join(textos)
            
        return texto_extraido.strip()