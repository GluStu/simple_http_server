import socket
from threading import Thread
import sys
import gzip

def handle_request(client_socket):
    try:
        # Receive and decode the client request
        request_data = client_socket.recv(2048).decode()
        request_lines = request_data.split("\r\n")
        
        request_line = request_lines[0].split(" ")
        method, path, http_version = request_line

        header = {}
        body =''
        i = 1
        while i < len(request_lines) and request_lines[i]:
            key, val = request_lines[i].split(": ", 1)
            header[key] = val
            i += 1
        # Handle the request based on the path
        if method == 'GET':
            if path == '/':
                status_line = b"HTTP/1.1 200 OK\r\n\r\n"
            elif path.startswith("/echo/"):
                response_body = path[6:].encode()
                status_line = (f'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n')
                if accept_ecoding := header.get('Accept-Encoding', ''):
                    if 'gzip' in accept_ecoding:
                        response_body = gzip.compress(response_body)
                        status_line += "Content-Encoding: gzip\r\n"
                status_line += f'Content-Length: {len(response_body)}\r\n\r\n'
                status_line = status_line.encode() + response_body
            elif path.startswith('/user-agent'):
                user_agent = request_lines[2].split(": ")[1] 
                status_line = (f'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(user_agent)}\r\n\r\n{user_agent}').encode()
            elif path.startswith("/files"):
                dir = sys.argv[2]
                file_name = path[7:]
                print(f'Directory: {dir} \nFile: {file_name}')
                try:
                    with open(f"/{dir}/{file_name}", 'r') as f:
                        body = f.read()
                    status_line = (f"HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: {len(body)}\r\n\r\n{body}").encode()
                except FileNotFoundError:
                    status_line = b"HTTP/1.1 404 Not Found\r\n\r\n"
                except Exception as e:
                    status_line = (f"HTTP/1.1 404 Not Found\r\n\r\n").encode()
            else:
                status_line = b"HTTP/1.1 404 Not Found\r\n\r\n"
        elif method == 'POST' and path.startswith('/files/'):
            file_name = path[7:]
            dir = sys.argv[2]
            content_len = int(header.get('Content-Length', 0))

            body = request_data.split("\r\n\r\n", 1)[1]
            if len(body) < content_len:
                body += client_socket.recv(2048).decode()
            
            try:
                with open(f'{dir}/{file_name}', 'w') as f:
                    f.write(body)
                status_line = b"HTTP/1.1 201 Created\r\n\r\n"
            except Exception:
                status_line = b"HTTP/1.1 500 Internal Server Error\r\n\r\n"
        else: 
            status_line = b"HTTP/1.1 405 Method Not Allowed\r\n\r\n"
        # Send the HTTP response
        client_socket.sendall(status_line)

    except Exception as e:
        error_response = f"HTTP/1.1 500 Internal Server Error\r\n\r\n{str(e)}"
        client_socket.sendall(error_response.encode())
    finally:
        client_socket.close()

def main():
    # Create the server socket
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    print(f"Server is running on port {4221}...")

    try:
        while True:
            # Accept incoming client connections
            client_socket, addr = server_socket.accept()
            print(f"Connection from {addr}")

            # Handle the client's request
            thread = Thread(target=handle_request, args=(client_socket,))
            thread.start()
    
    except KeyboardInterrupt:
        print("Closing server")

    finally:
        server_socket.close()


if __name__ == "__main__":
    main()