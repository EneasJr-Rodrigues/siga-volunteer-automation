import os
import glob
from src.image_processing.cropper import ImageCropper
from src.utils.catalog import VolunteerCatalog

def main():
    print("=== 1. Carregando Catálogo Oficial de Voluntários (Excel) ===")
    catalog = VolunteerCatalog()
    print(f"Total de voluntários na planilha: {len(catalog.nomes_todos)}")
    print(f"Voluntários ATIVOS prontos para o prompt: {len(catalog.nomes_ativos)}")

    # Teste rápido de validação com nomes manuscritos difíceis das fotos
    exemplos_manuscritos = [
        "Isaura M Souza Silva",
        "Maria G. Zirino",
        "Ma. Lourdes Tofanin Monteiro",
        "Edmilson de Aguiar Silva"
    ]
    print("\n--- Teste de Cruzamento Inteligente (Planilha) ---")
    for assinatura in exemplos_manuscritos:
        resultado = catalog.match_volunteer(assinatura)
        print(f"Manuscrito: '{assinatura}' -> Oficial: '{resultado['nome_oficial']}' (Cód: {resultado['codigo']} | Score: {resultado['score']}%)")

    print("\n=== 2. Fatiando Folha de Presença em Cabeçalho + Linhas Completas ===")
    raw_dir = os.path.join("data", "raw")
    crops_dir = os.path.join("data", "processed", "rows")

    image_files = sorted(glob.glob(os.path.join(raw_dir, "*.[jJ][pP]*[gG]")))
    if not image_files:
        print(f"Nenhuma imagem encontrada em '{raw_dir}'.")
        return

    test_image_path = image_files[0]
    print(f"Processando imagem: {test_image_path}")

    cropper = ImageCropper()
    img_raw = cropper.load_image(test_image_path)
    img_rotated = cropper.correct_orientation(img_raw)
    img_binary = cropper.preprocess_for_grid(img_rotated)
    img_grid = cropper.extract_grid(img_binary)

    header_path, row_paths, debug_img = cropper.crop_header_and_rows(img_rotated, img_grid, crops_dir)

    print(f"Cabeçalho salvo em: {header_path}")
    print(f"Total de tiras de linhas geradas: {len(row_paths)} (salvas em '{crops_dir}')")

    cropper.show_side_by_side(img_rotated, debug_img)

if __name__ == "__main__":
    main()