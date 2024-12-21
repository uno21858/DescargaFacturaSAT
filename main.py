from scipy.constants import value
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
from io import BytesIO
import time
import os


def preguntar_mes():
    meses_a_descargar = {"enero": "1", "febrero": "2", "marzo": "3", "abril": "4", "mayo": "5", "junio": "6",
                         "julio": "7", "agosto": "8", "septiembre": "9", "octubre": "10", "noviembre": "11", "diciembre": "12"}

    mes = input("Ingresa el mes que deseas descargar (enero, febrero, etc...): ").lower()
    if mes in meses_a_descargar:
        return meses_a_descargar[mes]
    else:
        print("Mes inválido.")
        return preguntar_mes()




def preguntar_anio():
    anio = input("Ingresa los dos últimos dígitos del año que deseas descargar (ej. 21): ")
    if len(anio) == 2 and anio.isnumeric():
        anio_completo = int("20" + anio)
        anio_actual = int(time.strftime("%Y"))
        if anio_completo <= anio_actual:
            return anio
        else:
            print("Año inválido. No intente viajar al futuro.")
    else:
        print("Año inválido.")
    return preguntar_anio()

# Configuración
SAT_URL = "https://portalcfdi.facturaelectronica.sat.gob.mx/"
DEMO_URL = "https://www.boxfactura.com/sat-captcha-ai-model/"
RFC_FILE = os.path.join(os.getcwd(), "RFC.txt")
PASSWORD_FILE = os.path.join(os.getcwd(), "passwd.txt")
CAPTCHA_FILE = os.path.join(os.getcwd(), "captcha_sat.png")

# Cargar RFC y contraseña
def cargar_credenciales():
    try:
        with open(RFC_FILE, 'r') as rfc_file:
            rfc_content = rfc_file.read().strip()
        with open(PASSWORD_FILE, 'r') as password_file:
            password_content = password_file.read().strip()
        return rfc_content, password_content
    except FileNotFoundError:
        print("Uno o ambos archivos de credenciales no se encontraron.")
        raise
    except Exception as e:
        print(f"Error al cargar credenciales: {e}")
        raise

# Configurar navegador en modo headless
def configurar_navegador():
    options = Options()
    #options.add_argument("--headless")  # Navegación oculta
    options.add_argument("--width=1920")
    options.add_argument("--height=1080")
    driver = webdriver.Firefox(options=options)
    return driver

# Descargar captcha del SAT
def descargar_captcha(driver):
    captcha_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "divCaptcha"))
    )
    captcha_screenshot = captcha_element.screenshot_as_png
    time.sleep(2)
    captcha_image = Image.open(BytesIO(captcha_screenshot))
    captcha_image.save(CAPTCHA_FILE)
    print(f"Captcha guardado en {CAPTCHA_FILE}")
    return CAPTCHA_FILE

# Resolver captcha en demo
def resolver_captcha_en_demo(driver, captcha_image):
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[1])
    driver.get(DEMO_URL)
    upload_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="file"]'))
    )
    upload_element.send_keys(captcha_image)
    time.sleep(3)
    captcha_result = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'span.demo-output-result[data-js-result]'))
    ).text
    print(f"Captcha resuelto: {captcha_result}")
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return captcha_result

# Iniciar sesión en el SAT
def iniciar_sesion_en_sat(driver, rfc, password, captcha_text):
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "rfc"))
    ).send_keys(rfc)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "password"))
    ).send_keys(password)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "userCaptcha"))
    ).send_keys(captcha_text)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "submit"))
    ).click()
    print("Intentando iniciar sesión en el SAT...")

# Verificar errores de inicio de sesión
def verificar_error(driver):
    try:
        error_message = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "msgError"))
        ).text
        print(f"Error detectado: {error_message}")
        return True
    except:
        return False



