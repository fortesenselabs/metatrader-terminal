# Docs

Exposed Ports:

- 5900 8000 4222 8080

**NATs Image:**

```bash
docker pull nats:2.8.4-alpine3.15
```

For APP_SECRETS:

```bash
base64 infrastructure/k8s/env.yaml > encoded_file.txt
```

copy the contents of encoded_file.txt. To see the contents of encoded_file.txt

```bash
base64 --decode encoded_file.txt > decoded_file.txt
```

GHCR_TOKEN:

- https://gist.github.com/yokawasa/841b6db379aa68b2859846da84a9643c

## Resources

https://github.com/karanpratapsingh/HyperTrade

https://medium.com/@deepak1812002/get-started-with-github-ghcr-an-alternative-of-dockerhub-f7d5b2198b9a
