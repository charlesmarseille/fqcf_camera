#include <stdio.h>
#include <stdlib.h>
#include <jpeglib.h>

void encode_jpeg(unsigned char *buffer, int width, int height, const char *output_filename) {
    struct jpeg_compress_struct cinfo;
    struct jpeg_error_mgr jerr;

    FILE *out_file;
    JSAMPARRAY row_pointer;  // Pointeur vers la ligne d'image à compresser

    // Initialiser les structures JPEG
    cinfo.err = jpeg_std_error(&jerr);
    jpeg_create_compress(&cinfo);

    // Ouvrir le fichier de sortie
    if ((out_file = fopen(output_filename, "wb")) == NULL) {
        fprintf(stderr, "Erreur d'ouverture du fichier pour écriture %s\n", output_filename);
        exit(1);
    }

    // Définir les paramètres de compression
    jpeg_stdio_dest(&cinfo, out_file);

    cinfo.image_width = width;       // Largeur de l'image
    cinfo.image_height = height;     // Hauteur de l'image
    cinfo.input_components = 3;      // 3 canaux (RGB)
    cinfo.in_color_space = JCS_RGB; // Format couleur RGB

    jpeg_set_defaults(&cinfo);
    jpeg_set_quality(&cinfo, 85, TRUE); // Qualité JPEG (85 par défaut)

    // Démarrer la compression JPEG
    jpeg_start_compress(&cinfo, TRUE);

    // Allouer la mémoire pour une ligne d'image
    row_pointer = (JSAMPARRAY) malloc(sizeof(JSAMPLE *) * height);
    for (int i = 0; i < height; i++) {
        row_pointer[i] = buffer + i * width * 3;  // Pointeur vers chaque ligne d'image
    }

    // Compresser l'image ligne par ligne
    while (cinfo.next_scanline < cinfo.image_height) {
        jpeg_write_scanlines(&cinfo, row_pointer + cinfo.next_scanline, 1);
    }

    // Terminer la compression
    jpeg_finish_compress(&cinfo);
    fclose(out_file);

    // Libérer la mémoire
    jpeg_destroy_compress(&cinfo);
    free(row_pointer);

}

