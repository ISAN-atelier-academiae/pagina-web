import pyotp, qrcode, json
from PIL import Image
from datetime import datetime

# 🧑‍🎓 Ingreso de datos
nombre = input("Nombre completo del cursante: ")
correo = input("Correo electrónico: ")
curso = input("Nombre del curso: ")

# 🔐 Clave OTP única
clave_otp = pyotp.random_base32()
uri = pyotp.totp.TOTP(clave_otp).provisioning_uri(name=nombre, issuer_name="Academiae Coral Multisede")

# 🎟️ Generar QR
qr = qrcode.make(uri)
nombre_archivo = f"qr_fichas/QR_{nombre.replace(' ', '_')}_{curso.replace(' ', '_')}.png"
qr.save(nombre_archivo)

# 🗂️ Guardar datos del cursante
registro = {
    "nombre": nombre,
    "correo": correo,
    "curso": curso,
    "clave_otp": clave_otp,
    "fecha": datetime.now().isoformat()
}
with open(f"data_cursantes/{nombre.replace(' ', '_')}_{curso.replace(' ', '_')}.json", "w") as f:
    json.dump(registro, f, indent=4)

# ✅ Confirmación
print(f"\nQR generado y guardado en: {nombre_archivo}")
print(f"Clave OTP: {clave_otp}")