# Auth

Authentication process for metatrader web interface

## Get All Supported Servers

**MT5:**

```bash
    curl 'https://metatraderweb.app/trade/servers?version=5&all=1'
```

**MT4:**

```bash
    curl 'https://metatraderweb.app/trade/servers?version=4&all=1'
```

uses query params
Request:

- version: int (4 or 5)
- all: bool (1 or 0) -> not sure

Response:
**MT5:**

```json
{
    mt5: [...]
}
```

**MT4:**

```json
{
    mt4: [...]
}
```

List of all servers supported by Metatrader

##

```bash
curl 'https://metatraderweb.app/trade/json' \
  --data-raw 'login=30565290&trade_server=Deriv-Demo&version=5'
```

Response:

```json
{
  "signal_server": "gwt4.mql5.com:443",
  "trade_server": "Deriv-Demo",
  "login": "30565290",
  "company": "Deriv.com Limited",
  "ping": 1,
  "key": "fa7e7e34da42ad9748bd9ac290e51c44d78358834f62c831d1abace5275cf599",
  "token": "NkyHkwp2YZcJg7kfNMAVKkzbQLDxvk7AphN8MJrPPSD4DjvWDPAhCtaBDgZJ2YDx",
  "version": 5,
  "enabled": true,
  "gwt_servers": [4, 2, 6, 12, 1, 7, 8, 11, 13, 9, 10, 5, 3]
}
```

Use your password to decrypt the key (Hash type: SHA2-256)
key:
Hash type: SHA2-256 or AES-CBC
Bit length: 256
Character length: 64
Character type: hexidecimal

The key and token are both dynamic

fa7e7e34da42ad9748bd9ac290e51c44d78358834f62c831d1abace5275cf599
52d71cf9dcf1dbbcaa0df6cf282614e09bd4bbbc31444a6bc0ba3f0e2116436b
db7debae6aa579fc7eba402498e2f5fc9e7a798233460ad37f672e4310cc55b3

Statistics for one of the keys:
Zeroes: 49.22 %
Ones: 50.78 %
Entropy: 4.87
Byte length: 32
If both zeroes and ones are close to 50%, this is probably encrypted using a modern cipher.

{"signal_server":"gwt4.mql5.com:443","trade_server":"Deriv-Demo","login":"30565290","company":"Deriv.com Limited","ping":1,"key":"f9814f7422b1d43e10509e254cf925beeebf16de764a4ac3fbb0afecdd06843f","token":"9JFYcj7FjztWtygsVxwvkBqYKXS8WXF5u3VHfLf3iCcwiWh5HyvjrA9pdAp8k8Tv","version":5,"enabled":true,"gwt_servers":[4,2,6,12,1,7,8,11,13,9,10,5,3]}

{"signal_server":"gwt4.mql5.com:443","trade_server":"Deriv-Demo","login":"30565290","company":"Deriv.com Limited","ping":1,"key":"14928b719261e69d04863656168417352529815a7a63b40a51dc0c2f908c8400","token":"s9sCCqhFBbksbuvdN2WiwaPMyFNa2MxnS4MrFCWt2VKmkzZMKkfFLEyrcPX5KZyX","version":5,"enabled":true,"gwt_servers":[4,2,6,12,1,7,8,11,13,9,10,5,3]}

the token is probably encoded

initiate a websocket connection with the signal_server(in this case gwt4.mql5.com)
and send the details using binary

Sent:
00000000: 5000 0000 0100 0000 0d63 b454 5d2c ee94 P........c.T],..
00000001: 2f0b ba73 7e7a d455 ee5c ccb4 beb9 3ca6 /..s~z.U.\....<.
00000002: 1d7d ad5b 27a0 7e51 a360 0018 9960 e049 .}.['.~Q.`...`.I
00000003: 3ccf f69f 0917 0faf 0397 ef18 23e4 06dd <...........#...
00000004: 935d f047 cdfd 797a 26c0 49d8 3374 fa95 .].G..yz&.I.3t..
00000005: 6b7e 557a 85d7 3ecd k~Uz..>.

