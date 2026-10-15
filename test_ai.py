# Comentamos o TrOCR e importamos o Paddle
# from src.ocr.trocr_engine import TrOCREngine
from src.ocr.paddle_engine import PaddleEngine

def main():
    # Instancia o novo motor
    engine = PaddleEngine()
    
    # Mantenha os exatos mesmos caminhos que você usou no teste anterior
    imagem_nome = "data/processed/crops/linha_048_celula.jpg" 
    imagem_horario = "data/processed/crops/linha_050_celula.jpg"
    
    print("\n--- TESTE COM PADDLEOCR ---")
    print("Lendo o Nome...")
    texto_nome = engine.extract_text(imagem_nome)
    print(f"Resultado IA: '{texto_nome}'")
    
    print("\nLendo o Horário...")
    texto_horario = engine.extract_text(imagem_horario)
    print(f"Resultado IA: '{texto_horario}'")

if __name__ == "__main__":
    main()