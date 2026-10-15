import os
import cv2
import numpy as np
import matplotlib.pyplot as plt

class ImageCropper:
    def __init__(self):
        pass

    def load_image(self, image_path):
        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError(f"Não foi possível carregar a imagem: {image_path}")
        return img

    def correct_orientation(self, image):
        h, w = image.shape[:2]
        if h > w:
            image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        # Mantém o giro de 180 graus validado nas fotos atuais
        image = cv2.rotate(image, cv2.ROTATE_180)
        return image

    def preprocess_for_grid(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )
        return thresh

    def extract_grid(self, binary_image):
        kernel_horizontal = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        kernel_vertical = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))

        horizontal_lines = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, kernel_horizontal, iterations=2)
        vertical_lines = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, kernel_vertical, iterations=2)

        table_mask = cv2.bitwise_or(horizontal_lines, vertical_lines)
        return table_mask

    def crop_header_and_rows(self, original_image, grid_image, output_dir):
        """
        Recorta 1 imagem para o Cabeçalho da ficha e estritamente 1 tira horizontal 
        para cada linha manuscrita da tabela (sem mesclar múltiplas linhas).
        """
        os.makedirs(output_dir, exist_ok=True)

        for old_file in os.listdir(output_dir):
            if old_file.endswith(".jpg"):
                os.remove(os.path.join(output_dir, old_file))

        contours, _ = cv2.findContours(grid_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        img_h, img_w = original_image.shape[:2]

        # 1. Filtra estritamente células de linha única (altura entre 16px e 36px)
        cell_boxes = []
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            area = w * h
            if 350 < area < 50000 and 16 <= h <= 36:
                cell_boxes.append((x, y, w, h))

        if not cell_boxes:
            raise ValueError("Nenhuma linha da tabela foi detectada na imagem.")

        table_x_min = max(0, min(b[0] for b in cell_boxes) - 5)
        table_x_max = min(img_w, max(b[0] + b[2] for b in cell_boxes) + 5)

        # 2. Agrupa células pelo centro vertical (cy) com tolerância mais justa (11px)
        cell_boxes.sort(key=lambda b: b[1] + b[3] / 2.0)

        row_clusters = []
        tolerance_y = 11

        for box in cell_boxes:
            cy = box[1] + box[3] / 2.0
            if not row_clusters:
                row_clusters.append([box])
            else:
                prev_cy = np.mean([b[1] + b[3] / 2.0 for b in row_clusters[-1]])
                if abs(cy - prev_cy) <= tolerance_y:
                    row_clusters[-1].append(box)
                else:
                    row_clusters.append([box])

        # 3. Filtra apenas as linhas de dados reais (abaixo do cabeçalho "Nome/Horário")
        valid_rows = []
        for cluster in row_clusters:
            y_top = int(np.median([b[1] for b in cluster]))
            y_bottom = int(np.median([b[1] + b[3] for b in cluster]))
            if y_top > int(img_h * 0.28) and len(cluster) >= 3:
                valid_rows.append((y_top, y_bottom))

        # 4. Salva o CABEÇALHO da Folha (do topo até o início da primeira linha manuscrita)
        first_row_y = valid_rows[0][0] if valid_rows else int(img_h * 0.30)
        header_y_end = max(100, first_row_y - 45)
        header_crop = original_image[0:header_y_end, table_x_min:table_x_max]
        header_path = os.path.join(output_dir, "00_cabecalho.jpg")
        cv2.imwrite(header_path, header_crop)

        # 5. Salva cada linha individual com margem de segurança (3px) + Padding
        debug_image = original_image.copy()
        cv2.rectangle(debug_image, (table_x_min, 0), (table_x_max, header_y_end), (255, 0, 0), 2)

        row_paths = []
        for idx, (y_top, y_bottom) in enumerate(valid_rows, start=1):
            y1 = max(0, y_top - 3)
            y2 = min(img_h, y_bottom + 3)

            row_crop = original_image[y1:y2, table_x_min:table_x_max]
            if row_crop.size == 0:
                continue

            padded_row = cv2.copyMakeBorder(
                row_crop,
                top=12, bottom=12, left=15, right=15,
                borderType=cv2.BORDER_CONSTANT,
                value=[235, 235, 235]
            )

            row_filename = f"linha_{idx:02d}.jpg"
            row_path = os.path.join(output_dir, row_filename)
            cv2.imwrite(row_path, padded_row)
            row_paths.append(row_path)

            cv2.rectangle(debug_image, (table_x_min, y1), (table_x_max, y2), (0, 255, 0), 2)

        return header_path, row_paths, debug_image

    def show_side_by_side(self, original, processed, title1="Original", title2="Fatiamento por Linhas"):
        original_rgb = cv2.cvtColor(original, cv2.COLOR_BGR2RGB)
        processed_rgb = cv2.cvtColor(processed, cv2.COLOR_BGR2RGB)

        fig, axes = plt.subplots(1, 2, figsize=(15, 8))
        axes[0].imshow(original_rgb)
        axes[0].set_title(title1)
        axes[0].axis("off")

        axes[1].imshow(processed_rgb)
        axes[1].set_title(title2)
        axes[1].axis("off")

        plt.tight_layout()
        plt.show()