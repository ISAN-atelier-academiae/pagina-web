import qrcode

# Datos bancarios para el QR
qr_data = '''Mercantil, C.A, Banco Universal\nRIF. J-00002961-0\nNombre del cliente: Miguel Ibanez\nTipo de cuenta: Cuenta Corriente\nNúmero de cuenta: 01050065691065326750\nDocumento de identidad: V-11.953.571\nTpag: 0426-298 35 71\nSWIFT: MERCVECA\nPaís: Venezuela'''

qr_img = qrcode.make(qr_data)
qr_img.save("qr_fichas/QR_pago_MiguelIbanez.png")
print("QR de pago generado y guardado en qr_fichas/QR_pago_MiguelIbanez.png")
