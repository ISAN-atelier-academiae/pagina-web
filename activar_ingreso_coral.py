import os
import requests
from dotenv import load_dotenv
import subprocess
import json
import smtplib
from email.message import EmailMessage

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_INSCRIPCIONES_ID")
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}


def obtener_inscripciones_pendientes():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    filtro = {
        "filter": {
            "property": "Estado",
            "status": {
                "equals": "Pendiente"
            }
        }
    }
    try:
        response = requests.post(url, headers=HEADERS, json=filtro)
        data = response.json()
        print("Respuesta cruda de Notion:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return data.get("results", [])
    except Exception as e:
        print(f"No se pudo conectar a Notion, usando inscripción de ejemplo. Error: {e}")
        return [
            {
                "id": "ejemplo-id",
                "properties": {
                    "Nombre": {"title": [{"text": {"content": "Cursante Ejemplo"}}]},
                    "Correo": {"email": "ejemplo@correo.com"},
                    "Curso": {"rich_text": [{"text": {"content": "Curso Prueba"}}]}
                }
            }
        ]


def procesar_cursante(cursante):
    props = cursante["properties"]
    nombre = props["Nombre"]["title"][0]["text"]["content"]
    # Permitir ambas claves: 'Correo electrónico' y 'Correo'
    if "Correo electrónico" in props:
        correo = props["Correo electrónico"]["email"]
    elif "Correo" in props:
        correo = props["Correo"]["email"]
    else:
        correo = ""
    # Usar el primer valor de multi_select en Suscripción con Certificado o Sin Certificado
    if "Suscripción con Certificado" in props and props["Suscripción con Certificado"].get("multi_select") and props["Suscripción con Certificado"]["multi_select"]:
        curso = props["Suscripción con Certificado"]["multi_select"][0]["name"]
    elif "Sin Certificado" in props and props["Sin Certificado"].get("multi_select") and props["Sin Certificado"]["multi_select"]:
        curso = props["Sin Certificado"]["multi_select"][0]["name"]
    else:
        curso = "Sin curso"


    # Limpiar el nombre del curso para usarlo en nombres de archivo
    import re
    curso_archivo = re.sub(r'[^A-Za-z0-9]', '', curso)

    # Enviar QR de pago en el primer correo
    enviar_correo_pago(nombre, correo, curso)

    # Ejecutar el script de generación con argumentos (solo si el pago está confirmado)
    # subprocess.run(["python", "generar_qr_otp.py", nombre, correo, curso])
    # ...el resto del flujo para OTP y acceso se ejecuta tras la confirmación de pago...


def enviar_correo_pago(nombre, correo, curso):
    remitente = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    if not remitente or not password:
        print("No se configuró el correo de envío. EMAIL_USER y EMAIL_PASS deben estar en .env")
        return
    asunto = f"Instrucciones de pago para tu suscripción: {curso}"
    cuerpo = (
        f"Hola {nombre},\n"
        f"Gracias por tu interés en el curso '{curso}'.\n\n"
        "Adjunto encontrarás el código QR con los datos bancarios para realizar el pago de tu suscripción.\n\n"
        "Por favor, realiza el pago y responde a este correo con el comprobante. Una vez confirmado, recibirás tu acceso y código OTP.\n\n"
        "Datos bancarios:\n"
        "Mercantil, C.A, Banco Universal\n"
        "RIF. J-00002961-0\n"
        "Nombre del cliente: Miguel Ibanez\n"
        "Tipo de cuenta: Cuenta Corriente\n"
        "Número de cuenta: 01050065691065326750\n"
        "Documento de identidad: V-11.953.571\n"
        "Tpag: 0426-298 35 71\n"
    "SWIFT: MERCVECA\n"
    "País: Venezuela\n"
    "Dirección: AVE. ANDRES BELLO NO 1 EDIF MERCANTIL PISO 31/P.O. BOX 789\n"
    "Ciudad: CARACAS 1050\n\n"
        "¡Gracias por confiar en ISAN atelier academiae!"
    )
    msg = EmailMessage()
    msg["Subject"] = asunto
    msg["From"] = remitente
    msg["To"] = correo
    msg.set_content(cuerpo)
    # Adjuntar QR de pago
    qr_pago_path = "qr_fichas/QR_pago_MiguelIbanez.png"
    try:
        with open(qr_pago_path, "rb") as f:
            qr_data = f.read()
        msg.add_attachment(qr_data, maintype="image", subtype="png", filename="QR_pago_MiguelIbanez.png")
    except Exception as e:
        print(f"No se pudo adjuntar el QR de pago: {e}")
    # Enviar correo
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(remitente, password)
            smtp.send_message(msg)
        print(f"Correo de pago enviado a {correo}")
    except Exception as e:
        print(f"Error enviando correo de pago a {correo}: {e}")

def enviar_correo_estudiante(nombre, correo, curso, clave_otp, qr_path):
    remitente = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    if not remitente or not password:
        print("No se configuró el correo de envío. EMAIL_USER y EMAIL_PASS deben estar en .env")
        return
    asunto = f"Inscripción confirmada: {curso}"
    cuerpo = f"""
Hola {nombre},

Tu inscripción al curso '{curso}' ha sido confirmada.

Adjunto encontrarás tu código QR y tu clave OTP para el acceso seguro:

Clave OTP: {clave_otp}
Instrucciones: Usa la clave OTP en una app autenticadora (Google Authenticator, Authy, etc.)

¡Nos vemos en el curso!
"""
    msg = EmailMessage()
    msg["Subject"] = asunto
    msg["From"] = remitente
    msg["To"] = correo
    msg.set_content(cuerpo)
    # Adjuntar QR
    try:
        with open(qr_path, "rb") as f:
            qr_data = f.read()
        msg.add_attachment(qr_data, maintype="image", subtype="png", filename=os.path.basename(qr_path))
    except Exception as e:
        print(f"No se pudo adjuntar el QR: {e}")
    # Enviar correo
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(remitente, password)
            smtp.send_message(msg)
        print(f"Correo enviado a {correo}")
    except Exception as e:
        print(f"Error enviando correo a {correo}: {e}")

def actualizar_notion(page_id, clave_otp, qr_path):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    data = {
        "properties": {
            "Clave OTP": {
                "rich_text": [{ "text": { "content": clave_otp } }]
            },
            "QR generado": {
                "url": f"file:///{os.path.abspath(qr_path).replace('\\', '/')}"
            },
            "Estado": {
                "status": { "name": "Enviado" }
            }
        }
    }
    requests.patch(url, headers=HEADERS, json=data)

def obtener_suscriptores_estado(estado):
    # Obtiene registros de la segunda base con el estado indicado
    database_id = os.getenv("NOTION_SUSCRIPTORES_ID")
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    filtro = {
        "filter": {
            "property": "Estado",
            "status": {"equals": estado}
        }
    }
    response = requests.post(url, headers=HEADERS, json=filtro)
    data = response.json()
    return data.get("results", [])

def procesar_suscriptores_estado(estado="Pagado", estado_final="Enviado"):
    suscriptores = obtener_suscriptores_estado(estado)
    print(f"Total suscriptores con estado '{estado}': {len(suscriptores)}")
    for suscriptor in suscriptores:
        props = suscriptor["properties"]
        nombre = props["Nombre"]["title"][0]["plain_text"]
        correo = props["Correo electrónico"]["email"]
        # Usar el primer valor de multi_select en Suscripción con Certificado o Sin Certificado
        if "Suscripción con Certificado" in props and props["Suscripción con Certificado"].get("multi_select") and props["Suscripción con Certificado"]["multi_select"]:
            curso = props["Suscripción con Certificado"]["multi_select"][0]["name"]
        elif "Sin Certificado" in props and props["Sin Certificado"].get("multi_select") and props["Sin Certificado"]["multi_select"]:
            curso = props["Sin Certificado"]["multi_select"][0]["name"]
        else:
            curso = "Sin curso"
        # Generar OTP y QR
        import pyotp, qrcode
        clave_otp = pyotp.random_base32()
        qr_img = qrcode.make(f"OTP:{clave_otp}\nNombre:{nombre}\nCurso:{curso}")
        import re
        def limpiar_texto(texto):
            # Elimina caracteres no válidos para nombres de archivo en Windows
            return re.sub(r'[\\/:*?"<>|$.,]', '', texto.replace(' ', ''))
        nombre_limpio = limpiar_texto(nombre)
        curso_limpio = limpiar_texto(curso)
        qr_path = f"qr_fichas/QR_{nombre_limpio}_{curso_limpio}.png"
        os.makedirs("qr_fichas", exist_ok=True)
        qr_img.save(qr_path)
        # Actualizar Notion
        actualizar_notion(suscriptor["id"], clave_otp, qr_path)
        # Enviar correo
        enviar_correo_estudiante(nombre, correo, curso, clave_otp, qr_path)
        # Cambiar estado en Notion a estado_final
        url = f"https://api.notion.com/v1/pages/{suscriptor['id']}"
        data = {"properties": {"Estado": {"status": {"name": estado_final}}}}
        requests.patch(url, headers=HEADERS, json=data)
        print(f"Suscriptor {nombre} procesado y marcado como '{estado_final}'.")


# Ritual principal


def procesar_ejemplo():
    ejemplo = {
        "id": "ejemplo-id",
        "properties": {
            "Nombre": {"title": [{"text": {"content": "Cursante Ejemplo"}}]},
            "Correo electrónico": {"email": "ejemplo@correo.com"},
            "Curso": {"rich_text": [{"text": {"content": "Curso Prueba"}}]}
        }
    }
    print("Procesando inscripción de ejemplo...")
    procesar_cursante(ejemplo)
    print("Cursante de ejemplo procesado.")

if __name__ == "__main__":
    print("Obteniendo inscripciones pendientes desde Notion...")
    inscripciones = obtener_inscripciones_pendientes()
    print(f"Total inscripciones pendientes: {len(inscripciones)}")  # Este mensaje ya está en español
    if len(inscripciones) == 0:
        opcion = input("No hay inscripciones pendientes. ¿Procesar inscripción de ejemplo? (s/n): ").strip().lower()
        if opcion == "s":
            procesar_ejemplo()
    else:
        for idx, cursante in enumerate(inscripciones, 1):
            print(f"Procesando cursante {idx}/{len(inscripciones)}...")
            procesar_cursante(cursante)
            print(f"Cursante procesado: {cursante['properties']['Nombre']['title'][0]['text']['content']}")
        print("\nProceso finalizado.")  # Este mensaje ya está en español
    # Procesar suscriptores con estado 'Pagado' y marcar como 'Enviado'
    print("\nProcesando suscriptores con estado 'Pendiente'...")
    procesar_suscriptores_estado(estado="Pendiente", estado_final="Enviado")
    print("\nSuscriptores 'Pendiente' procesados y marcados como 'Enviado'.")