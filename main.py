from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
from io import BytesIO
import time
import os

# Datos del SAT
SAT_URL = "https://portalcfdi.facturaelectronica.sat.gob.mx/"
DEMO_URL = "https://www.boxfactura.com/sat-captcha-ai-model/"

RFC = os.path.join(os.getcwd(), "RFC.txt")  # Cambia esto por tu archivo RFC
PASSWORD = os.path.join(os.getcwd(), "passwd.txt")  # Cambia esto por tu archivo de contraseña
try:
    with open(RFC, 'r') as rfc_file:
        rfc_content = rfc_file.read()

    with open(PASSWORD, 'r') as password_file:
        password_content = password_file.read()

except FileNotFoundError:
    print("Uno o ambos archivos no se encontraron.")
except Exception as e:
    print(f"Ocurrió un error: {e}")


# Inicializa Selenium
driver = webdriver.Firefox()  # Cambia si usas otro navegador
wait = WebDriverWait(driver, 10)

def descargar_captcha(driver):
    """Descargar la imagen del captcha de la página del SAT."""
    captcha_element = wait.until(
        EC.presence_of_element_located((By.ID, "divCaptcha"))
    )
    captcha_screenshot = captcha_element.screenshot_as_png
    captcha_image = Image.open(BytesIO(captcha_screenshot))

    # Especificar una ruta absoluta para guardar el archivo
    save_path = os.path.join(os.getcwd(), "captcha_sat.png")
    captcha_image.save(save_path)  # Guarda la imagen en el directorio actual
    print(f"Captcha descargado y guardado como '{save_path}'")
    return save_path

def resolver_captcha_en_demo(driver, captcha_image):
    """Abrir la página demo y resolver el captcha."""
    driver.execute_script("window.open('');")  # Abrir nueva pestaña
    driver.switch_to.window(driver.window_handles[1])  # Cambiar a la nueva pestaña
    driver.get(DEMO_URL)  # Navegar a la demo
    time.sleep(2)
    # Subir la imagen del captcha
    upload_element = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="file"]'))
    )
    upload_element.send_keys(captcha_image)
    time.sleep(3)
    # Obtener el resultado del captcha
    captcha_result = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'span.demo-output-result[data-js-result]'))
    ).text

    print(f"Captcha resuelto: {captcha_result}")

    # Cerrar la pestaña demo y volver al SAT
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return captcha_result


def iniciar_sesion_en_sat(driver, captcha_text):
    """Iniciar sesión en la página del SAT."""
    # Rellenar RFC
    rfc_input = wait.until(
        EC.presence_of_element_located((By.ID, "rfc"))
    )
    rfc_input.send_keys(rfc_content)


    # Rellenar contraseña
    password_input = wait.until(
        EC.presence_of_element_located((By.ID, "password"))
    )
    password_input.send_keys(password_content)


    # Rellenar el captcha
    captcha_input = wait.until(
        EC.presence_of_element_located((By.ID, "userCaptcha"))
    )
    captcha_input.send_keys(captcha_text)

    # Hacer clic en iniciar sesión
    submit_button = wait.until(
        EC.presence_of_element_located((By.ID, "submit"))
    )
    submit_button.click()
    print("Intentando iniciar sesión en el SAT...")

# En caso de detectar un error
def erroresSAT():

    pass


# Flujo principal
if __name__ == "__main__":
    try:
        driver.get(SAT_URL)
        # Descargar el captcha del SAT
        captcha_path = descargar_captcha(driver)
        # Resolver el captcha en la demo
        captcha_text = resolver_captcha_en_demo(driver, captcha_path)
        # Iniciar sesión en el SAT
        iniciar_sesion_en_sat(driver, captcha_text)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        time.sleep(10)  # Para inspección visual antes de cerrar
        driver.quit()
