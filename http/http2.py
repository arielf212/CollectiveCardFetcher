# HTTP Server Shell
# Author: Barak Gonen
# Purpose: Provide a basis for Ex. 4.4
# Note: The code is written in a simple way, without classes, log files or other utilities, for educational purpose
# Usage: Fill the missing functions and constants

# TO DO: import modules
import socket, os

# TO DO: set constants
SOCKET_TIMEOUT = 10
PORT = 8000
IP = '127.0.0.1'
DEFAULT_URL = r'D:\programming\python_projects\ccf_rewrite\a.txt'
REDIRECTION_DICTIONARY = {}


def get_file_data(filename):
    """ Get data from file """
    my_file = open(filename)
    file_read = my_file.read()
    my_file.close()
    return file_read



def handle_client_request(resource, client_socket):
    """ Check the required resource, generate proper HTTP response and send to client"""
    # TO DO : add code that given a resource (URL and parameters) generates the proper response
    if resource == '':
        url = DEFAULT_URL
    else:
        url = resource

    # TO DO: check if URL had been redirected, not available or other error code. For example:

    http_header = 'HTTP/1.1 200 OK\r\n'
    if not os.path.isfile(url):
        http_header = "HTTP/1.1 404 Not Found\r\n"
        url = "b.txt"
    filetype = url.split('.')[1]
    if url in REDIRECTION_DICTIONARY:
        pass
        # TO DO: extract requested file tupe from URL (html, jpg etc)
    if filetype == 'html':
        http_header += 'Content-Type: text/html; charset=utf-8' + '\r\n'  # TO DO: generate proper HTTP header
    elif filetype == 'jpg':
        http_header += 'Content-Type: image/jpeg' + '\r\n'  # TO DO: generate proper jpg header
    # TO DO: handle all other headers

    # TO DO: read the data from the file

    data = get_file_data(url)
    http_header += "Content-Length: " + str(len(data)) + "\r\n"
    http_response = http_header + "\r\n" + data
    client_socket.send(http_response)
                            
def validate_http_request(request):
    """ Check if request is a valid HTTP request and returns TRUE / FALSE and the requested URL """
    # TO DO: write function
    print request
    holder = request.split("\r\n")[0].split(" ")
    if holder[0] != 'GET' or holder[2] != 'HTTP/1.1':
        return False, ""
    return True, holder[1][1:]


def handle_client(client_socket):
    """ Handles client requests: verifies client's requests are legal HTTP, calls function to handle the requests """
    print 'Client connected'
    while True:
        # TO DO: insert code that receives client request
        client_request = client_socket.recv(1024)
        valid_http, resource = validate_http_request(client_request)
        print 'the resource: ' + resource
        if valid_http:
            print 'Got a valid HTTP request'
            handle_client_request(resource, client_socket)
        else:
            print 'Error: Not a valid HTTP request'
            break
    print 'Closing connection'
    client_socket.close()


def main():
    # Open a socket and loop forever while waiting for clients
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((IP, PORT))
    server_socket.listen(10)
    print "Listening for connections on port %d" % PORT

    while True:
        client_socket, client_address = server_socket.accept()
        print 'New connection received'
        client_socket.settimeout(SOCKET_TIMEOUT)
        handle_client(client_socket)


if __name__ == "__main__":
    # Call the main handler function
    main()