# Función para crear estructura de carpetas
def crear_estructura_carpetas(base_dir, anio, mes):
    # Convertir mes numérico a formato de dos dígitos (ej. "01", "02", ...)
    # Crear ruta de la carpeta
    ruta_anio = os.path.join(base_dir, "xml_descargado", anio)
    ruta_mes = os.path.join(ruta_anio, mes)
    # Crear carpetas si no existen
    os.makedirs(ruta_mes, exist_ok=True)
    print(f"Carpeta creada o ya existente: {ruta_mes}")
    return ruta_mes

# Descargar XML Recibidos
def descarga(driver, destino):
    # IR a la sección de Recibidos
    driver.find_element(By.XPATH, "/html/body/form/main/div[1]/div[2]/div[1]/div/div[1]/div/nav/ul/div[2]/li/a").click()
    # Filtrar por fecha
    driver.find_element(By.ID, "ctl00_MainContent_RdoFechas").click()
    # Fecha de Emisión (mes)
    select_mes = Select(driver.find_element(By.ID, "ctl00_MainContent_CldFecha_DdlMes"))
    select_mes.select_by_value(mes)

    select_anio = Select(driver.find_element(By.ID, "DdlAnio"))
    select_anio.select_by_value("20" + year)

    # Poner RFC Emisor
    driver.find_element(By.ID, "ctl00_MainContent_TxtRfcReceptor").send_keys("GCO740121MC5")
    # Facturas Vigentes
    Select(driver.find_element(By.ID, "ctl00_MainContent_DdlEstadoComprobante")).select_by_value("1")
    # Buscar CFDis
    driver.find_element(By.ID, "ctl00_MainContent_BtnBusqueda").click()
    # Descargar XML
    botones_descarga = driver.find_elements(By.ID, "BtnDescarga")
    for index, boton in enumerate(botones_descarga, start=1):
        try:
            boton.click()
            print(f"Descargando XML {index} de {len(botones_descarga)}")
            time.sleep(1)
            # Mover los archivos descargados a la carpeta de destino
            archivo_descargado = mover_archivo_descargado(destino)
            print(f"Archivo movido a: {archivo_descargado}")
        except Exception as e:
            print(f"Error al descargar XML {index}: {e}")
            continue

def mover_archivo_descargado(destino):
    # Ruta predeterminada de descargas (ajusta si es necesario)
    ruta_descargas = os.path.join(os.path.expanduser("~"), "Downloads")
    archivos = [f for f in os.listdir(ruta_descargas) if f.endswith(".xml")]
    if archivos:
        archivo = archivos[-1]  # Toma el archivo más reciente
        origen = os.path.join(ruta_descargas, archivo)
        destino_final = os.path.join(destino, archivo)
        os.rename(origen, destino_final)
        return destino_final
    else:
        print("No se encontraron archivos XML en la carpeta de descargas.")
        return None



# Flujo principal
if __name__ == "__main__":
    base_dir = os.getcwd()  # Cambia esto si necesitas usar otra carpeta base
    year = preguntar_anio()
    mes = preguntar_mes()
    carpeta_destino = crear_estructura_carpetas(base_dir, "20" + year, mes)

    driver = configurar_navegador()
    rfc, password = cargar_credenciales()
    intentos = 0
    max_intentos = 6

    try:
        driver.get(SAT_URL)
        while intentos < max_intentos:
            try:
                time.sleep(1)
                captcha_path = descargar_captcha(driver)
                captcha_text = resolver_captcha_en_demo(driver, captcha_path)
                iniciar_sesion_en_sat(driver, rfc, password, captcha_text)
                if verificar_error(driver):
                    intentos += 1
                    print(f"Reintentando... ({intentos}/{max_intentos})")
                    driver.get(SAT_URL)  # Recargar página
                else:
                    print("Inicio de sesión exitoso.")
                    descarga(driver, carpeta_destino)
            except Exception as e:
                print(f"Error durante el intento: {e}")
                intentos += 1
        if intentos == max_intentos:
            print("Se alcanzó el límite máximo de intentos.")
    finally:
        time.sleep(5)
        driver.quit()
        print("Navegador cerrado.")