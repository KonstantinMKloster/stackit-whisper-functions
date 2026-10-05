"""ASGI entrypoint for the custom-build (Dockerfile) deployment path.

The buildpack path's generated entrypoint normally wraps handler.py's
Function.start()/stop()/handle() in an ASGI app with lifespan support --
see docs.functions.onstackit.cloud/reference/generated-code.html. Since a
Dockerfile-built image skips that generated entrypoint, this file recreates
the same lifespan wiring so `uvicorn asgi:app` boots and shuts down
correctly (Function.start() loads the Whisper model once per warm
instance; Function.stop() runs on SIGTERM via uvicorn's graceful shutdown).

Used instead of the buildpack build because the project's STACKIT Harbor
registry rejects the zero-byte metadata layer Cloud Native Buildpacks adds
("blob unknown to registry") -- a plain Dockerfile build doesn't produce
that layer.
"""

from handler import new

_fn = new()


async def app(scope, receive, send):
    if scope["type"] == "lifespan":
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                await _fn.start()
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                await _fn.stop()
                await send({"type": "lifespan.shutdown.complete"})
                return
        return

    await _fn.handle(scope, receive, send)
