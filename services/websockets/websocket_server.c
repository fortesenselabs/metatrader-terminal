#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <openssl/sha.h>
#include <stdint.h>
#include <netinet/in.h>
#include <fcntl.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <netinet/tcp.h>
#include <errno.h>

#define PORT 7681
#define BUFFER_SIZE 1024

// WebSocket GUID for handshake
const char *WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11";

void handle_error(const char *message)
{
    perror(message);
    exit(EXIT_FAILURE);
}

void base64_encode(const unsigned char *input, int length, char *output)
{
    const char base64_chars[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    int i = 0, j = 0;
    while (length--)
    {
        output[j++] = base64_chars[(input[i] >> 2) & 0x3F];
        output[j++] = base64_chars[((input[i] & 0x3) << 4) | ((input[i + 1] & 0xF0) >> 4)];
        output[j++] = (length ? base64_chars[((input[i + 1] & 0xF) << 2) | ((input[i + 2] & 0xC0) >> 6)] : '=');
        output[j++] = (length ? base64_chars[input[i + 2] & 0x3F] : '=');
        i += 3;
        length -= 2;
    }
    output[j] = '\0';
}

void compute_accept_key(const char *key, char *accept_key)
{
    char buffer[BUFFER_SIZE];
    unsigned char hash[SHA_DIGEST_LENGTH];

    snprintf(buffer, BUFFER_SIZE, "%s%s", key, WS_GUID);

    SHA1((unsigned char *)buffer, strlen(buffer), hash);

    base64_encode(hash, SHA_DIGEST_LENGTH, accept_key);
}

void send_handshake_response(int client_socket, const char *sec_websocket_key)
{
    char response[BUFFER_SIZE];
    char accept_key[BUFFER_SIZE];

    compute_accept_key(sec_websocket_key, accept_key);

    snprintf(response, BUFFER_SIZE,
             "HTTP/1.1 101 Switching Protocols\r\n"
             "Upgrade: websocket\r\n"
             "Connection: Upgrade\r\n"
             "Sec-WebSocket-Accept: %s\r\n\r\n",
             accept_key);

    send(client_socket, response, strlen(response), 0);
}

void handle_websocket_connection(int client_socket)
{
    char buffer[BUFFER_SIZE];
    int received;

    while ((received = recv(client_socket, buffer, BUFFER_SIZE, 0)) > 0)
    {
        buffer[received] = '\0';
        printf("Received: %s\n", buffer);

        const char *short_message = "Received your message";
        send(client_socket, short_message, strlen(short_message), 0);
    }

    if (received == 0)
    {
        printf("Client disconnected.\n");
    }
    else
    {
        handle_error("recv");
    }

    close(client_socket);
}

void start_server()
{
    int server_socket, client_socket;
    struct sockaddr_in server_addr, client_addr;
    socklen_t client_addr_len = sizeof(client_addr);

    if ((server_socket = socket(AF_INET, SOCK_STREAM, 0)) == -1)
    {
        handle_error("socket");
    }

    int opt = 1;
    if (setsockopt(server_socket, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) == -1)
    {
        handle_error("setsockopt");
    }

    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(PORT);
    server_addr.sin_addr.s_addr = INADDR_ANY;

    if (bind(server_socket, (struct sockaddr *)&server_addr, sizeof(server_addr)) == -1)
    {
        handle_error("bind");
    }

    if (listen(server_socket, 10) == -1)
    {
        handle_error("listen");
    }

    printf("Server listening on port %d\n", PORT);

    while ((client_socket = accept(server_socket, (struct sockaddr *)&client_addr, &client_addr_len)) != -1)
    {
        char buffer[BUFFER_SIZE];
        int received = recv(client_socket, buffer, BUFFER_SIZE, 0);
        buffer[received] = '\0';

        char *key_start = strstr(buffer, "Sec-WebSocket-Key: ");
        if (key_start)
        {
            key_start += strlen("Sec-WebSocket-Key: ");
            char *key_end = strstr(key_start, "\r\n");
            char sec_websocket_key[BUFFER_SIZE];
            strncpy(sec_websocket_key, key_start, key_end - key_start);
            sec_websocket_key[key_end - key_start] = '\0';

            send_handshake_response(client_socket, sec_websocket_key);
            handle_websocket_connection(client_socket);
        }
        else
        {
            close(client_socket);
        }
    }

    if (client_socket == -1)
    {
        handle_error("accept");
    }

    close(server_socket);
}

int main()
{
    start_server();
    return 0;
}

// gcc -o websocket_server websocket_server.c -lssl -lcrypto
// ./websocket_server
