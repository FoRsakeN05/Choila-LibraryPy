from email.message import EmailMessage
import subprocess
from cryptography.fernet import Fernet, InvalidToken
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QMainWindow, QPushButton, QVBoxLayout, 
                             QLineEdit, QLabel, QDialog, QDesktopWidget, 
                             QMessageBox, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QComboBox, QHBoxLayout)
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt
from datetime import datetime, timedelta
import json, os, ssl, smtplib, sys, mariadb, re

# Datos para enviar correos electrónicos
password = "gvqr gzpl irqn mqzk"            # Contraseña de app generada para el correo electrónico
                                            # No debería estar aquí, pero es necesario para enviar correos electrónicos
                                            # Y es una cuenta de correo propia para pruebas (Pueden usar dotenv para ocultarla)
                                            # Creen una cuenta de correo para la app y generen una contraseña de app
                                            # Para crear una contraseña de app, vayan a https://myaccount.google.com/u/0/apppasswords
                                            # Ocupan activar la verificación en dos pasos para poder generar una contraseña de app
                                            # La contraseña de app solo se puede ver una vez, así que guárdenla en un lugar seguro
                                            # Si les sirve, pueden usar la cuenta de correo que puse aquí, pero así no tendrán acceso
                                            # Yo ví este video para hacerlo: https://www.youtube.com/watch?v=oPAo8Hh8bj0
                                            # No vayan a dejar estos comentarios en su código, es solo para que sepan cómo hacerlo xd

email_sender = "librarypy2024@gmail.com"    # Correo electrónico del remitente
email_reciver = " "                         # Correo electrónico del destinatario
email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'   # Expresión regular para validar correos electrónicos
subject = " "                               # Asunto del correo
body = " "                                  # Cuerpo del correo

# Versión de la aplicación
version = "1.0.0"

# Obtiene el directorio del script
script_dir = os.path.dirname(__file__)  

# Obtiene el directorio de la aplicación
appdata = os.environ["APPDATA"]
directorio_libreria = os.path.join(appdata, "LibraryPy")

# Abre el directorio de la librería, se los dejo por si quieren usarlo para saber dónde se guardan los archivos
# No es necesario para la aplicación, pero puede ser útil para que sepan dónde se guardan los archivos
# Básicamente, el directorio es C:\Users\Usuario\AppData\Roaming\LibraryPy
def abrir_directorio():
    if os.path.exists(directorio_libreria):
        subprocess.Popen(['explorer', directorio_libreria])
            
    else:
        print(f"El directorio {directorio_libreria} no existe.")

# Quitar comentario para abrir el directorio
# abrir_directorio()

class VentanaPago(QDialog):
    def __init__(self, account_id, credit, account_email):
        super().__init__()
        self.credit = credit
        self.account_id = account_id
        self.account_email = account_email
        self.init_ui()

    def init_ui(self):
        # Título de la ventana
        self.setWindowTitle("Pagar")
        # Tamaño fijo de la ventana
        self.setFixedSize(300, 300)
        # Quitar el botón de ayuda
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        # Saldo pendiente
        self.labelCredit = QLabel(self)
        self.labelCredit.setText(f"Saldo pendiente: ${self.credit}.00 MXN")
        # Etiqueta para nombre del beneficiario
        self.labelNombre = QLabel(self)
        self.labelNombre.setText("Nombre del beneficiario:")
        self.inputNombre = QLineEdit(self)

        # Etiqueta para numero de tarjeta
        self.labelTarjeta = QLabel(self)
        self.labelTarjeta.setText("Número de tarjeta:")
        self.inputTarjeta = QLineEdit(self)
        self.inputTarjeta.setInputMask("9999-9999-9999-9999")
        
        # Selector de mes
        self.labelMes = QLabel(self)
        self.labelMes.setText("Mes de vencimiento:")
        self.comboMes = QComboBox(self)
        self.comboMes.addItems(["01 - Enero", "02 - Febrero", "03 - Marzo", "04 - Abril", "05 - Mayo", "06 - Junio",
                                "07 - Julio", "08 - Agosto", "09 - Septiembre", "10 - Octubre", "11 - Noviembre", "12 - Diciembre"])

        # Selector de año
        self.labelAño = QLabel(self)
        self.labelAño.setText("Año de vencimiento:")
        self.comboAño = QComboBox(self)
        current_year = datetime.now().year
        self.comboAño.addItems([str(año) for año in range(current_year, current_year+15)])

        # Iconos de Visa y Mastercard
        
        image_visa = os.path.join(script_dir, "img/visa.png")
        image_master = os.path.join(script_dir, "img/mastercard.png")
        pixmap_visa = QPixmap(image_visa)
        pixmap_mastercard = QPixmap(image_master)
        self.labelVisa = QLabel(self)
        self.labelVisa.setPixmap(pixmap_visa.scaledToHeight(30))
        self.labelVisa.setAlignment(Qt.AlignCenter)
        self.labelVisa.setScaledContents(True)
        self.labelMastercard = QLabel(self)
        self.labelMastercard.setPixmap(pixmap_mastercard.scaledToHeight(30))
        self.labelMastercard.setAlignment(Qt.AlignCenter)
        self.labelMastercard.setScaledContents(True)

        # Layout para los iconos
        icon_layout = QHBoxLayout()
        icon_layout.addWidget(self.labelVisa)
        icon_layout.addWidget(self.labelMastercard)
        icon_layout.setAlignment(Qt.AlignCenter)

        self.btnPay = QPushButton("Pagar", self)
        self.btnPay.clicked.connect(self.pay)

        layout = QVBoxLayout()
        layout.addLayout(icon_layout)
        layout.addWidget(self.labelCredit)
        layout.addWidget(self.labelNombre)
        layout.addWidget(self.inputNombre)
        layout.addWidget(self.labelTarjeta)
        layout.addWidget(self.inputTarjeta)
        layout.addWidget(self.labelMes)
        layout.addWidget(self.comboMes)
        layout.addWidget(self.labelAño)
        layout.addWidget(self.comboAño)
        layout.addWidget(self.btnPay)

        self.setLayout(layout)
        self.center()

    def center(self):
        # Obtenemos la geometría de la ventana principal
        qr = self.frameGeometry()
        # Obtenemos la posición central de la pantalla
        cp = QDesktopWidget().availableGeometry().center()
        # Movemos la ventana al centro de la pantalla
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        
    def conectar(self):
        try:
            conn = mariadb.connect(
                user="libraryPy",
                password="michoacan",
                host="64.23.180.219",
                port=3306,
                database="biblioteca"
            )
            return conn
        except Exception as e:
            print("Error al conectar con la base de datos:", e)
            return None

    def luhn_check(self, tarjeta):

        tarjeta = tarjeta.replace("-", "")
        tarjeta = tarjeta.replace(" ", "")

        digits = [int(d) for d in tarjeta]
   
        for i in range(len(digits) - 2, -1, -2):
            digits[i] *= 2
            if digits[i] > 9:
                digits[i] -= 9

        checksum = sum(digits)

        return checksum % 10 == 0
    
    def pay(self):
        # Obtener los datos ingresados por el usuario
        nombre = self.inputNombre.text()
        tarjeta = self.inputTarjeta.text().replace(" ", "")
        mes_vencimiento = self.comboMes.currentText()
        año_vencimiento = self.comboAño.currentText()
        # Verificar si el nombre es válido
        if not nombre:
            QtWidgets.QMessageBox.critical(None, "Error", "Por favor, ingrese el nombre del beneficiario.")
            return
        # Verificar si la tarjeta es válida (solo números y longitud de 16)
        if not re.match("^[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{4}$", tarjeta):
            QtWidgets.QMessageBox.critical(None, "Error", "Número de tarjeta inválido.")
            return
        # Validar el número de la tarjeta utilizando el algoritmo de Luhn
        if not self.luhn_check(tarjeta):
            QtWidgets.QMessageBox.critical(None, "Error", "Número de tarjeta inválido según la verificación de Luhn.")
            return
        # Realizar el pago y actualizar la base de datos
        conn = self.conectar()
        if conn:
            try:
                cursor = conn.cursor()
                # Realizar el pago y actualizar el crédito del usuario
                cursor.execute("UPDATE usuarios SET credit = 0 WHERE id = ?", (self.account_id,))
                conn.commit()
                QtWidgets.QMessageBox.information(None, "Pago exitoso", "El pago se ha realizado con éxito.\nPuede que el pago tarde un poco en verse reflejado, reinicie la aplicación si el pago no se ve reflejado.")
            except mariadb.Error as e:
                print(f"Error al actualizar la base de datos: {e}")
            finally:
                
                conn.close()
            fecha_hoy = datetime.now().strftime('%d / %m / %Y')
            subject = f"Saldo pendiente liquidado"
            body = f"""
Has realizado el pago de tu saldo pendiente con éxito el día {fecha_hoy}.

Gracias por tu preferencia.
    """
            email_reciver = self.account_email
            if re.match(email_regex, email_reciver):
                em = EmailMessage()
                em["From"] = email_sender
                em["To"] = email_reciver
                em["Subject"] = subject
                em.set_content(body)

                try:
                    context = ssl.create_default_context()
                    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
                        smtp.login(email_sender, password)
                        smtp.sendmail(email_sender, email_reciver, em.as_string())
                    print("Correo enviado correctamente.")
                except Exception as e:
                    print(f"Error al enviar el correo: {e}")
            else:
                print("Dirección de correo electrónico no válida.")
        else:
            QtWidgets.QMessageBox.critical(None, "Error", "No se pudo conectar a la base de datos.")
    
        # Cerrar la ventana de pago
        self.accept()

