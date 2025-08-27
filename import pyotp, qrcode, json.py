import pyotp, qrcode, json, os
from PIL import Image
from datetime import datetime

# 📁 Crear carpetas si no existen
os.makedirs("qr_fichas", exist_ok=True)
os.makedirs("data_cursantes", exist_ok=True)

# 🧑‍🎓 Ingreso de datos
nombre = input("Nombre completo del cursante: ").strip()
correo = input("Correo electrónico: ").strip()
curso = input("Nombre del curso: ").strip()

# ⚠️ Validación básica
if not nombre or not correo or not curso:
    print("⚠️ Todos los campos son obligatorios.")
    exit()

# 🔐 Clave OTP única
clave_otp = pyotp.random_base32()
uri = pyotp.totp.TOTP(clave_otp).provisioning_uri(name=nombre, issuer_name="Academiae Coral Multisede")

# 🎟️ Generar QR
qr = qrcode.make(uri)
qr_img = qr.convert("RGB")

# 🖼️ Consagración visual (opcional: emblema institucional)
emblema_path = ""D:\ISAN atelier\GitHub\Favicon IAacademia 210 Emblema.jpg""
if os.path.exists(emblema_path):
    emblema = Image.open(emblema_path).resize((60, 60))
    qr_img.paste(emblema, (10, 10))  # Posición simbólica

# 📁 Guardar QR
nombre_archivo = f"qr_fichas/QR_{nombre.replace(' ', '')}_{curso.replace(' ', '')}.png"
qr_img.save(nombre_archivo)

# 🗂️ Guardar datos del cursante
registro = {
    "nombre": nombre,
    "correo": correo,
    "curso": curso,
    "clave_otp": clave_otp,
    "fecha": datetime.now().isoformat()
}
json_path = f"data_cursantes/{nombre.replace(' ', '')}_{curso.replace(' ', '')}.json"
with open(json_path, "w") as f:
    json.dump(registro, f, indent=4)

# ✅ Confirmación
print("\n🎓 QR generado y consagrado:")
print(f"📁 Archivo QR: {nombre_archivo}")
print(f"🔐 Clave OTP: {clave_otp}")
print(f"🗂️ Registro guardado en: {json_path}")