Sent:
00000000: f002 0000 0100 0000 7304 c4ad b5d0 984e ........s......N
00000001: e9fc 9a84 92c1 1796 a390 2bf7 d163 2f0d ..........+..c/.
00000002: de08 53a2 54fa f60d 8c98 3eb2 d05d bb9c ..S.T.....>..]..
00000003: f73b 1495 d26f d1ee c932 ca17 f9fe e491 .;...o...2......
00000004: 0c64 a545 32bc aa5f 2d0f fb76 ced2 9088 .d.E2.._-..v....
00000005: 3613 148e 45cd 1a0f f739 037b 6ef5 0af0 6...E....9.{n...
00000006: 8de2 61b7 3dab 2a7e 33fb 8fe0 7b32 d510 ..a.=.\*~3...{2..
00000007: b989 1f58 5f12 36af e783 3916 7fe3 9d5e ...X_.6...9....^
00000008: 191d 7ef3 1fd9 42aa 40a9 fe5d 394a e886 ..~...B.@..]9J..
00000009: cc88 bf7a d75c 80d4 af8f ea08 6ef5 c252 ...z.\......n..R
0000000a: 0985 51d8 511c 91a1 bb50 c337 a20e 4a6c ..Q.Q....P.7..Jl
0000000b: 15c2 ab14 df45 c341 0269 eda6 a299 0e4d .....E.A.i.....M
0000000c: d437 8fd5 2cc1 f14a 7227 3bc8 44b5 b060 .7..,..Jr';.D..`
0000000d: 5411 679e 3e31 6326 16d9 6b95 1979 1120  T.g.>1c&..k..y. 
0000000e: 22e4 2753 1fbc b544 fdcd 011d 2b4d 4a69  ".'S...D....+MJi
0000000f: 5140 9b94 82ee b1da cfba 0b75 b8c5 74fa  Q@.........u..t.
00000010: c2ad 59de ce0a c0a0 9770 0728 1c7b ecb1  ..Y......p.(.{..
00000011: ad9f 5b18 7142 6672 930a 7243 a567 f591  ..[.qBfr..rC.g..
00000012: a8d5 c2b3 fd85 73a6 61f7 ed0c 49df b170  ......s.a...I..p
00000013: e0a4 c2bb 9732 d114 f4c1 8c68 22a5 8f96  .....2.....h"...
00000014: 86f9 d57f 676e 1102 f9bc 7ef5 4e24 159a  ....gn....~.N$..
00000015: 0e03 0933 9812 5c38 9ef9 8ef1 bc7f be54  ...3..\8.......T
00000016: 4e72 b225 5916 e8c9 0323 6cb7 b0b2 6675  Nr.%Y....#l...fu
00000017: e93d 918d adc4 f6d8 7f32 5dae 1248 83b7  .=.......2]..H..
00000018: 0ef7 2da4 ec18 d69b 0856 50cc 7746 fa60  ..-......VP.wF.`
00000019: 04f2 c0e1 d0cc 0b85 0597 f128 21e7 6c76 ...........(!.lv
0000001a: 558f 85b1 c603 7541 36c5 511b f284 70c0 U.....uA6.Q...p.
0000001b: d657 43eb 6cee 7097 5904 19a1 4759 f2c2 .WC.l.p.Y...GY..
0000001c: 6fd0 edd3 d326 98bb 49c7 d2d1 9d48 2096 o....&..I....H .
0000001d: 83f6 3aa0 2290 767c 1c7d ae22 d291 9195 ..:.".v|.}."....
0000001e: 2b3e 5b74 0cdc dab1 d8b5 3e37 ff98 9bd0 +>[t......>7....
0000001f: e9c5 1a4f f7cf d05e a9f1 6f7b d122 1c87 ...O...^..o{."..
00000020: 81c4 76e2 53c1 77d3 ef06 25f1 01cf 3970 ..v.S.w...%...9p
00000021: 90f6 b33b a0ed 7929 3227 6510 7524 3ac5 ...;..y)2'e.u$:.
00000022: b9bc b319 984e 945c 79cf a42d d929 2a3f .....N.\y..-.)\*?
00000023: 18ff 7690 d39a f4a3 39ae b2b0 c417 b56d ..v.....9......m
00000024: 42db c054 56d7 3e49 3c91 0051 099e ae33 B..TV.>I<..Q...3
00000025: 1c72 fc4b 0d0d d84a cb14 9642 bacc 5820 .r.K...J...B..X
00000026: efa9 a1a5 0c77 13f5 bb8a fe15 1151 ad08 .....w.......Q..
00000027: cfef fb06 da72 dff4 b040 8659 0e53 c65c .....r...@.Y.S.\
00000028: aaab 9f86 d374 467e dd4d b13b be4a 7fdd .....tF~.M.;.J..
00000029: 5762 0419 e326 35c9 abdb 2e8e 3bd8 a225 Wb...&5.....;..%
0000002a: 3ebe 597f 1e42 c919 2fc8 7022 ae82 9fac >.Y..B../.p"....
0000002b: 26b1 b47b 9c69 1a75 a075 e192 1045 3c7b &..{.i.u.u...E<{
0000002c: 1fae 8c7e c172 ae3c abce aeda d817 05dd ...~.r.<........
0000002d: 017f 9467 a8c3 f8fa 2e7b fa2d 6bf2 7df3 ...g.....{.-k.}.
0000002e: 3b83 c7fe 7841 4a64 db79 0f2c 3829 2b9d ;...xAJd.y.,8)+.
0000002f: abce 5670 d2fc 1fc8 ..Vp....

Received:
00000000: 1000 0000 0000 0000 640b b1c2 c1b3 bbce ........d.......
00000001: 684b 84ff 5af5 245f hK..Z.$\_

## Micell.

```
HTTP/2.0 200
content-type: application/json
date: Wed, 07 Feb 2024 08:44:47 GMT
accept-ranges: none
access-control-allow-origin: *
cache-control: no-cache
content-length: 343
x-service: MQL5 API
strict-transport-security: max-age=31536000
generate-time: 101676

{"signal_server":"gwt13.mql5.com:443","trade_server":"Deriv-Demo","login":"30565290","company":"Deriv.com Limited","ping":1,"key":"db7debae6aa579fc7eba402498e2f5fc9e7a798233460ad37f672e4310cc55b3","token":"AxFuzhgnWCgkJsZaQfqsTbAsMRjuDPyFHeuVCTDFfdmaCREMfeSYuxByPpAR7ERZ","version":5,"enabled":true,"gwt_servers":[4,6,12,1,7,8,11,13,9,10,5,3]}
```

```
curl 'https://metatraderweb.app/trade?version=5&referrer=metatraderweb.app&ref=294ac365b6a2b205e273c7ae9d5649a5a580dbb4a15bfaab95b7f67a63223192087b04e741468103604b0b546a7e41be' \
  -H 'authority: metatraderweb.app' \
  -H 'accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7' \
  -H 'accept-language: en-GB,en-US;q=0.9,en;q=0.8' \
  -H 'cookie: _fz_uniq=5190860881111465187; _fz_fvdt=1707297510; _fz_ssn=1707297510178023646' \
  -H 'referer: https://metatraderweb.app/trade?version=4&referrer=metatraderweb.app&ref=294ac365b6a2b205e273c7ae9d5649a54fe14f3b59ed923827d6f61fc96bf909dedf708d09a68e3ec94526f628a47e57' \
  -H 'sec-ch-ua: "Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "Linux"' \
  -H 'sec-fetch-dest: document' \
  -H 'sec-fetch-mode: navigate' \
  -H 'sec-fetch-site: same-origin' \
  -H 'sec-fetch-user: ?1' \
  -H 'upgrade-insecure-requests: 1' \
  -H 'user-agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36' \
  --compressed
```

```bash
curl 'https://metatraderweb.app/trade/json' \
  -H 'authority: metatraderweb.app' \
  -H 'accept: */*' \
  -H 'accept-language: en-GB,en-US;q=0.9,en;q=0.8' \
  -H 'content-type: application/x-www-form-urlencoded' \
  -H 'cookie: _fz_uniq=5190860881111465187; _fz_fvdt=1707297510; _fz_ssn=1707297510178023646' \
  -H 'origin: https://metatraderweb.app' \
  -H 'referer: https://metatraderweb.app/trade?version=5&referrer=metatraderweb.app&ref=294ac365b6a2b205e273c7ae9d5649a5a580dbb4a15bfaab95b7f67a63223192087b04e741468103604b0b546a7e41be' \
  -H 'sec-ch-ua: "Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "Linux"' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: same-origin' \
  -H 'user-agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36' \
  --data-raw 'login=30565290&trade_server=Deriv-Demo&version=5' \
  --compressed
```