class VentanaRegistro(QDialog):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Define los elementos de la ventana modal aquí
        self.setWindowTitle("Registrarse")
        self.setGeometry(600, 300, 600, 300)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # Etiqueta para email
        self.labelEmail = QLabel(self)
        self.labelEmail.setText("Email:")
        self.inputEmail = QLineEdit(self)
        # Etiqueta para contraseña
        self.labelPassword = QLabel(self)
        self.labelPassword.setText("Contraseña:")
        self.inputPassword = QLineEdit(self)
        # Etiqueta para nombre
        self.labelName = QLabel(self)
        self.labelName.setText("Nombre:")
        self.inputName = QLineEdit(self)
        # Etiqueta para Apellido1
        self.labelLastName1 = QLabel(self)
        self.labelLastName1.setText("Apellido paterno:")
        self.inputLastName1 = QLineEdit(self)
        # Etiqueta para Apellido2
        self.labelLastName2 = QLabel(self)
        self.labelLastName2.setText("Apellido materno:")
        self.inputLastName2 = QLineEdit(self)

        # Botón para eliminar el registro
        self.btnRegister = QPushButton("Registrarse", self)
        self.btnRegister.clicked.connect(self.insertar)

        # Layout vertical para organizar los elementos
        layout = QVBoxLayout()
        layout.addWidget(self.labelEmail)
        layout.addWidget(self.inputEmail)
        layout.addWidget(self.labelPassword)
        layout.addWidget(self.inputPassword)
        layout.addWidget(self.labelName)
        layout.addWidget(self.inputName)
        layout.addWidget(self.labelLastName1)
        layout.addWidget(self.inputLastName1)
        layout.addWidget(self.labelLastName2)
        layout.addWidget(self.inputLastName2)
        layout.addWidget(self.btnRegister)
        # Asigna el layout a la ventana modal
        self.setLayout(layout)
        self.center()

    def center(self):
        # Obtenemos la geometría de la ventana principal
        qr = self.frameGeometry()
        # Obtenemos la posición central de la pantalla
        cp = QDesktopWidget().availableGeometry().center()
        # Movemos la ventana al centro de la pantalla
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # Método para conectar a la base de datos
    def conectar(self):
        try:
            conn = mariadb.connect(
                user="root",
                password="250755",
                host="127.0.0.1",
                port=3306,
                database="biblioteca"
            )
            return conn
        except Exception as e:
            print("Error al conectar con la base de datos:", e)
            return None

    # Método para validar el correo electrónico
    def validarcorreo(self, txtAValidar):
        x=re.search("^[\w\.-]+@[a-zA-Z\d\.-]+\.[a-zA-Z]{2,}$", txtAValidar)
        return x

    # Método para validar la contraseña
    def validarpass(self, txtAValidar):
        x=re.search("^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$¡!%*¿?&(){}[\]<>^;:,./\\|_~`+=-])[A-Za-z\d@$¡!%*¿?&(){}[\]<>^;:,./\\|_~`+=-]{8,}$", txtAValidar)
        return x

    # Método para validar campos vacíos
    def validarVacio(self, txtAValidar, n = 3):
        if txtAValidar is None or len(txtAValidar.strip()) < n:
            return True
        return False

    # Método para llamar a la función de insertar un usuario en la base de datos
    def insertar(self):
        # Obtener los valores ingresados por el usuario
        email = self.inputEmail.text()
        contraseña = self.inputPassword.text()
        nombre = self.inputName.text()
        apellido1 = self.inputLastName1.text()
        apellido2 = self.inputLastName2.text()

        if not self.validarcorreo(email):
            QtWidgets.QMessageBox.critical(self, "Error", "Formato de correo inválido.")
            return

        if not self.validarpass(contraseña):
            QtWidgets.QMessageBox.critical(self, "Error", "La contraseña debe tener al menos 8 caracteres, una mayúscula, una minúscula, un número y un carácter especial.")
            return
        
        if self.validarVacio(nombre):
            QtWidgets.QMessageBox.critical(self, "Error", "El nombre es obligatorio y debe tener al menos 3 caracteres.")
            return
        
        if self.validarVacio(apellido1):
            QtWidgets.QMessageBox.critical(self, "Error", "El apellido paterno es obligatorio y debe tener al menos 3 caracteres.")
            return
        
        if self.validarVacio(apellido2):
            QtWidgets.QMessageBox.critical(self, "Error", "El apellido materno es obligatorio y debe tener al menos 3 caracteres.")
            return
        
        # Insertar el registro en la base de datos
        try:
            # Asignar el ID del usuario registrado a la variable usuario_id
            usuario_id = self.insertar_usuarios(email, contraseña, nombre, apellido1, apellido2)
            if usuario_id:
                QtWidgets.QMessageBox.information(self, "Éxito", "Registro realizado correctamente.")
                print("ID del usuario registrado:", usuario_id)
                self.close()

        except mariadb.Error as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Error al realizar el registro: {e}")

    # Ejecutar una consulta en la base de datos
    def ejecutar_query(self, query, values):
        try:
            conn = self.conectar()
            cur = conn.cursor()
            cur.execute(query, values)
            conn.commit()
            return cur.lastrowid
        except mariadb.Error as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Error al realizar el registro: {e}")
            return None
        finally:
            if conn:
                conn.close()

    # Método para insertar un nuevo registro en la base de datos
    def insertar_usuarios(self, email, contraseña, nombre, apellido1, apellido2):
        query = "INSERT INTO usuarios (email, password, name, last_name1, last_name2) VALUES (?, ?, ?, ?, ?)"
        values = (email, contraseña, nombre, apellido1, apellido2)
        # Ejecutar la consulta y retornar el ID del usuario registrado
        return self.ejecutar_query(query, values)

