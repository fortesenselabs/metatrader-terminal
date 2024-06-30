# Docs - MT5 Reverse Engineering

Authentication functions seems to be stored at: 04a8e93f.js, a1151122.js, 00a24b22.js
Also check out the login function at async login(e), it seems some kind of dependency injection is been used

the websockets onMessage(e) function at 00a24b22.js seem to be
decrypting the message -> decoding the message -> parsing the message

connectApi(e) method inside the Z1 class in 00a24b22.js file seems to be the entry point to the application

this.api seems to be used alot

this.apiKey == key in Response
this.server == signal_server in Response

Response(gotten from making a GET request to https://mt5-demo-web.deriv.com/terminal/json):

```json
{
  "signal_server": "mt5-demo-web.deriv.com/terminal",
  "trade_server": "",
  "login": "0",
  "company": "Deriv.com Limited",
  "ping": 1,
  "key": "79611d75c9c9735f9acd14ae9014273f2126634225c21855b02da00d313154ed",
  "token": "bbb099c8ac62aec36a01e37b94940078ada674ec706ec7355cae6894ed23878b",
  "version": 5,
  "enabled": true
}
```

connectToServer()

What is this -> 13ef13b2b76dd8:5795gdcfb2fdc1ge85bf768f54773d22fff996e3ge75g5:75 ? as it seems to have something to do with the private key generation

ImportKey(ConvertKeyToBuffer(ParseString(string)))

the REST request function: async function tn(e, t, o) in 00a24b22.js file

This class is for Error mapping especially API errors:

```typescript
class sc extends Error {
  constructor(e) {
    super(e.message ?? ""),
      (this.command = e.command),
      (this.code = e.code),
      (this.count = e.count);
  }
}
```

class a extends n in file 04a8e93f.js contains the usage of the function, where the function is now called o in the file. Then function on(e, t) in 00a24b22.js in called r in the same file

the string that leads to the private key generation seems to be static:
const o = co(ro(so("13ef13b2b76dd8:5795gdcfb2fdc1ge85bf768f54773d22fff996e3ge75g5:75")));

A way to get this string would be to use a web-scraper.

https://github.com/padolsey/findAndReplaceDOMText

## Auth Flow

1. Send a GET Request to /terminal/json to get key, token, signal_server, and other relevant info
2. Use the Info from step one to create a websocket client that will connect to the server
3.

### connectToServer websocket function:

1. Fetch public and private keys asynchronously
   ```typescript
   await Promise.all([
     co(ro(this.apiKey)).then((publicKey) => {
       this.keyPublic = publicKey;
     }),
     co(
       ro(
         so("13ef13b2b76dd8:5795gdcfb2fdc1ge85bf768f54773d22fff996e3ge75g5:75")
       )
     ).then((privateKey) => {
       this.keyPrivate = privateKey;
     }),
   ]);
   ```
2. Establish WebSocket connection

   ```typescript
   await new Promise<void>((resolve, reject) => {
     this.reject = reject;
     this.resolve = resolve;

     this.webSocket = new WebSocket(`wss://${this.server}`);
     this.webSocket.binaryType = "arraybuffer";
     this.webSocket.removeEventListener("message", this.onMessage);
     this.webSocket.addEventListener("message", this.onMessage);
     this.webSocket.addEventListener("close", this.onClose, { once: true });
     this.webSocket.addEventListener("error", this.onError, { once: true });
     this.webSocket.addEventListener("open", this.onOpen, { once: true });
   });
   ```

3. Send initial command to the server and handle response
   ```typescript
   const response = await this.sendCommand(0, this.token);
   this.signalServerVersion = new Uint16Array(response.resBody)[0];
   ```

### sendCommand in the connectToServer function

Let's break down what the `sendCommand` function does:

1. **Input Validation**:

   - It first checks if the provided command (`e`) is valid by calling the `Xo` function.
   - If the command is not valid, it throws a custom error (`SC`) indicating the invalid command with the appropriate error code.

2. **Selecting Key**:

   - Based on the command (`e`), it selects either the private key (`this.keyPrivate`) or the public key (`this.keyPublic`) for encryption.
   - If the command is `0`, it uses the private key for encryption, otherwise, it uses the public key.

3. **Constructing Message**:

   - It constructs the message to be sent to the server by encoding the command and payload (`t`) into a binary format.
   - The message starts with two random bytes, followed by the command encoded as a 16-bit integer (little-endian), and then the payload.

4. **Encrypting Message**:

   - It encrypts the constructed message using the selected key (either private or public) and the `uo` function, which likely encrypts the message using AES encryption.

5. **Sending Message**:

   - It sends the encrypted message to the server using the `send` method, along with options (`o` and `n`) for handling the message.
   - The `send` method returns a promise that resolves with the server's response.

6. **Handling Response**:

   - It awaits the response from the server and checks if the response code (`resCode`) is not equal to `0`.
   - If the response code is not `0`, it throws a custom error (`SC`) with the command, response code, and count.

7. **Error Handling**:
   - It catches any errors that occur during the process, extracts the command and code from the error, and throws a custom error (`SC`) with the extracted command, code, and count.

In summary, the `sendCommand` function handles the encryption of commands and payloads, sends them to the server, receives and validates the server's response, and handles errors that occur during the process.

## Websocket Client Class

Dc class in 00a24b22.js file

1. **Property Initialization**:

   - `this.isReady`, `this.requests`, `this.listeners`, `this.queues`, and `this.systemListeners` are initialized with default values (`false` for `isReady` and new `Map()` instances for the rest).

2. **Count Assignment**:

   - `this.count` is set to `0` initially and then reassigned to the value of `t` provided as an argument.

3. **Server Information**:

   - `this.server` is assigned the value of `e.signal_server`.

4. **Token Handling**:

   - If `e.token` is a string, it's converted into a 64-byte ArrayBuffer using a function (`Oc.setCharString`) and assigned to `this.token`.
   - If `e.token` is already an ArrayBuffer, it's directly assigned to `this.token`.

5. **API Key Assignment**:

   - `this.apiKey` is assigned the value of `e.apiKey`.

6. **Initialization Reset**:

   - `this.reset()` is called, presumably to reset any internal state or configurations.

7. **Binding Event Handlers**:
   - Event handler methods (`onMessage`, `onParse`, `onClose`, `onTimeout`, `onError`, `onOpen`) are bound to the current instance of the class (`this`) using `bind(this)`.

## Resources

https://gemini.google.com/app/31f70b074e739377
https://chatgpt.com/c/0ab74452-c99a-4b29-9b3c-d2562377ad7c
https://www.meta.ai/c/7cb57ebc-7988-4bf1-a002-df0979273712
https://github.com/Legrandin/pycryptodome/
https://chatgpt.com/c/8b98f95f-93de-479e-94ae-3aab70fa435d
