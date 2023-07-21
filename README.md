# <img valign="middle" src="https://www.vicchi.org/assets/images/avatar.jpeg" height="64" alt="Gary Gale">&nbsp;indieauthify

A work-in-progress [IndieAuth](https://indieauth.com/) server implementation, in Python, using [FastAPI](https://fastapi.tiangolo.com/), [Starlette](https://www.starlette.io/) and [indieweb-utils](https://github.com/capjamesg/indieweb-utils).

There are sharp edges here and it's not even remotely deployable yet.

Note that the Docker container (currently) supports `linux/amd64` and `linux/arm64` but *not* `linux/arm/v7` due to `pyca/cryptography` [effectively not supporting ARM32 wheels](https://github.com/pyca/cryptography/issues/6286#issuecomment-922563400).

# Running with Docker

```
docker run --rm \
    --env-file=.env \
    -p 8000:80 \
    -v $(pwd)/data-stores:/service/data-stores \
    -v $(pwd)/gunicorn.conf.py:/service/gunicorn.conf.py \
    --name indieauthify \
    ghcr.io/vicchi/indieauthify:latest
```