# Clase principal de la aplicación
class Ui_MainWindow(object):
    def __init__(self):
        self.key = self.cargar_clave()  # Carga la clave en una variable de instancia
        self.cipher_suite = Fernet(self.key)  # Crea la suite de cifrado

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.setWindowModality(QtCore.Qt.NonModal)
        MainWindow.resize(860, 480)
        MainWindow.setMinimumSize(QtCore.QSize(860, 480))
        MainWindow.setMaximumSize(QtCore.QSize(860, 480))
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setGeometry(QtCore.QRect(0, 0, 851, 461))
        self.tabWidget.setObjectName("tabWidget")
        self.tab_search = QtWidgets.QWidget()
        self.tab_search.setObjectName("tab_search")
        
        # Inicializar la QTableWidget para mostrar los resultados
        self.tableSearch = QTableWidget(self.tab_search)
        self.tableSearch.setGeometry(QtCore.QRect(30, 50, 781, 331))
        self.tableSearch.setObjectName("tableSearch")
        self.tableSearch.setColumnCount(5)  # Número de columnas para mostrar los resultados
        self.tableSearch.setHorizontalHeaderLabels(["Título", "Autor", "Género", "ID", "Estado"])
        self.tableSearch.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tableSearch.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tableSearch.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)

        self.label = QtWidgets.QLabel(self.tab_search)

        self.label.setGeometry(QtCore.QRect(30, 10, 61, 16))
        self.label.setObjectName("label")

        self.btnSearchTitle = QtWidgets.QPushButton(self.tab_search)
        self.btnSearchTitle.setGeometry(QtCore.QRect(540, 10, 75, 23))
        font = QtGui.QFont()
        font.setPointSize(7)
        self.btnSearchTitle.setFont(font)
        self.btnSearchTitle.setObjectName("btnSearchTitle")
        self.btnSearchTitle.clicked.connect(self.searchTitle)

        self.searchBar = QtWidgets.QLineEdit(self.tab_search)
        self.searchBar.setGeometry(QtCore.QRect(90, 10, 441, 20))
        self.searchBar.setText("")
        self.searchBar.setObjectName("searchBar")
        self.searchBar.returnPressed.connect(self.searchTitle)


        self.btnSearchAutor = QtWidgets.QPushButton(self.tab_search)
        self.btnSearchAutor.setGeometry(QtCore.QRect(640, 10, 75, 23))
        font = QtGui.QFont()
        font.setPointSize(7)
        self.btnSearchAutor.setFont(font)
        self.btnSearchAutor.setObjectName("btnSearchAutor")
        self.btnSearchAutor.clicked.connect(self.searchAuthor)

        self.btnSearchGenre = QtWidgets.QPushButton(self.tab_search)
        self.btnSearchGenre.setGeometry(QtCore.QRect(740, 10, 75, 23))
        font = QtGui.QFont()
        font.setPointSize(7)
        self.btnSearchGenre.setFont(font)
        self.btnSearchGenre.setObjectName("btnSearchGenre")
        self.btnSearchGenre.clicked.connect(self.searchGenre)

        self.btnReservar = QtWidgets.QPushButton(self.tab_search)
        self.btnReservar.setGeometry(QtCore.QRect(610, 390, 201, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.btnReservar.setFont(font)
        self.btnReservar.setObjectName("btnReservar")
        self.btnReservar.clicked.connect(self.reservar)

        self.tabWidget.addTab(self.tab_search, "")
        self.tab_history = QtWidgets.QWidget()
        self.tab_history.setObjectName("tab_history")

        # Inicializar la QTableWidget para mostrar los resultados
        self.tableHistory = QTableWidget(self.tab_history)
        self.tableHistory.setGeometry(QtCore.QRect(30, 50, 781, 331))
        self.tableHistory.setObjectName("tableHistory")
        self.tableHistory.setColumnCount(6)  # Número de columnas para mostrar los resultados
        self.tableHistory.setHorizontalHeaderLabels(["ID", "ID del libro", "Título del libro", "Fecha de prestamo", "Fecha de devolución", "Estado"])
        self.tableHistory.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tableHistory.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tableHistory.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tableHistory.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tableHistory.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.tableHistory.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)

        self.tabWidget.addTab(self.tab_history, "")
        self.tab_mybooks = QtWidgets.QWidget()
        self.tab_mybooks.setObjectName("tab_mybooks")
        
        # Inicializar la QTableWidget para mostrar los resultados
        self.tableMyBooks = QTableWidget(self.tab_mybooks)
        self.tableMyBooks.setGeometry(QtCore.QRect(30, 50, 781, 331))
        self.tableMyBooks.setObjectName("tableMyBooks")
        self.tableMyBooks.setColumnCount(7)  # Número de columnas para mostrar los resultados
        self.tableMyBooks.setHorizontalHeaderLabels(["ID","Título", "Autor", "ID Libro", "Fecha de prestamo", "Fecha de devolución", "Estado"])
        # Ajustar el tamaño de las columnas automáticamente
        self.tableMyBooks.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tableMyBooks.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tableMyBooks.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tableMyBooks.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tableMyBooks.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.tableMyBooks.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.tableMyBooks.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)

        self.tabWidget.currentChanged.connect(self.tab_changed)
        self.tableMyBooks.verticalHeader().setVisible(False)
        self.tableSearch.verticalHeader().setVisible(False)
        self.tableHistory.verticalHeader().setVisible(False)

        self.btnCancelar = QtWidgets.QPushButton(self.tab_mybooks)
        self.btnCancelar.setGeometry(QtCore.QRect(30, 390, 101, 23))
        self.btnCancelar.setObjectName("btnCancelar")
        self.btnCancelar.clicked.connect(self.cancelar_reserva)

        self.btnDevolver = QtWidgets.QPushButton(self.tab_mybooks)
        self.btnDevolver.setGeometry(QtCore.QRect(150, 390, 101, 23))
        self.btnDevolver.setObjectName("btnDevolver")
        self.btnDevolver.clicked.connect(self.devolver_reserva)

        self.tabWidget.addTab(self.tab_mybooks, "")
        self.tab_account = QtWidgets.QWidget()
        self.tab_account.setObjectName("tab_account")
        self.btnLogin = QtWidgets.QPushButton(self.tab_account)
        self.btnLogin.setGeometry(QtCore.QRect(370, 300, 101, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.btnLogin.setFont(font)
        self.btnLogin.setObjectName("btnLogin")
        self.btnLogin.clicked.connect(lambda: self.iniciar_sesion(True))
        self.label_2 = QtWidgets.QLabel(self.tab_account)
        self.label_2.setGeometry(QtCore.QRect(340, 40, 171, 61))
        font = QtGui.QFont()
        font.setPointSize(22)
        self.label_2.setFont(font)
        self.label_2.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_2.setObjectName("label_2")
        self.inputEmail = QtWidgets.QLineEdit(self.tab_account)
        self.inputEmail.setGeometry(QtCore.QRect(270, 160, 311, 31))
        self.inputEmail.setObjectName("inputEmail")
        self.inputPassword = QtWidgets.QLineEdit(self.tab_account)
        self.inputPassword.setGeometry(QtCore.QRect(270, 240, 311, 31))
        self.inputPassword.setEchoMode(QtWidgets.QLineEdit.Password)
        self.inputPassword.setObjectName("inputPassword")
        self.inputPassword.returnPressed.connect(lambda: self.iniciar_sesion(True))
        self.label_3 = QtWidgets.QLabel(self.tab_account)
        self.label_3.setGeometry(QtCore.QRect(260, 360, 211, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.pushButton_8 = QtWidgets.QPushButton(self.tab_account)
        self.pushButton_8.setGeometry(QtCore.QRect(500, 360, 101, 31))
        self.pushButton_8.clicked.connect(self.registrarse)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.pushButton_8.setFont(font)
        self.pushButton_8.setObjectName("pushButton_8")
        self.label_4 = QtWidgets.QLabel(self.tab_account)
        self.label_4.setGeometry(QtCore.QRect(390, 130, 61, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label_4.setFont(font)
        self.label_4.setObjectName("label_4")
        self.label_5 = QtWidgets.QLabel(self.tab_account)
        self.label_5.setGeometry(QtCore.QRect(380, 210, 91, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label_5.setFont(font)
        self.label_5.setObjectName("label_5")
        self.tabWidget.addTab(self.tab_account, "")
        
        self.tab_user = QtWidgets.QWidget()
        self.tab_user.setObjectName("tab_user")

        self.labelNombre = QtWidgets.QLabel(self.tab_user)
        self.labelNombre.setGeometry(QtCore.QRect(30, 30, 781, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.labelNombre.setFont(font)
        self.labelNombre.setObjectName("labelNombre")

        self.labelCredit = QtWidgets.QLabel(self.tab_user)
        self.labelCredit.setGeometry(QtCore.QRect(30, 90, 781, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.labelCredit.setFont(font)
        self.labelCredit.setObjectName("labelCredit")

        self.labelUserID = QtWidgets.QLabel(self.tab_user)
        self.labelUserID.setGeometry(QtCore.QRect(30, 150, 781, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.labelUserID.setFont(font)
        self.labelUserID.setObjectName("labelUserID")

        self.labelApellido2 = QtWidgets.QLabel(self.tab_user)
        self.labelApellido2.setGeometry(QtCore.QRect(30, 150, 781, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.labelApellido2.setFont(font)
        self.labelApellido2.setObjectName("labelApellido2")

        self.btnLogout = QtWidgets.QPushButton(self.tab_user)
        self.btnLogout.setGeometry(QtCore.QRect(30, 380, 141, 31))
        self.btnLogout.clicked.connect(self.logout)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.btnLogout.setFont(font)
        self.btnLogout.setObjectName("btnLogout")

        self.btnPay = QtWidgets.QPushButton(self.tab_user)
        self.btnPay.setGeometry(QtCore.QRect(670, 380, 141, 31))
        self.btnPay.clicked.connect(self.pay)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.btnPay.setFont(font)
        self.btnPay.setObjectName("btnPay")


        self.tabWidget.addTab(self.tab_user, "")

        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self.account_id = 0
        self.credit = 0
        self.account_email = ""
        self.cargar_credenciales()
        self.tabWidget.removeTab(4)
        self.tabWidget.setCurrentIndex(0)

        # Establecer el tema oscuro directamente en el método setupUi
        """
        MainWindow.setStyleSheet("background-color: #26233b;")
        self.centralwidget.setStyleSheet("background-color: #26233b; color: #ffffff;")
        self.statusbar.setStyleSheet("background-color: #26233b; color: #ffffff;")
        tooltip_stylesheet = "QToolTip { color: #ffffff; background-color: #333333; border: 1px solid white; }"
        QtWidgets.QApplication.instance().setStyleSheet(tooltip_stylesheet)
        """

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        # Título de la ventana principal con la versión de la aplicación
        MainWindow.setWindowTitle(_translate("MainWindow", f"LibraryPy - {version}"))
        icon = os.path.join(script_dir, 'img/icon.ico').replace("\\", "/")
        MainWindow.setWindowIcon(QIcon(icon))
        self.label.setText(_translate("MainWindow", "Busqueda:"))
        self.btnSearchTitle.setText(_translate("MainWindow", "Buscar título"))
        self.searchBar.setPlaceholderText(_translate("MainWindow", "Título, autor o género"))
        self.btnSearchAutor.setText(_translate("MainWindow", "Buscar autor"))
        self.btnSearchGenre.setText(_translate("MainWindow", "Buscar género"))
        self.btnReservar.setText(_translate("MainWindow", "Reservar"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_search), _translate("MainWindow", "Busqueda"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_history), _translate("MainWindow", "Historial de prestamos"))
        self.btnCancelar.setText(_translate("MainWindow", "Cancelar reserva"))
        self.btnDevolver.setText(_translate("MainWindow", "Devolver libro"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_mybooks), _translate("MainWindow", "Mis libros"))
        self.btnLogin.setText(_translate("MainWindow", "Entrar"))
        self.label_2.setText(_translate("MainWindow", "Iniciar Sesión"))
        self.inputEmail.setPlaceholderText(_translate("MainWindow", "user@example.com"))
        self.inputPassword.setPlaceholderText(_translate("MainWindow", "Aa12345678+¿?"))
        self.label_3.setText(_translate("MainWindow", "¿Aún no tienes una cuenta?"))
        self.pushButton_8.setText(_translate("MainWindow", "Registrarse"))
        self.btnLogout.setText(_translate("MainWindow", "Cerrar sesión"))
        self.btnPay.setText(_translate("MainWindow", "Pagar saldo"))
        self.label_4.setText(_translate("MainWindow", "Correo:"))
        self.label_5.setText(_translate("MainWindow", "Contraseña:"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_account), _translate("MainWindow", "Cuenta"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_user), _translate("MainWindow", "Datos de usuario"))

    def registrarse(self):
        ventana_registro = VentanaRegistro()
        if ventana_registro.exec_() == QDialog.Accepted:
            usuario_id = ventana_registro.insertar_usuarios()
            if usuario_id:
                # Aquí puedes hacer lo que necesites con el ID del usuario
                print("ID del usuario insertado:", usuario_id)
                self.account_id = usuario_id

    def conectar(self):
        try:
            conn = mariadb.connect(
                user="libraryPy",
                password="michoacan",
                host="64.23.180.219",
                port=3306,
                database="biblioteca"
            )
            return conn
        except Exception as e:
            print("Error al conectar con la base de datos:", e)
            return None

    def iniciar_sesion(self, showMessage):
        email = self.inputEmail.text()
        contraseña = self.inputPassword.text()

        if not email or not contraseña:
            QtWidgets.QMessageBox.critical(None, "Error", "Por favor, ingrese email y contraseña.")
            return

        try:
            conn = self.conectar()
            cur = conn.cursor()
            cur.execute("SELECT id, name, last_name1, last_name2, credit, email FROM usuarios WHERE email = ? AND password = ?", (email, contraseña))
            usuario = cur.fetchone()

            if usuario:
                self.account_id = usuario[0]
                self.credit = usuario[4]
                self.account_email = usuario[5]
                self.tabWidget.setCurrentIndex(3)  # Cambia a la pestaña tab_account
                self.labelNombre.setText("Nombre: " + usuario[1] + " " + usuario[2] + " " + usuario[3])
                self.labelCredit.setText(f"Saldo pendiente: ${str(self.credit)}")
                self.labelUserID.setText(f"ID: {str(self.account_id)}")
                # self.labelApellido2.setText("Apellido Materno: " + usuario[3])
                if(showMessage):
                    QtWidgets.QMessageBox.information(None, "Inicio de sesión exitoso", f"¡Bienvenido {usuario[1]} {usuario[2]} {usuario[3]}!")
                self.guardar_credenciales(email, contraseña)
                self.tabWidget.insertTab(4, self.tab_user, "Datos de usuario")  # Muestra la pestaña tab_user al cerrar sesión
                self.tabWidget.removeTab(3)  # Oculta la pestaña tab_user al iniciar sesión
                self.tabWidget.setCurrentIndex(4)  # Cambia a la pestaña tab_account
            else:
                if(showMessage):
                    QtWidgets.QMessageBox.critical(None, "Error", "Credenciales inválidas.\n¿El usuario está registrado?")

        except mariadb.Error as e:
            QtWidgets.QMessageBox.critical(None, "Error", f"Error al iniciar sesión: {e}")

        finally:
            if conn:
                conn.close()

    def guardar_credenciales(self, email, contraseña):
        credenciales = {'email': email, 'contraseña': contraseña}
        credenciales_encriptadas = self.cipher_suite.encrypt(json.dumps(credenciales).encode())  # Encripta las credenciales
        data = {'credenciales': credenciales_encriptadas.decode()}  # Crea un objeto JSON con las credenciales encriptadas
        # Crea un directorio para guardar la clave si no existe
        os.makedirs(f'{directorio_libreria}', exist_ok=True)
        # Guarda las credenciales en un archivo
        credenciales_file = os.path.join(directorio_libreria, 'credenciales.json')
        with open(credenciales_file, 'w') as file:
            json.dump(data, file)  # Guarda el objeto JSON en un archivo
    
    def cargar_credenciales(self):
        # Crea un directorio para guardar la clave si no existe
        os.makedirs(f'{directorio_libreria}', exist_ok=True)
        # Carga las credenciales desde un archivo
        credenciales_file = os.path.join(directorio_libreria, 'credenciales.json')
        if not os.path.exists(credenciales_file):
            return

        with open(credenciales_file, 'r') as file:
            data = json.load(file)  # Carga el objeto JSON de un archivo

        if not data or 'credenciales' not in data:
            return

        try:
            credenciales_desencriptadas = self.cipher_suite.decrypt(data['credenciales'].encode()).decode()  # Desencripta las credenciales
            credenciales = json.loads(credenciales_desencriptadas)
            self.inputEmail.setText(credenciales['email'])
            self.inputPassword.setText(credenciales['contraseña'])
            self.iniciar_sesion(showMessage=False)  # Evitar que se muestre el mensaje al cargar las credenciales
        except (json.JSONDecodeError, InvalidToken):
            QtWidgets.QMessageBox.critical(None, "Error", "El archivo de credenciales no tiene un formato JSON válido o la clave de encriptación es incorrecta.")
            return

    # Método para cargar la clave de encriptación        
    def cargar_clave(self):
        # Crea un directorio para guardar la clave si no existe
        os.makedirs(f'{directorio_libreria}', exist_ok=True)
        # Carga la clave de un archivo o genera una nueva si no existe
        key_file = os.path.join(directorio_libreria, 'clave.key')
        if not os.path.exists(key_file):
            key = Fernet.generate_key()  # Genera una nueva clave si no existe una
            with open(key_file, 'w') as file:
                file.write(key.decode())  # Guarda la clave en un archivo
            return key
        else:
            with open(key_file, 'r') as file:
                key = file.read().encode()  # Lee la clave de un archivo
            return key
    
    # Método para cerrar sesión
    def logout(self):
        # Crea un directorio para guardar la clave si no existe
        os.makedirs(f'{directorio_libreria}', exist_ok=True)
        # Elimina el archivo de credenciales al cerrar sesión
        credenciales = os.path.join(directorio_libreria, "credenciales.json")
        if os.path.exists(credenciales):
            os.remove(credenciales)
            # NO DEBE ELIMINARSE clave.key, ESTO GENERARÍA UNA NUEVA CLAVE Y NO SE PODRÍAN DESCIFRAR LOS DATOS
            # SI SE ELIMINA SE DEBERÁN ELIMINAR TAMBIÉN LOS ARCHIVOS CIFRADOS Y VOLVER A INICIAR SESIÓN
            self.account_id = 0
            self.inputEmail.clear()
            self.inputPassword.clear()
            self.tabWidget.insertTab(3, self.tab_account, "Cuenta")  # Muestra la pestaña tab_user al cerrar sesión
            self.tabWidget.removeTab(4)  # Oculta la pestaña tab_user al cerrar sesión
            self.tabWidget.setCurrentIndex(3)  # Cambia a la pestaña tab_account

    # Busqueda por título
    def searchTitle(self):
        title = self.searchBar.text()
        if title:
            query = f"SELECT * FROM libro WHERE titulo LIKE '%{title}%'"
            self.mostrar_resultados(query, "título", title)
        else:
            QtWidgets.QMessageBox.critical(None, "Error", "Primero escribe algo en el buscador.")

    # Busqueda por autor
    def searchAuthor(self):
        author = self.searchBar.text()
        if author:
            query = f"SELECT * FROM libro WHERE autor LIKE '%{author}%'"
            self.mostrar_resultados(query, "autor", author)
        else:
            QtWidgets.QMessageBox.critical(None, "Error", "Primero escribe algo en el buscador.")

    # Busqueda por genero
    def searchGenre(self):
        genre = self.searchBar.text()
        if genre:
            query = f"SELECT * FROM libro WHERE genero LIKE '%{genre}%'"
            self.mostrar_resultados(query, "género", genre)
        else:
            QtWidgets.QMessageBox.critical(None, "Error", "Primero escribe algo en el buscador.")

    # Método para mostrar los resultados de la búsqueda
    def mostrar_resultados(self, query, tipo_busqueda, busqueda):
        try:
            self.tableSearch.clearContents()
            self.tableSearch.setRowCount(0)
            
            cur = self.consulta(query)
            if cur:
                found = False
                for row_number, row_data in enumerate(cur):
                    self.tableSearch.insertRow(row_number)
                    # Ajusta el orden de los datos para mostrarlos en la tabla
                    data_order = [3, 1, 4, 0, 2]  # Orden de las columnas: titulo, autor, genero, id, estado
                    for column_number, index in enumerate(data_order):
                        if index == 2:  # Si la columna es la del estado
                            estado = "Disponible" if row_data[index] == 1 else "No disponible"
                            item = QTableWidgetItem(estado)
                        else:
                            item = QTableWidgetItem(str(row_data[index]))
                        # Establecer el hint para mostrar el texto completo cuando el mouse pasa sobre la celda
                        if index == 2:
                            item.setToolTip(estado)
                        else:
                            item.setToolTip(str(row_data[index]))
                        self.tableSearch.setItem(row_number, column_number, item)
                    found = True
                if not found:
                    QtWidgets.QMessageBox.information(None, "Información", f"No se encontraron resultados para el {tipo_busqueda} '{busqueda}'.")
            else:
                QtWidgets.QMessageBox.information(None, "Información", f"No se encontraron resultados para el {tipo_busqueda} '{busqueda}'.")
        except Exception as e:
            print("Error al mostrar resultados:", e)

    # Método para realizar una consulta en la base de datos
    def consulta(self, query, values=None):
        try:
            conn = self.conectar()
            if conn:
                cur = conn.cursor()
                if values:
                    if not isinstance(values, (tuple, list)):
                        values = (values,)
                    cur.execute(query, values)
                else:
                    cur.execute(query)
                return cur
        except Exception as e:
            print("Error al ejecutar la consulta:", e)
            return None
        finally:
            if conn:
                conn.close()

    # Reservar un libro
    def reservar(self):
        # Verificar si el usuario ha iniciado sesión
        if self.account_id == 0:
            QtWidgets.QMessageBox.critical(None, "Error", "Debes iniciar sesión para reservar un libro.")
            return
        # Obtener el índice de la fila seleccionada
        selected_row = self.tableSearch.currentRow()
        if selected_row >= 0:
            # Obtener los datos de la fila seleccionada
            id_libro = self.tableSearch.item(selected_row, 3).text()  # ID del libro
            disponibilidad = self.tableSearch.item(selected_row, 4).text()  # Disponibilidad del libro
            titulo = self.tableSearch.item(selected_row, 0).text()  # Título del libro
            autor = self.tableSearch.item(selected_row, 1).text()  # Autor del libro

            # Verificar si el libro está disponible
            if disponibilidad == 'Disponible':
                reply = QMessageBox.question(None, 'Reserva', 'El costo por reserva de cada libro es de $7.00 MXN por día, se te dará un limite de 15 días para retornarlo. Si no se devuelve a tiempo se cobrará una multa de $20 por cáda día que pase.\n(Es posible devolver antes el libro, solo se te cobrará lo correspondiente)',
                            QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
                if reply == QMessageBox.Ok:
                    # Obtener la fecha actual
                    fecha_prestamo = datetime.now().strftime('%Y-%m-%d')
                    # Obtener la fecha de devolución (15 días después de la fecha actual)
                    fecha_devolucion = (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d')
                    # Obtener el ID de usuario
                    id_usuario = self.account_id
                    
                    # Insertar el préstamo en la base de datos
                    query = "INSERT INTO prestamo (fecha_devolucion, fecha_prestamo, id_usuario, id_libro) VALUES (?, ?, ?, ?)"
                    values = (fecha_devolucion, fecha_prestamo, id_usuario, id_libro)
                    id_pedido = self.ejecutar_query(query, values)
                    query = "INSERT INTO historial (id, fecha_devolucion, fecha_prestamo, id_usuario, id_libro) VALUES (?, ?, ?, ?, ?)"
                    values = (id_pedido, fecha_devolucion, fecha_prestamo, id_usuario, id_libro)
                    self.ejecutar_query(query, values)
                    if id_pedido:
                        self.correo_pedido(id_pedido, fecha_prestamo, fecha_devolucion, titulo, autor)
                        # Cambiar la disponibilidad del libro a 0
                        query = "UPDATE libro SET disponibilidad = 0 WHERE id = ?"
                        values = (id_libro,)
                        self.ejecutar_query(query, values)
                        
                        QtWidgets.QMessageBox.information(None, "Información", "Libro reservado con éxito.")
                        self.tableSearch.item(selected_row, 4).setText("No disponible")
            else:
                QtWidgets.QMessageBox.critical(None, "Error", "El libro seleccionado no está disponible.")
        else:
            QtWidgets.QMessageBox.critical(None, "Error", "Selecciona un libro para reservar.")

    # Método para ejecutar una consulta en la base de datos
    def ejecutar_query(self, query, values):
        try:
            conn = self.conectar()
            if conn:
                cur = conn.cursor()
                cur.execute(query, values)
                conn.commit()
                return cur.lastrowid
        except Exception as e:
            print("Error al ejecutar la consulta:", e)
        finally:
            if conn:
                conn.close()

    # Actualizar la disponibilidad de un libro
    def actualizar_disponibilidad_libro(self, id_libro, disponibilidad):
        query = "UPDATE libro SET disponibilidad = ? WHERE id = ?"
        values = (disponibilidad, id_libro)
        self.ejecutar_query(query, values)
    
    # Insertar un nuevo préstamo en la base de datos
    def insertar_prestamo(self, fecha_devolucion, fecha_prestamo, id_usuario, id_libro):
        query = "INSERT INTO prestamo (fecha_devolucion, fecha_prestamo, id_usuario, id_libro) SELECT ?, ?, (SELECT id FROM usuarios WHERE id = ?), (SELECT id FROM libro WHERE id = ?)"
        values = (fecha_devolucion, fecha_prestamo, id_usuario, id_libro)
        self.insertar(query, values)
    
    # Método para insertar un nuevo registro en la base de datos
    def insertar(self, query, values):
        try:
            conn = self.conectar()
            if conn:
                cur = conn.cursor()
                cur.execute(query, values)
                conn.commit()
                print("Datos insertados correctamente.")
        except Exception as e:
            print(f"Error al insertar datos: {e}")
        finally:
            if conn:
                conn.close()

    # Consultar los libros reservados por el usuario actual
    def actualizar_mis_libros(self, estado = ""):
        # Limpiar la tabla
        self.tableMyBooks.clearContents()
        self.tableMyBooks.setRowCount(0)
        # Verificar si el usuario ha iniciado sesión
        if self.account_id == 0:
            QtWidgets.QMessageBox.critical(None, "Error", "Debes iniciar sesión para ver tus libros.")
            return
        # Obtener los préstamos del usuario actual
        query = "SELECT prestamo.id, libro.titulo, libro.autor, libro.id, prestamo.fecha_prestamo, prestamo.fecha_devolucion, prestamo.devuelto FROM prestamo INNER JOIN libro ON prestamo.id_libro = libro.id WHERE prestamo.id_usuario = ?"
        values = (self.account_id)
        cur = self.consulta(query, values)
        if cur.rowcount > 0:
            for row_number, row_data in enumerate(cur):
                self.tableMyBooks.insertRow(row_number)
                for column_number, data in enumerate(row_data):
                    item = QTableWidgetItem(str(data))
                    if column_number == 6:  # Columna 6
                        if data == 0:
                            item.setText("Reservado")
                        elif data == 2:
                            item.setText("Cancelado")

                    # Insertar el item en la tabla
                    self.tableMyBooks.setItem(row_number, column_number, item)
        else:
            QtWidgets.QMessageBox.information(None, "Información", "No tienes libros reservados.")

    # Actualizar el historial de préstamos del usuario actual
    def actualizar_historial(self):
        # Limpiar la tabla
        self.tableHistory.clearContents()
        self.tableHistory.setRowCount(0)
        if self.account_id == 0:
            QtWidgets.QMessageBox.critical(None, "Error", "Debes iniciar sesión para ver tu historial.")
            return
        # Obtener el historial del usuario actual
        query = "SELECT h.id, l.id, l.titulo, h.fecha_prestamo, h.fecha_devolucion, h.devuelto FROM historial AS h INNER JOIN libro AS l ON h.id_libro = l.id WHERE h.id_usuario = ?"
        values = (self.account_id,)
        cur = self.consulta(query, values)
        if cur.rowcount > 0:
            for row_number, row_data in enumerate(cur):
                self.tableHistory.insertRow(row_number)
                for column_number, data in enumerate(row_data):
                    item = QTableWidgetItem(str(data))
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                    if column_number == 5:  # Verificar si estamos en la columna de "devuelto"
                        if data == 0:
                            item.setText("Reservado")
                        elif data == 1:
                            item.setText("Devuelto")
                        elif data == 2:
                            item.setText("Cancelado")
                    # Insertar el item en la tabla
                    self.tableHistory.setItem(row_number, column_number, item)
        else:
            QtWidgets.QMessageBox.information(None, "Información", "No tienes historial de préstamos.")

    # Cancelar un préstamo
    def cancelar_reserva(self):
        # Obtener el índice de la fila seleccionada
        selected_row = self.tableMyBooks.currentRow()
        if selected_row >= 0:
            # Obtener los datos de la fila seleccionada
            id_prestamo = int(self.tableMyBooks.item(selected_row, 0).text())  # ID de prestamo
            id_libro = int(self.tableMyBooks.item(selected_row, 3).text())  # ID de libro
            fecha_prestamo = self.tableMyBooks.item(selected_row, 4).text()  # Fecha de prestamo
            fecha_hoy = datetime.now().strftime('%Y-%m-%d')
            if fecha_prestamo == fecha_hoy:
                try:
                    # Cambiar 'disponibilidad' del libro con id = id_libro a 1
                    query = "UPDATE libro SET disponibilidad = 1 WHERE id = ?"
                    self.ejecutar_query(query, (id_libro,))

                    # Cambiar 'devuelto' del prestamo con id = id_prestamo a 2
                    query2 = "UPDATE historial SET devuelto = 2 WHERE id = ?"
                    self.ejecutar_query(query2, (id_prestamo,))

                    # Borrar la tupla de la tabla 'prestamo' con 'id' = id_prestamo
                    query3 = "DELETE FROM prestamo WHERE id = ?"
                    self.ejecutar_query(query3, (id_prestamo,))
                    self.correo_cancelacion(id_prestamo)
                    QtWidgets.QMessageBox.information(None, "Cancelación de reserva", "Reserva cancelada con éxito.")

                    # Actualizar la tabla de mis libros
                    self.actualizar_mis_libros()

                except mariadb.Error as e:
                    QtWidgets.QMessageBox.critical(None, "Error", f"Error al cancelar reserva: {e}")

            else:
                QtWidgets.QMessageBox.warning(None, "Error", "Solo puedes cancelar reservas que se han hecho el mismo día.")

    # Devolver un libro
    def devolver_reserva(self):
        # Obtener el índice de la fila seleccionada
        selected_row = self.tableMyBooks.currentRow()
        if selected_row >= 0:
            # Obtener los datos de la fila seleccionada
            id_prestamo = int(self.tableMyBooks.item(selected_row, 0).text())  # ID de prestamo
            id_libro = int(self.tableMyBooks.item(selected_row, 3).text())  # ID de libro
            fecha_devolucion = datetime.strptime(self.tableMyBooks.item(selected_row, 5).text(), '%Y-%m-%d')  # Fecha de devolucion
            fecha_prestamo = datetime.strptime(self.tableMyBooks.item(selected_row, 4).text(), '%Y-%m-%d')  # Fecha de prestamo
            fecha_hoy = datetime.now()
            fecha_hoy_sin_tiempo = fecha_hoy.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Calcular la diferencia de días
            dias_diferencia = (fecha_hoy_sin_tiempo - fecha_prestamo).days
            # Si se pasa de los 15 días, agregar la multa de $20 por día adicional
            if dias_diferencia > 15:
                costo = (dias_diferencia - 15) * 20
            else:
                costo = max(0, dias_diferencia) * 7
            try:
                # Obtener el crédito actual del usuario
                query_credito = "SELECT credit FROM usuarios WHERE id = ?"
                cur_credito = self.consulta(query_credito, (self.account_id,))
                credito_actual = cur_credito.fetchone()[0]

                # Sumar el costo al crédito actual
                nuevo_credito = credito_actual + costo
                self.credit = nuevo_credito
                # Actualizar el crédito del usuario en la base de datos
                query_actualizar_credito = "UPDATE usuarios SET credit = ? WHERE id = ?"
                self.ejecutar_query(query_actualizar_credito, (nuevo_credito, self.account_id))

                # Cambiar 'disponibilidad' del libro con id = id_libro a 1
                query1 = "UPDATE libro SET disponibilidad = 1 WHERE id = ?"
                self.ejecutar_query(query1, (id_libro,))

                # Cambiar 'devuelto' del prestamo con id = id_prestamo a 1
                query2 = "UPDATE historial SET devuelto = 1 WHERE id = ?"
                self.ejecutar_query(query2, (id_prestamo,))

                # Borrar la tupla de la tabla 'prestamo' con 'id' = id_prestamo
                query3 = "DELETE FROM prestamo WHERE id = ?"
                self.ejecutar_query(query3, (id_prestamo,))
                self.correo_devolucion(id_prestamo, fecha_devolucion, costo)
                QtWidgets.QMessageBox.information(None, "Devolución de reserva", f"Libro devuelto con éxito.\nCosto: ${costo}")

                # Actualizar la tabla de mis libros
                self.actualizar_mis_libros()

            except mariadb.Error as e:
                QtWidgets.QMessageBox.critical(None, "Error", f"Error al devolver reserva: {e}")

    # Actualizar tablas al cambiar de pestaña
    def tab_changed(self):
        if self.tabWidget.currentIndex() == 2:  
            self.actualizar_mis_libros()
        elif self.tabWidget.currentIndex() == 1:
            self.actualizar_historial()
        elif self.tabWidget.currentIndex() == 3:
            self.actualizar_usuario()

    # Actualizar el crédito del usuario
    def actualizar_usuario(self):
        if self.account_id != 0:
            self.labelCredit.setText(f"Saldo pendiente: ${str(self.credit)}")

    # Método para enviar un correo electrónico al realizar un pedido
    def correo_pedido(self, id_pedido, fecha_prestamo, fecha_devolucion, titulo, autor):
        fecha_prestamo = datetime.strptime(fecha_prestamo, '%Y-%m-%d').strftime('%d / %m / %Y')
        fecha_devolucion = datetime.strptime(fecha_devolucion, '%Y-%m-%d').strftime('%d / %m / %Y')
        subject = f"Pedido realizado | Folio Nro.#{id_pedido}"
        body = f"""Tu pedido con folio #{id_pedido} ha sido realizado con éxito.
{titulo} de {autor}.

Pedido realizado el día: {fecha_prestamo}
Devolver antes del: {fecha_devolucion}

Recuerda que el costo por reserva de cada libro es de $7.00 MXN por día, se te dará un límite de 15 días para retornarlo. Si no se devuelve a tiempo se cobrará una multa de $20 por cáda día que pase.
(Es posible devolver antes el libro, solo se te cobrará lo correspondiente)
Gracias por tu preferencia.
"""
        email_reciver = self.account_email
        if re.match(email_regex, email_reciver):
            em = EmailMessage()
            em["From"] = email_sender
            em["To"] = email_reciver
            em["Subject"] = subject
            em.set_content(body)

            try:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
                    smtp.login(email_sender, password)
                    smtp.sendmail(email_sender, email_reciver, em.as_string())
                print("Correo enviado correctamente.")
            except Exception as e:
                print(f"Error al enviar el correo: {e}")
        else:
            print("Dirección de correo electrónico no válida.")


    def correo_cancelacion(self, id_pedido):
        subject = f"Cancelación de pedido | Folio Nro.{id_pedido}"
        body = f"""Tu pedido con folio #{id_pedido} ha sido cancelado con éxito.

Has cancelado el pedido el mismo día de la reserva por lo que no se te cobrará ningun cargo.

Gracias por tu preferencia.
"""
        email_reciver = self.account_email
        if re.match(email_regex, email_reciver):
            em = EmailMessage()
            em["From"] = email_sender
            em["To"] = email_reciver
            em["Subject"] = subject
            em.set_content(body)

            try:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
                    smtp.login(email_sender, password)
                    smtp.sendmail(email_sender, email_reciver, em.as_string())
                print("Correo enviado correctamente.")
            except Exception as e:
                print(f"Error al enviar el correo: {e}")
        else:
            print("Dirección de correo electrónico no válida.")

    # Método para enviar un correo electrónico al realizar una devolución
    def correo_devolucion(self, id_pedido, fecha_devolucion, costo):
            fecha_hoy = datetime.now().strftime('%d / %m / %Y')
            subject = f"Devolución de pedido | Folio Nro.{id_pedido}"
            body = f"""Tu pedido con folio #{id_pedido} ha sido devuelto con éxito.

Has devuelto el libro el día {fecha_hoy}, la fecha de devolución está marcada para el día {fecha_devolucion.strftime('%d / %m / %Y')}.
Se ha agregado un cargo de ${costo} a tu cuenta, actualmente se debe un total de ${self.credit}.

Gracias por tu preferencia.
    """
            email_reciver = self.account_email
            if re.match(email_regex, email_reciver):
                em = EmailMessage()
                em["From"] = email_sender
                em["To"] = email_reciver
                em["Subject"] = subject
                em.set_content(body)

                try:
                    context = ssl.create_default_context()
                    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
                        smtp.login(email_sender, password)
                        smtp.sendmail(email_sender, email_reciver, em.as_string())
                    print("Correo enviado correctamente.")
                except Exception as e:
                    print(f"Error al enviar el correo: {e}")
            else:
                print("Dirección de correo electrónico no válida.")
    
    # Método para pagar el saldo pendiente
    def pay(self):
        if self.credit == 0:
            QtWidgets.QMessageBox.information(None, "Saldo pendiente", "Actualmente no tienes saldo pendiente por pagar.")
            return
        else:
            ventana_pago = VentanaPago(self.account_id, self.credit, self.account_email)
            ventana_pago.exec_()
    
# Clase principal de la aplicación
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    MainWindow = QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())   