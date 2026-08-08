import os
from PIL import Image, ImageDraw

def criar_icones():
    # Garante que a pasta static/img existe
    pasta_destino = os.path.join('static', 'img')
    os.makedirs(pasta_destino, exist_ok=True)

    # Cores da identidade visual do IMUTÁVEL FIRE
    cor_fundo = (15, 23, 42)      # #0F172A (Azul Escuro)
    cor_destaque = (220, 53, 69)  # #DC3545 (Vermelho)

    icones = [
        (192, 'icon-192.png'),
        (512, 'icon-512.png')
    ]

    for tamanho, nome_arquivo in icones:
        # Cria a imagem com o fundo azul escuro
        img = Image.new('RGB', (tamanho, tamanho), color=cor_fundo)
        draw = ImageDraw.Draw(img)

        # Desenha um círculo vermelho no centro para simular uma logo provisória
        padding = tamanho * 0.15
        draw.ellipse(
            [(padding, padding), (tamanho - padding, tamanho - padding)],
            fill=cor_destaque
        )

        # Salva o arquivo
        caminho_completo = os.path.join(pasta_destino, nome_arquivo)
        img.save(caminho_completo)
        
        print(f"✅ Ícone gerado com sucesso: {caminho_completo} ({tamanho}x{tamanho} px)")

if __name__ == '__main__':
    criar_icones()