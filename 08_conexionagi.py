import socketserver
#
class FastAGIHandler(socketserver.StreamRequestHandler):
    def handle(self):
        # Leer entorno AGI
        agi_env = {}
        while True:
            line = self.rfile.readline().decode().strip()
            if line == '':
                break
            key, value = line.split(':', 1)
            agi_env[key.strip()] = value.strip()

        self.send_command("ANSWER")
        print("AGI env:", agi_env)
        # el hello-world se lo utilizo para realziar pruebas de funcionalidad con audios
        #self.send_command('STREAM FILE hello-world ""')
        
        #el colgar de aqui es para poder probarle que luego del hello worl se cirre la llamada
        #self.send_command('HANGUP')
        # Leer variables de canal (pasadas desde AMI)
        audio = self.get_variable("AUDIO")
        audio1 = self.get_variable("AUDIO1")
        audio2 = self.get_variable("AUDIO2")
        audio3 = self.get_variable("AUDIO3")
        audio4 = self.get_variable("AUDIO4")
        audio1_1 = self.get_variable("AUDIO1_1")
        audio1_2 = self.get_variable("AUDIO1_2")

        print(f"Audios recibidos: {audio}, {audio1}, {audio2}, etc.")

        # Reproducir el primer menú
        self.send_command(f'STREAM FILE {audio} ""')

        # Esperar tecla
        #este control de espera es para que luego de reproducir el audio, este espera un segundo mas,
        #debido a que se esta colgando muy rapido la llamada luego de terminar la reproduccion de audio primario
        self.send_command("WAIT FOR DIGIT 1000")
        lines = self.send_command("WAIT FOR DIGIT 5000")
        digit_code = self.get_result_value(lines)
        digit = chr(int(digit_code)) if digit_code and digit_code.isdigit() else None

        if digit == "1":
            self.send_command(f'STREAM FILE {audio1} ""')
            '''digit_code = self.send_command("WAIT FOR DIGIT 5000")
            digit = chr(int(digit_code)) if digit_code and digit_code.isdigit() else None'''
            lines = self.send_command("WAIT FOR DIGIT 5000")
            digit_code = self.get_result_value(lines)
            digit = chr(int(digit_code)) if digit_code and digit_code.isdigit() else None
            if digit == "1":
                self.send_command(f'STREAM FILE {audio1_1} ""')
            elif digit == "2":
                self.send_command(f'STREAM FILE {audio1_2} ""')
            else:
                self.send_command(f'STREAM FILE {audio4} ""')  # inválida
        elif digit == "2":
            self.send_command(f'STREAM FILE {audio2} ""')
        elif digit == "3":
            self.send_command(f'STREAM FILE {audio3} ""')
        else:
            self.send_command(f'STREAM FILE {audio4} ""')

        self.send_command("HANGUP")

    def send_command(self, command):
        if not command.endswith('\n'):
            command += '\n'
        self.wfile.write(command.encode())
        self.wfile.flush()

        # Leer respuesta completa
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



    def get_variable(self, var_name):
        lines = self.send_command(f'GET VARIABLE {var_name}')
        for line in lines:
            if "result=1" in line:
                value = line.split('(')[-1].rstrip(')')
                return value
        return None

    def get_result_value(self, lines):
        for line in lines:
            if line.startswith("200 result="):
                result = line.split('=')[1].split()[0]
                return result
        return None



class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True  # permite reiniciar sin problemas de "puerto en uso"

if __name__ == "__main__":
    server = ThreadedTCPServer(("192.168.2.10", 4573), FastAGIHandler) 
    print("Servidor FastAGI corriendo en puerto 4573 (multicliente)...")
    server.serve_forever()

