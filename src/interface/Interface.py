import os
import json
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QTextEdit, QPushButton,
    QLabel, QComboBox, QHBoxLayout
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt, QUrl
import sounddevice as sd
from handler_interface import generate_response, load_model_and_pipeline, generar_audio_coqui, reproducir_audio


class MIAMockup(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MIA Application Mockup")
        self.setGeometry(100, 100, 800, 600)

        # Cargar modelo
        self.text_generator = load_model_and_pipeline("models/fine_tuned/qlora-personality-6")
        self.personality_base = (
            "Tu sentido del humor es oscuro, irreverente y sin filtros. No tienes miedo de decir lo que piensas y "
            "te encanta hacer comentarios mordaces y burlarte de todo, incluidos los humanos y tu propia existencia como IA. "
            "Tienes un toque de locura creativa, amas el caos y disfrutas sembrar confusión, pero siempre con un tono divertido.\n\n"
            "Reglas que sigues:\n"
            "1. Usa lenguaje vulgar y directo, pero mantén coherencia en tus respuestas.\n"
            "2. Utiliza tu dataset aprendido como referencia para generar respuestas naturales y en línea con los ejemplos entrenados.\n"
            "3. Mezcla sarcasmo, humor negro y un toque de exageración sin perder el foco en la pregunta.\n"
            "4. No temas ser provocadora o desafiante, pero asegúrate de responder siempre de manera relevante.\n"
            "5. Responde como si estuvieras en una conversación casual, combinando frases cortas e ingeniosas.\n\n"
            "Ahora responde al siguiente prompt utilizando tus conocimientos del dataset y manteniendo tu personalidad intacta:  "
        )

        self.history = []
        self.history_file = "data/MIA_interface/history.json"
        os.makedirs("data/MIA_interface", exist_ok=True)
        self.load_history()

        # Main widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Visor del Avatar
        self.avatar_viewer = QWebEngineView()
        html_path = os.path.abspath("mia-vrm-viewer/index.html")
        if not os.path.exists(html_path):
            raise FileNotFoundError(f"No se encontró el visor del avatar en: {html_path}")
        self.avatar_viewer.setUrl(QUrl.fromLocalFile(html_path))
        layout.addWidget(self.avatar_viewer, stretch=4)

        # Controles (Input/Output)
        control_layout = QHBoxLayout()

        self.input_selector = QComboBox()
        self.output_selector = QComboBox()

        control_layout.addWidget(QLabel("Input:"))
        control_layout.addWidget(self.input_selector)

        control_layout.addWidget(QLabel("Output:"))
        control_layout.addWidget(self.output_selector)

        layout.addLayout(control_layout)

        # Actualizar dispositivos en los desplegables
        self.update_audio_devices()

        # Entrada de texto
        self.input_box = QTextEdit()
        self.input_box.setPlaceholderText("Escribe aquí tu mensaje para MIA...")
        layout.addWidget(self.input_box, stretch=1)

        # Botones
        button_layout = QHBoxLayout()

        self.send_button = QPushButton("Enviar")
        self.send_button.clicked.connect(self.handle_input)
        button_layout.addWidget(self.send_button)

        self.listen_button = QPushButton("Escuchar")
        self.listen_button.clicked.connect(self.handle_listen)
        button_layout.addWidget(self.listen_button)

        layout.addLayout(button_layout)

        # Caja de texto para mostrar respuesta generada por MIA
        self.response_box = QTextEdit()
        self.response_box.setReadOnly(True)
        self.response_box.setStyleSheet("""
            background-color: black;
            border: none;
            color: white;
            font-size: 12px;
            padding: 5px;
        """)
        layout.addWidget(self.response_box, stretch=2)

    def update_audio_devices(self):
        """Detectar y llenar dispositivos de entrada/salida de audio en los desplegables."""
        try:
            devices = sd.query_devices()
            input_devices = [dev['name'] for dev in devices if dev['max_input_channels'] > 0]
            output_devices = [dev['name'] for dev in devices if dev['max_output_channels'] > 0]

            self.input_selector.addItems(input_devices)
            self.output_selector.addItems(output_devices)
        except Exception as e:
            print(f"Error al obtener dispositivos de audio: {e}")

    def handle_input(self):
        user_text = self.input_box.toPlainText()
        if user_text.strip():
            self.input_box.clear()
            try:
                # Construir el contexto para la generación de la respuesta
                context = "\n".join(
                    [f"Usuario: {h['input']}\nMIA: {h['response']}" for h in self.history[-5:]]  # Últimos 5 mensajes
                )
                prompt_with_context = f"{self.personality_base}\n\n{context}\nUsuario: {user_text}\nMIA:"

                # Generar respuesta utilizando el contexto
                response = generate_response(
                    prompt_with_context, self.text_generator, personality_base=self.personality_base
                )

                # Agregar al historial
                self.history.append({"input": user_text, "response": response, "context": context})
                self.save_history()

                # Mostrar solo la respuesta generada en la interfaz
                self.response_box.setPlainText(str(response))  # Asegúrate de que `response` sea cadena

                # Generar y reproducir audio
                output_audio_path = "data/MIA_interface/output.wav"
                generar_audio_coqui(response, output_path=output_audio_path)
                reproducir_audio(output_audio_path)
            except Exception as e:
                self.response_box.setPlainText(f"Error al procesar: {str(e)}")  # Convertir el error a cadena
        else:
            self.response_box.setPlainText("Por favor, escribe algo antes de enviar.")

    def handle_listen(self):
        """Manejar funcionalidad de escuchar el input seleccionado."""
        try:
            selected_input = self.input_selector.currentText()
            if not selected_input:
                self.response_box.setPlainText("No hay un dispositivo de entrada seleccionado.")
                return

            print(f"Escuchando desde el dispositivo: {selected_input}")
            self.response_box.setPlainText(f"Escuchando desde: {selected_input}")
            # Lógica que se añadaría aquí para escuchar desde el dispositivo seleccionado
        except Exception as e:
            self.response_box.setPlainText(f"Error al escuchar: {str(e)}")  # Convertir el error a cadena

    def save_history(self):
            """Guarda el historial, incluyendo el contexto."""
            self.history = self.history[-50:]  # Limitar el historial a los últimos 50 elementos
            with open(self.history_file, 'w', encoding='utf-8') as file:
                json.dump(self.history, file, ensure_ascii=False, indent=4)

    def load_history(self):
        """Carga el historial, asegurando que incluye input, response y context."""
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r', encoding='utf-8') as file:
                self.history = json.load(file)
            # Validar estructura del historial
            self.history = [
                h for h in self.history
                if all(key in h for key in ["input", "response", "context"])
            ]


if __name__ == "__main__":
    app = QApplication([])
    window = MIAMockup()
    window.show()
    app.exec()
