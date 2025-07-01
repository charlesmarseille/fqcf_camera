import qrcode

def create_qr_code(position_number: int, tunnel_number: int, tree_species: str, version_number: float, file_path: str):
    """
    Creates a QR code containing the specified data and saves it to a file.

    Args:
        position_number: The position number (integer).
        tunnel_number: The tunnel number (integer).
        tree_species: The tree species (string).
        version_number: The version number (float).
        file_path: The path to save the QR code image (e.g., "qr_code.png").
    """

    data = f"Position: {position_number}\n" \
           f"Tunnel: {tunnel_number}\n" \
           f"Espece: {tree_species}\n" \
           f"Pepiniere: {pepiniere_name}\n" \
           f"Version: {version_number}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(file_path)

if __name__ == '__main__':
    max_pos_num = 5
    tunnel_number = 123
    tree_species = "fir"
    pepiniere_name = "Girardville" 
    version_number = 1.0

    for position_number in range(max_pos_num + 1):
        file_path = f"qr_code_pos_{position_number}.png"
        create_qr_code(position_number, tunnel_number, tree_species, version_number, file_path)
        print(f"QR code created for position {position_number} and saved to {file_path}")