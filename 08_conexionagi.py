import socketserver

# Clase que maneja las conexiones entrantes AGI (Asterisk Gateway Interface)
class FastAGIHandler(socketserver.StreamRequestHandler):
    def handle(self):
        # Leer el entorno AGI enviado por Asterisk al inicio de la conexión
        agi_env = {}
        while True:
            line = self.rfile.readline().decode().strip()
            if line == '':
                break  # Línea vacía indica fin del entorno
            key, value = line.split(':', 1)
            agi_env[key.strip()] = value.strip()

        # Contestar la llamada
        self.send_command("ANSWER")
        print("AGI env:", agi_env)

        # Línea para pruebas (opcional): reproducir audio de prueba y colgar
        # self.send_command('STREAM FILE hello-world ""')
        # self.send_command('HANGUP')

        # Leer variables personalizadas pasadas desde AMI o desde el dialplan
        audio = self.get_variable("AUDIO")
        audio1 = self.get_variable("AUDIO1")
        audio2 = self.get_variable("AUDIO2")
        audio3 = self.get_variable("AUDIO3")
        audio4 = self.get_variable("AUDIO4")
        audio1_1 = self.get_variable("AUDIO1_1")
        audio1_2 = self.get_variable("AUDIO1_2")

        print(f"Audios recibidos: {audio}, {audio1}, {audio2}, etc.")

        # Reproducir el primer audio (menú principal)
        self.send_command(f'STREAM FILE {audio} ""')

        # Esperar un segundo extra tras reproducir el audio
        # para evitar que la llamada se cuelgue demasiado rápido
        self.send_command("WAIT FOR DIGIT 1000")

        # Esperar que el usuario ingrese un dígito (máximo 5 segundos)
        lines = self.send_command("WAIT FOR DIGIT 5000")
        digit_code = self.get_result_value(lines)
        digit = chr(int(digit_code)) if digit_code and digit_code.isdigit() else None

        # Lógica del menú según la tecla presionada
        if digit == "1":
            self.send_command(f'STREAM FILE {audio1} ""')
            # Esperar otro dígito (submenú)
            lines = self.send_command("WAIT FOR DIGIT 5000")
            digit_code = self.get_result_value(lines)
            digit = chr(int(digit_code)) if digit_code and digit_code.isdigit() else None
            if digit == "1":
                self.send_command(f'STREAM FILE {audio1_1} ""')
            elif digit == "2":
                self.send_command(f'STREAM FILE {audio1_2} ""')
            else:
                self.send_command(f'STREAM FILE {audio4} ""')  # Opción inválida
        elif digit == "2":
            self.send_command(f'STREAM FILE {audio2} ""')
        elif digit == "3":
            self.send_command(f'STREAM FILE {audio3} ""')
        else:
            self.send_command(f'STREAM FILE {audio4} ""')  # Opción inválida

        # Colgar la llamada al final
        self.send_command("HANGUP")

    # Función para enviar comandos AGI y leer la respuesta
    def send_command(self, command):
        if not command.endswith('\n'):
            command += '\n'
        self.wfile.write(command.encode())
        self.wfile.flush()

        # Leer respuesta del servidor AGI
        lines = []
        while True:
            line = self.rfile.readline().decode().strip()
            if line == '':
                break
            lines.append(line)
            if line.startswith('200 result='):
                break
        print(f"Respuesta AGI para '{command.strip()}': {lines}")
        return lines

    # Obtener el valor de una variable enviada desde el dialplan o AMI
    def get_variable(self, var_name):
        lines = self.send_command(f'GET VARIABLE {var_name}')
        for line in lines:
            if "result=1" in line:
                value = line.split('(')[-1].rstrip(')')
                return value
        return None

    # Extraer el resultado del dígito presionado a partir de la respuesta AGI
    def get_result_value(self, lines):
        for line in lines:
            if line.startswith("200 result="):
                result = line.split('=')[1].split()[0]
                return result
        return None

# Servidor multicliente basado en hilos para manejar múltiples llamadas a la vez
class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True  # Permite reiniciar sin errores de "puerto en uso"

if __name__ == "__main__":
    # Dirección IP y puerto donde el servidor FastAGI escucha conexiones
    server = ThreadedTCPServer(("192.168.0.144", 4573), FastAGIHandler) 
    print("Servidor FastAGI corriendo en puerto 4573 (multicliente)...")
    server.serve_forever()


